"""Compaction persistence, reload cycles, heading checks, isolation, and tool-result clearing."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiosqlite
import httpx2
import pytest
from openai import AsyncOpenAI
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from pydantic_ai.messages import (
    CompactionPart,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import AgentInfo

from capper.agent.agent import opaque_user_key, openai_model
from capper.context.builder import load_history, user_prompt_payload
from capper.context.compaction import find_compaction
from capper.conversation.service import ConversationService
from capper.db import create_engine, create_session_factory
from tests.support import (
    ESTABLISHED_USER,
    Auxiliary,
    Harness,
    Keys,
    ScriptedModel,
    Seen,
    Step,
    SteppingClock,
    database_url,
    running_app,
)

# Large enough that instructions plus the kept tail fit under the trigger after a compaction.
BUDGET: dict[str, Any] = {"history_budget_tokens": 14_000, "min_clear_tokens": 0}
ANSWER = "Here is a long answer. " + "word " * 300


def turn_steps(count: int) -> list[Step]:
    steps: list[Step] = []
    for _ in range(count):
        steps.append(Step(calls=[("search_products", {"query": None, "limit": 5, "cursor": None})]))
        steps.append(Step(ANSWER))
    return steps


async def run_turns(h: Harness, count: int, start: int = 0) -> list[list[dict[str, Any]]]:
    results: list[list[dict[str, Any]]] = []
    for i in range(start, start + count):
        status, events = await h.send(ESTABLISHED_USER, f"Question {i}. " + "please " * 40)
        assert status == 200
        results.append(events)
    return results


async def rows(db_path: Path, sql: str) -> list[tuple[Any, ...]]:
    async with aiosqlite.connect(db_path) as db:
        return [tuple(row) for row in await (await db.execute(sql)).fetchall()]


def pairs_intact(messages: list[ModelMessage]) -> bool:
    calls = {
        p.tool_call_id
        for m in messages
        if isinstance(m, ModelResponse)
        for p in m.parts
        if isinstance(p, ToolCallPart)
    }
    returns = {
        p.tool_call_id
        for m in messages
        if isinstance(m, ModelRequest)
        for p in m.parts
        if isinstance(p, ToolReturnPart)
    }
    return calls == returns


def prompts_seen(seen: Seen) -> list[str]:
    return [
        p.content
        for m in seen.messages
        if isinstance(m, ModelRequest)
        for p in m.parts
        if isinstance(p, UserPromptPart)
        and isinstance(p.content, str)
        and p.content.startswith("Question")
    ]


async def test_compaction_persists_a_summary_and_reload_matches(db_path: Path, keys: Keys) -> None:
    turns = 14
    chat = ScriptedModel(turn_steps(turns + 1))
    async with running_app(db_path, keys, chat, auxiliary=Auxiliary(), **BUDGET) as h:
        await run_turns(h, turns)
        summaries = await rows(
            db_path, "SELECT id, covers_through_model_message_id, text FROM summaries ORDER BY id"
        )
        assert summaries, "the budget should have forced a compaction"
        _, watermark, text = summaries[-1]

        # The transcript is never touched: every message of every turn is still there.
        transcript = await rows(db_path, "SELECT role FROM messages")
        assert len(transcript) == 2 * turns

        # Reload = the latest summary plus exactly the stored messages after its watermark.
        engine = create_engine(database_url(db_path))
        service = ConversationService(
            create_session_factory(engine),
            lambda: datetime.now(UTC),
            max_message_chars=8000,
            model_name="m",
            app_version="v",
            prompt_payload=user_prompt_payload,
        )
        stored = await service.load_history(ESTABLISHED_USER)
        await engine.dispose()
        loaded = load_history(stored.summary_payload, stored.payloads)
        after = await rows(
            db_path, f"SELECT id FROM model_messages WHERE id > {watermark} ORDER BY id"
        )
        assert stored.row_ids == [None, *[r[0] for r in after]]
        first = loaded[0]
        assert isinstance(first, ModelRequest) and isinstance(first.parts[0], CompactionPart)
        assert first.parts[0].content == text
        assert pairs_intact(loaded[1:])

        # The next turn's model request starts from that reload: summary in, early turns out.
        await run_turns(h, 1, start=turns)
        next_turn = chat.seen[-2]
        assert any(
            isinstance(p, CompactionPart) and p.content == text
            for m in next_turn.messages
            if isinstance(m, ModelRequest)
            for p in m.parts
        )
        assert "Question 0. " not in " ".join(prompts_seen(next_turn))
        for seen in chat.seen:
            assert pairs_intact(seen.messages)


def leading_summary(messages: list[ModelMessage]) -> str | None:
    """The summary text a request opens with, if it opens with one."""
    first = messages[0] if messages else None
    if isinstance(first, ModelRequest):
        for part in first.parts:
            if isinstance(part, CompactionPart):
                return part.content
    return None


async def test_a_turn_that_compacts_then_fails_keeps_its_summary(db_path: Path, keys: Keys) -> None:
    """The chat model fails on the request a compaction just shortened: the turn is saved as an
    error with its summary, and the next turn loads from that summary."""
    scripted = turn_steps(18)
    failed = False

    def fail_once_compacted(messages: list[ModelMessage], _info: AgentInfo) -> Step:
        nonlocal failed
        if not failed and leading_summary(messages) is not None:
            failed = True
            raise RuntimeError("chat model down")
        return scripted.pop(0)

    chat = ScriptedModel([fail_once_compacted] * 40)
    async with running_app(db_path, keys, chat, **BUDGET) as h:
        turn = 0
        while not failed:
            assert turn < 16, "the budget should have forced a compaction"
            await run_turns(h, 1, start=turn)
            turn += 1
        statuses = await rows(db_path, "SELECT status FROM turns ORDER BY started_at")
        assert statuses[-1] == ("error",)
        summaries = await rows(db_path, "SELECT text FROM summaries ORDER BY id")
        assert summaries, "the failed turn's summary should be saved"

        await run_turns(h, 1, start=turn)
    assert leading_summary(chat.seen[-2].messages) == summaries[-1][0]


async def test_summarizer_requests_opt_out_of_storage(db_path: Path, keys: Keys) -> None:
    """The Harness summarizer runs its own agent with no settings; its requests still opt out."""
    bodies: list[dict[str, Any]] = []

    def refuse(request: httpx2.Request) -> httpx2.Response:
        bodies.append(json.loads(request.content))
        return httpx2.Response(400, json={"error": {"message": "refused in a spec"}})

    client = AsyncOpenAI(
        api_key="spec", http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(refuse))
    )
    chat = ScriptedModel(turn_steps(16))
    # Requests are allowed only because the transport above answers them in-process.
    with override_allow_model_requests(True):
        async with running_app(
            db_path, keys, chat, compaction_model=openai_model("spec-model", client), **BUDGET
        ) as h:
            for i in range(16):
                await run_turns(h, 1, start=i)
                if bodies:
                    break
    assert bodies, "the budget should have forced a compaction"
    assert all(body["store"] is False for body in bodies)


async def test_compact_reload_compact_folds_the_previous_summary(db_path: Path, keys: Keys) -> None:
    turns = 20
    aux = Auxiliary()
    chat = ScriptedModel(turn_steps(turns))
    async with running_app(db_path, keys, chat, auxiliary=aux, **BUDGET) as h:
        await run_turns(h, turns)
    summaries = await rows(
        db_path, "SELECT covers_through_model_message_id FROM summaries ORDER BY id"
    )
    assert len(summaries) >= 2
    watermarks = [w for (w,) in summaries]
    assert watermarks == sorted(watermarks) and len(set(watermarks)) == len(watermarks)
    # A later compaction updates the earlier summary rather than starting over (incremental).
    assert any("<previous-summary>" in prompt for prompt in aux.summary_prompts[1:])


async def test_a_summary_missing_a_heading_is_retried_then_used(db_path: Path, keys: Keys) -> None:
    aux = Auxiliary(summaries=["just some prose", Auxiliary().summaries[0]])
    chat = ScriptedModel(turn_steps(16))
    async with running_app(db_path, keys, chat, auxiliary=aux, **BUDGET) as h:
        results = await run_turns(h, 16)
    assert all(events[-1]["type"] == "turn.end" for events in results)
    texts = await rows(db_path, "SELECT text FROM summaries")
    assert texts and all("## Open questions" in text for (text,) in texts)


async def test_a_summary_that_keeps_missing_headings_fails_the_turn(
    db_path: Path, keys: Keys
) -> None:
    aux = Auxiliary(summaries=["just some prose"])
    chat = ScriptedModel(turn_steps(16))
    async with running_app(db_path, keys, chat, auxiliary=aux, **BUDGET) as h:
        results = await run_turns(h, 16)
    assert any(events[-1]["type"] == "error" for events in results)
    assert await rows(db_path, "SELECT id FROM summaries") == []
    statuses = {status for (status,) in await rows(db_path, "SELECT status FROM turns")}
    assert "error" in statuses


async def test_runs_carry_the_users_opaque_key_as_conversation_id(
    db_path: Path, keys: Keys
) -> None:
    chat = ScriptedModel([Step("Hi.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "Hello")
        expected = opaque_user_key(h.settings.cache_key_secret.get_secret_value(), ESTABLISHED_USER)
    payloads = await rows(db_path, "SELECT payload FROM model_messages")
    assert any(expected in payload for (payload,) in payloads)
    assert str(ESTABLISHED_USER) != expected


async def test_clearing_keeps_the_active_turn_and_recent_results(db_path: Path, keys: Keys) -> None:
    turns = 6
    calls_per_turn = 4
    steps: list[Step] = []
    for _ in range(turns):
        steps.append(
            Step(
                calls=[("search_products", {"query": None, "limit": 8, "cursor": None})]
                * calls_per_turn
            )
        )
        steps.append(Step("Short answer."))
    chat = ScriptedModel(steps)
    # A budget where clearing has work to do; compaction may follow, which is fine here.
    async with running_app(
        db_path, keys, chat, history_budget_tokens=9_000, min_clear_tokens=0
    ) as h:
        for i in range(turns):
            await h.send(ESTABLISHED_USER, f"Question {i}")
    for seen in chat.seen:
        returns = [
            p
            for m in seen.messages
            if isinstance(m, ModelRequest)
            for p in m.parts
            if isinstance(p, ToolReturnPart)
        ]
        cleared = [p for p in returns if p.content == "[tool result cleared]"]
        # The newest results are never cleared: at least five past ones plus the active turn's.
        kept = [p for p in returns if p.content != "[tool result cleared]"]
        if cleared:
            assert len(kept) >= min(len(returns), 5 + calls_per_turn)
            assert returns[-1].content != "[tool result cleared]"
    assert any(
        p.content == "[tool result cleared]"
        for seen in chat.seen
        for m in seen.messages
        if isinstance(m, ModelRequest)
        for p in m.parts
        if isinstance(p, ToolReturnPart)
    ), "the budget should have forced clearing"


def test_find_compaction_places_the_suffix_by_position() -> None:
    from pydantic_ai_harness.compaction._summary import summary_request

    from capper.context.compaction import CompactionShapeError

    summary = summary_request("## Open questions\nNone.")
    first = ModelRequest(parts=[UserPromptPart("first")])
    second = ModelRequest(parts=[UserPromptPart("second")])
    new: list[ModelMessage] = [ModelResponse(parts=[])]
    loaded: list[ModelMessage] = [first, second]
    # Nothing compacted: the history starts with what was loaded.
    assert find_compaction(loaded, new, [*loaded, *new]) is None
    # [summary, second, new]: the suffix starts at index 1 of loaded + new.
    result = find_compaction(loaded, new, [summary, second, *new])
    assert result is not None and result.first_kept == 1
    # A suffix as long as everything leaves nothing summarized: never guessed.
    with pytest.raises(CompactionShapeError):
        find_compaction(loaded, new, [summary, first, second, *new])
    # A summary anywhere but the start is a shape we don't place.
    with pytest.raises(CompactionShapeError):
        find_compaction(loaded, new, [first, summary, *new])


async def test_a_date_search_reaches_messages_compacted_away(db_path: Path, keys: Keys) -> None:
    """Compaction changes only what the model sees; the transcript stays searchable by date."""
    turns = 16
    found = Step(
        calls=[
            (
                "search_my_history",
                {"query": None, "start_date": "2026-01-01", "end_date": "2026-01-01"},
            )
        ]
    )
    chat = ScriptedModel([*turn_steps(turns), found, Step("We talked about it.")])
    # 18:00 UTC is January 1 in every US time zone, whichever one the seed gave the user.
    january_1 = SteppingClock(datetime(2026, 1, 1, 18, tzinfo=UTC))
    async with running_app(db_path, keys, chat, clock=january_1, **BUDGET) as h:
        await run_turns(h, turns)
        await h.send(ESTABLISHED_USER, "What did we talk about on January 1?")
    assert await rows(db_path, "SELECT id FROM summaries"), "the budget should have compacted"
    assert "Question 0. " not in " ".join(prompts_seen(chat.seen[-1]))
    returned = [
        p.content
        for p in chat.seen[-1].messages[-1].parts
        if isinstance(p, ToolReturnPart) and p.tool_name == "search_my_history"
    ]
    assert "Question 0." in str(returned[0])


async def test_the_trace_names_the_summaries_each_turn_loaded_and_saved(
    db_path: Path, keys: Keys
) -> None:
    """Loaded and saved summary rows are events of their own, apart from the compaction."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    turns = 20
    chat = ScriptedModel(turn_steps(turns))
    async with running_app(db_path, keys, chat, tracer_provider=provider, **BUDGET) as h:
        await run_turns(h, turns)
    summaries = await rows(
        db_path, "SELECT id, covers_through_model_message_id FROM summaries ORDER BY id"
    )
    assert len(summaries) >= 2
    spans = sorted(
        (s for s in exporter.get_finished_spans() if s.name == "capper.turn"),
        key=lambda s: s.start_time or 0,
    )

    def events(name: str) -> list[dict[str, Any]]:
        return [dict(e.attributes or {}) for s in spans for e in s.events if e.name == name]

    assert [e["summary_id"] for e in events("context.summary_saved")] == [i for i, _ in summaries]
    assert summaries[0][0] in {e["summary_id"] for e in events("context.summary_loaded")}
    compactions = events("context.compaction")
    assert len(compactions) == len(summaries)
    assert "previous_cutoff_message_id" not in compactions[0]
    assert compactions[1]["previous_cutoff_message_id"] == summaries[0][1]
    assert all(c["kept_from_position"] > 0 for c in compactions)
