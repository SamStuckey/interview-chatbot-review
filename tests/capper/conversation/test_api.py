"""Conversation HTTP behavior: authentication, history, sends, stops, feedback, and replay."""

import asyncio
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite
from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart
from pydantic_ai.models.function import AgentInfo

from capper.container import Services
from capper.conversation.service import StartedTurn, request_hash
from tests.support import (
    ESTABLISHED_USER,
    PARALLEL_USER,
    Keys,
    ScriptedModel,
    Step,
    events_of,
    running_app,
    streamed_text,
)


async def query(db_path: Path, sql: str, *args: Any) -> list[tuple[Any, ...]]:
    async with aiosqlite.connect(db_path) as db:
        return [tuple(row) for row in await (await db.execute(sql, args)).fetchall()]


async def test_greeting_and_no_turn_in_progress(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        body = (await h.client.get("/v1/conversation", headers=h.auth(ESTABLISHED_USER))).json()
    assert body["greeting"][0].startswith("Hi! I'm Capper")
    assert body == {**body, "turn_in_progress": False, "active_turn_id": None}


async def test_a_turn_streams_and_is_saved_with_provenance(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel([Step("Hello there.")])) as h:
        status, events = await h.send(ESTABLISHED_USER, "Hi")
        history = (
            await h.client.get("/v1/conversation/messages", headers=h.auth(ESTABLISHED_USER))
        ).json()
    assert status == 200
    assert events[0]["type"] == "turn.start"
    assert events[-1] == {**events[-1], "type": "turn.end", "status": "complete"}
    assert streamed_text(events).strip() == "Hello there."
    assistant, user = history["messages"]  # newest first
    assert assistant["id"] == events[-1]["assistant_message_id"]
    assert user["id"] == events[0]["user_message_id"]
    assert assistant["parts"] == [{"type": "text", "text": "Hello there. "}]
    turn = await query(db_path, "SELECT status, model, content_version, app_version FROM turns")
    assert turn[0][0] == "complete" and all(turn[0])


async def test_history_pages_newest_first(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel()) as h:
        for i in range(3):
            await h.send(ESTABLISHED_USER, f"Message {i}")
        page = (
            await h.client.get(
                "/v1/conversation/messages?limit=4", headers=h.auth(ESTABLISHED_USER)
            )
        ).json()
        rest = (
            await h.client.get(
                f"/v1/conversation/messages?limit=4&before={page['next_cursor']}",
                headers=h.auth(ESTABLISHED_USER),
            )
        ).json()
    assert len(page["messages"]) == 4 and page["next_cursor"]
    assert len(rest["messages"]) == 2 and rest["next_cursor"] is None
    times = [m["created_at"] for m in page["messages"] + rest["messages"]]
    assert times == sorted(times, reverse=True)


async def test_message_validation_happens_before_streaming(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel(), max_message_chars=10) as h:
        empty = await h.send(ESTABLISHED_USER, "   ")
        long = await h.send(ESTABLISHED_USER, "x" * 11)
        no_key = await h.client.post(
            "/v1/conversation/messages", json={"text": "hi"}, headers=h.auth(ESTABLISHED_USER)
        )
    assert empty[0] == 422 and empty[1][0]["error"]["code"] == "invalid_request"
    assert long[0] == 422
    assert no_key.status_code == 422
    assert await query(db_path, "SELECT id FROM turns") == []


async def test_duplicate_sends_follow_the_outcome_rules(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel([Step("Once.")])) as h:
        _, first = await h.send(ESTABLISHED_USER, "Hello", key="key-1")
        status, replay = await h.send(ESTABLISHED_USER, "Hello", key="key-1")
        reused = await h.send(ESTABLISHED_USER, "Different", key="key-1")
    assert status == 200
    assert replay[0] == first[0]
    assert streamed_text(replay) == streamed_text(first)
    assert replay[-1] == first[-1]
    assert len(await query(db_path, "SELECT id FROM turns")) == 1  # no second model call
    assert reused[0] == 422 and reused[1][0]["error"]["code"] == "idempotency_key_reused"


async def test_one_active_turn_and_a_running_duplicate_are_409(db_path: Path, keys: Keys) -> None:
    release = asyncio.Event()

    async def slow(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        await release.wait()
        return Step("Finally.")

    async with running_app(db_path, keys, ScriptedModel([slow])) as h:
        first = asyncio.create_task(h.send(ESTABLISHED_USER, "Slow one", key="slow"))
        await asyncio.sleep(0.2)
        other = await h.send(ESTABLISHED_USER, "Another", key="other")
        duplicate = await h.send(ESTABLISHED_USER, "Slow one", key="slow")
        state = (await h.client.get("/v1/conversation", headers=h.auth(ESTABLISHED_USER))).json()
        # The user message and prompt are committed before generation.
        committed = await query(db_path, "SELECT role FROM messages")
        prompts = await query(db_path, "SELECT payload FROM model_messages")
        release.set()
        status, events = await first
    assert other[0] == 409 and other[1][0]["error"]["code"] == "turn_in_progress"
    assert other[1][0]["error"]["turn_id"] == events[0]["turn_id"]
    assert duplicate[0] == 409
    assert state["turn_in_progress"] is True and state["active_turn_id"] == events[0]["turn_id"]
    assert committed == [("user",)]
    assert len(prompts) == 1 and "Slow one" in prompts[0][0]
    assert status == 200 and events[-1]["status"] == "complete"


async def test_stop_ends_the_turn_as_stopped_and_keeps_what_was_said(
    db_path: Path, keys: Keys
) -> None:
    started = asyncio.Event()

    async def hang(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        started.set()
        await asyncio.sleep(30)
        return Step("never")

    chat = ScriptedModel([Step(calls=[("get_my_referral_code", {})]), hang])
    async with running_app(db_path, keys, chat) as h:
        send = asyncio.create_task(h.send(ESTABLISHED_USER, "Stop me", key="stop-me"))
        await asyncio.wait_for(started.wait(), 5)
        turn_id = (await query(db_path, "SELECT id FROM turns"))[0][0]
        other_users_stop = await h.client.post(
            f"/v1/conversation/turns/{turn_id}/stop", headers=h.auth(PARALLEL_USER)
        )
        stop = await h.client.post(
            f"/v1/conversation/turns/{turn_id}/stop", headers=h.auth(ESTABLISHED_USER)
        )
        _, events = await send
        again = await h.client.post(
            f"/v1/conversation/turns/{turn_id}/stop", headers=h.auth(ESTABLISHED_USER)
        )
        _, replay = await h.send(ESTABLISHED_USER, "Stop me", key="stop-me")
    assert other_users_stop.status_code == 404
    assert stop.status_code == 202 and stop.json() == {"stopped": True}
    assert again.json() == {"stopped": False}
    assert events[-1] == {"type": "turn.end", "status": "stopped", "assistant_message_id": None}
    assert replay[-1] == events[-1]
    assert (await query(db_path, "SELECT status FROM turns"))[0][0] == "stopped"
    # The tool exchange that finished before the stop is in the model history.
    payloads = " ".join(p for (p,) in await query(db_path, "SELECT payload FROM model_messages"))
    assert "get_my_referral_code" in payloads


async def test_a_failure_after_streaming_starts_is_one_error_event(
    db_path: Path, keys: Keys
) -> None:
    def boom(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        raise RuntimeError("provider exploded")

    chat = ScriptedModel([Step("Partial words.", calls=[("get_my_referral_code", {})]), boom])
    async with running_app(db_path, keys, chat) as h:
        status, events = await h.send(ESTABLISHED_USER, "Fail please", key="fail")
        _, replay = await h.send(ESTABLISHED_USER, "Fail please", key="fail")
        history = (
            await h.client.get("/v1/conversation/messages", headers=h.auth(ESTABLISHED_USER))
        ).json()
    assert status == 200
    errors = events_of(events, "error")
    assert errors == [events[-1]] and errors[0]["code"] == "generic"
    assert "provider" not in errors[0]["message"].lower()
    assert replay[-1] == events[-1]
    assert streamed_text(replay) == streamed_text(events) == "Partial words. "
    assert history["messages"][0]["status"] == "error"
    assert (await query(db_path, "SELECT status FROM turns"))[0][0] == "error"


async def test_a_turn_past_the_timeout_ends_as_one_error(db_path: Path, keys: Keys) -> None:
    """The turn timeout bounds the whole run: the turn is saved as an error."""

    async def hang(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        await asyncio.sleep(30)
        return Step("never")

    async with running_app(db_path, keys, ScriptedModel([hang]), turn_timeout_seconds=0.3) as h:
        status, events = await h.send(ESTABLISHED_USER, "Slow please")
    assert status == 200 and events[-1]["type"] == "error"
    assert (await query(db_path, "SELECT status FROM turns"))[0][0] == "error"


async def test_a_tool_call_stopped_mid_run_is_closed_by_the_framework_on_the_next_send(
    db_path: Path, keys: Keys
) -> None:
    """Stop lands while `get_promotions` runs, and the call is still audited. The stored history
    keeps the unanswered call and the framework's interrupted state; on the next send the
    framework closes the call with an interrupted result, and the turn succeeds."""
    services: list[Services] = []
    stop_armed = False
    stopped = False

    def clock() -> datetime:
        # Armed when the model returns the tool call; the next reading is the tool's own.
        nonlocal stop_armed, stopped
        if stop_armed:
            stop_armed = False
            with sqlite3.connect(db_path) as db:
                active = "SELECT id FROM turns WHERE status = 'in_progress'"
                (turn_id,) = db.execute(active).fetchone()
            stopped = services[0].stops.stop(turn_id)
        return datetime.now(UTC)

    def call_promotions(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        nonlocal stop_armed
        stop_armed = True
        return Step(calls=[("get_promotions", {"limit": 5, "cursor": None})])

    chat = ScriptedModel([call_promotions, Step("Back again.")])
    async with running_app(db_path, keys, chat, clock=clock) as h:
        services.append(h.app.state.services)
        _, stopped_events = await h.send(ESTABLISHED_USER, "Any promotions?")
        payloads = [row[0] for row in await query(db_path, "SELECT payload FROM model_messages")]
        audit = await query(db_path, "SELECT tool_name, status FROM tool_calls")
        status, events = await h.send(ESTABLISHED_USER, "Try again")

    assert stopped
    # Audited although it never returned.
    assert audit == [("get_promotions", "error")]
    assert stopped_events[-1] == {
        "type": "turn.end",
        "status": "stopped",
        "assistant_message_id": None,
    }
    stored = [message for payload in payloads for message in json.loads(payload)]
    stored_parts = [part["part_kind"] for message in stored for part in message["parts"]]
    assert "tool-call" in stored_parts and "tool-return" not in stored_parts
    assert stored[-1]["state"] == "interrupted"

    closed = [
        part
        for message in chat.seen[-1].messages
        if isinstance(message, ModelRequest)
        for part in message.parts
        if isinstance(part, ToolReturnPart) and part.tool_name == "get_promotions"
    ]
    assert len(closed) == 1 and "interrupted" in str(closed[0].content)
    assert status == 200 and streamed_text(events).strip() == "Back again."


async def test_startup_marks_stale_turns_as_error(db_path: Path, keys: Keys) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO turns (id, user_id, status, idempotency_key, request_text_hash, model, "
            "content_version, app_version, started_at) VALUES "
            "('stale', ?, 'in_progress', 'k', ?, 'm', 'c', 'v', '2026-01-01T00:00:00+00:00')",
            (ESTABLISHED_USER, request_hash("Interrupted")),
        )
        await db.commit()
    async with running_app(db_path, keys, ScriptedModel([Step("Fresh.")])) as h:
        status, _ = await h.send(ESTABLISHED_USER, "Hello")
        _, replay = await h.send(ESTABLISHED_USER, "Interrupted", key="k")
    assert status == 200
    assert (await query(db_path, "SELECT status FROM turns WHERE id = 'stale'"))[0][0] == "error"
    # Replaying a recovered turn ends with the saved error.
    assert [e["type"] for e in replay] == ["turn.start", "error"]


async def test_feedback_is_saved_replaced_and_scoped(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel([Step("Rate me.")])) as h:
        _, events = await h.send(ESTABLISHED_USER, "Hi")
        message_id = events[-1]["assistant_message_id"]
        url = f"/v1/conversation/messages/{message_id}/feedback"
        up = await h.client.post(url, json={"rating": "up"}, headers=h.auth(ESTABLISHED_USER))
        down = await h.client.post(
            url, json={"rating": "down", "comment": "Too long"}, headers=h.auth(ESTABLISHED_USER)
        )
        other = await h.client.post(url, json={"rating": "up"}, headers=h.auth(PARALLEL_USER))
        user_message = await h.client.post(
            f"/v1/conversation/messages/{events[0]['user_message_id']}/feedback",
            json={"rating": "up"},
            headers=h.auth(ESTABLISHED_USER),
        )
        bad = await h.client.post(url, json={"rating": "meh"}, headers=h.auth(ESTABLISHED_USER))
    assert up.status_code == 200 and down.json()["rating"] == "down"
    assert down.json()["comment"] == "Too long"
    assert other.status_code == 404 and user_message.status_code == 404
    assert bad.status_code == 422
    assert await query(db_path, "SELECT rating, comment FROM message_feedback") == [
        ("down", "Too long")
    ]


async def test_users_never_see_each_others_conversations(db_path: Path, keys: Keys) -> None:
    async with running_app(db_path, keys, ScriptedModel([Step("Private.")])) as h:
        _, events = await h.send(ESTABLISHED_USER, "My secret")
        theirs = (
            await h.client.get("/v1/conversation/messages", headers=h.auth(PARALLEL_USER))
        ).json()
        state = (await h.client.get("/v1/conversation", headers=h.auth(PARALLEL_USER))).json()
        # Another user reusing the same Idempotency-Key starts their own turn.
        status, _ = await h.send(PARALLEL_USER, "Mine", key=events[0]["turn_id"])
    assert theirs["messages"] == []
    assert state["turn_in_progress"] is False
    assert status == 200
    assert json.dumps(theirs).find("My secret") == -1


async def test_the_terminal_event_is_sent_only_after_the_commit(db_path: Path, keys: Keys) -> None:
    """Reading the runner's queue directly: when `turn.end` arrives, the turn is already saved."""
    async with running_app(db_path, keys, ScriptedModel([Step("Saved first.")])) as h:
        services: Services = h.app.state.services
        snapshot = await services.conversations.snapshot()
        started = await services.conversations.start_turn(ESTABLISHED_USER, "Hi", "k", snapshot)
        assert isinstance(started, StartedTurn)
        queue = services.runner.start(started, snapshot)
        while (event := await queue.get()) is not None:
            if event["type"] in {"turn.end", "error"}:
                status = await query(
                    db_path, "SELECT status FROM turns WHERE id = ?", started.turn_id
                )
                messages = await query(db_path, "SELECT role FROM messages ORDER BY created_at")
                assert status == [("complete",)]
                assert [role for (role,) in messages] == ["user", "assistant"]
