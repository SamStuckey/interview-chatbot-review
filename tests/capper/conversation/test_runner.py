"""Model requests: context, continuation after stop, content snapshots, and telemetry."""

import asyncio
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
    ModelMessage,
    ModelRequest,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import AgentInfo

from capper.agent.agent import opaque_user_key, openai_model
from capper.context.builder import (
    ACCOUNT_CONTEXT_HEADER,
    TURN_CONTEXT_HEADER,
)
from capper.db import create_engine, create_session_factory
from content_bundle import DocumentSource, publish
from tests.support import (
    ESTABLISHED_USER,
    GUIDANCE_USER,
    Auxiliary,
    Keys,
    ScriptedModel,
    Seen,
    Step,
    SteppingClock,
    database_url,
    running_app,
)


def user_texts(seen: Seen) -> list[str]:
    return [
        p.content
        for m in seen.messages
        if isinstance(m, ModelRequest)
        for p in m.parts
        if isinstance(p, UserPromptPart) and isinstance(p.content, str)
    ]


async def stored_payloads(db_path: Path) -> str:
    async with aiosqlite.connect(db_path) as db:
        rows = await (await db.execute("SELECT payload FROM model_messages")).fetchall()
    return " ".join(str(row[0]) for row in rows)


async def test_the_request_is_assembled_in_order(db_path: Path, keys: Keys) -> None:
    chat = ScriptedModel([Step("First."), Step("Second.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(GUIDANCE_USER, "Earlier question")
        await h.send(GUIDANCE_USER, "Snack ideas?")
    texts = user_texts(chat.seen[1])
    account = next(i for i, t in enumerate(texts) if t.startswith(ACCOUNT_CONTEXT_HEADER))
    earlier = texts.index("Earlier question")
    turn = next(i for i, t in enumerate(texts) if t.startswith(TURN_CONTEXT_HEADER))
    prompt = texts.index("Snack ideas?")
    assert account < earlier < turn < prompt == turn + 1
    # Guidance is a data block, never instructions; the avoid list isn't sent.
    assert "Allergic to peanuts." in texts[account]
    assert all("Peanut Butter" not in text for seen in chat.seen for text in user_texts(seen))
    instructions = chat.seen[1].info.instructions or ""
    assert "Allergic to peanuts." not in instructions
    assert "Capper" in instructions and "Referral program" in instructions


async def test_instructions_are_identical_for_a_content_version(db_path: Path, keys: Keys) -> None:
    chat = ScriptedModel([Step("A."), Step("B.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "One")
        await h.send(GUIDANCE_USER, "Two")
    assert chat.seen[0].info.instructions == chat.seen[1].info.instructions


async def test_request_only_context_is_never_stored(db_path: Path, keys: Keys) -> None:
    chat = ScriptedModel([Step("Noted.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(GUIDANCE_USER, "Hello")
    payloads = await stored_payloads(db_path)
    assert "Hello" in payloads
    assert ACCOUNT_CONTEXT_HEADER not in payloads and TURN_CONTEXT_HEADER not in payloads
    assert "Allergic to peanuts." not in payloads


async def test_expired_guidance_is_left_out(db_path: Path, keys: Keys) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO guidance_notes (user_id, text, expires_at, created_at, updated_at) VALUES "
            "(?, 'Old holiday plan.', '2020-01-01T00:00:00+00:00', "
            "'2019-12-01T00:00:00+00:00', '2019-12-01T00:00:00+00:00')",
            (ESTABLISHED_USER,),
        )
        await db.commit()
    chat = ScriptedModel([Step("Ok.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "Hi")
    account = next(t for t in user_texts(chat.seen[0]) if t.startswith(ACCOUNT_CONTEXT_HEADER))
    assert "Shops for a family of four." in account
    assert "Old holiday plan." not in account


async def test_local_time_is_in_the_users_own_zone(db_path: Path, keys: Keys) -> None:
    """A user's own time zone wins; others get the configured default."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE Users SET time_zone = 'America/Los_Angeles' WHERE id = ?", (ESTABLISHED_USER,)
        )
        await db.execute("UPDATE Users SET time_zone = NULL WHERE id = ?", (GUIDANCE_USER,))
        await db.commit()
    chat = ScriptedModel([Step("A."), Step("B.")])
    noon_utc = SteppingClock(datetime(2026, 11, 17, 20, tzinfo=UTC))
    async with running_app(db_path, keys, chat, clock=noon_utc) as h:
        await h.send(ESTABLISHED_USER, "Hi")
        await h.send(GUIDANCE_USER, "Hi")
    times = [
        next(t for t in user_texts(seen) if t.startswith(TURN_CONTEXT_HEADER)) for seen in chat.seen
    ]
    assert "Tuesday, November 17, 2026, 12:00 PM PST" in times[0]
    assert "Tuesday, November 17, 2026, 8:00 PM UTC" in times[1]


async def test_stop_then_continue_keeps_the_original_request(db_path: Path, keys: Keys) -> None:
    """After a stop, a narrowing follow-up still has the original request."""
    started = asyncio.Event()

    async def hang(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        started.set()
        await asyncio.sleep(30)
        return Step("never")

    chat = ScriptedModel([hang, Step("Here are some snacks.")])
    async with running_app(db_path, keys, chat) as h:
        send = asyncio.create_task(h.send(ESTABLISHED_USER, "Recommend groceries for the week"))
        await asyncio.wait_for(started.wait(), 5)
        async with aiosqlite.connect(db_path) as db:
            (turn_id,) = await (await db.execute("SELECT id FROM turns")).fetchone() or ("",)
        await h.client.post(
            f"/v1/conversation/turns/{turn_id}/stop", headers=h.auth(ESTABLISHED_USER)
        )
        await send
        await h.send(ESTABLISHED_USER, "Actually, just snacks")
    texts = user_texts(chat.seen[-1])
    assert "Recommend groceries for the week" in texts
    assert texts[-1] == "Actually, just snacks"


async def test_model_settings_and_the_opaque_cache_key(db_path: Path, keys: Keys) -> None:
    chat = ScriptedModel([Step("Hi.")])
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "Hello")
        key = opaque_user_key(h.settings.cache_key_secret.get_secret_value(), ESTABLISHED_USER)
    settings: dict[str, Any] = dict(chat.seen[0].info.model_settings or {})
    assert settings["openai_reasoning_context"] == "current_turn"
    assert settings["openai_send_reasoning_ids"] is False
    assert settings["openai_truncation"] == "disabled"
    assert settings["max_tokens"] == 4096
    assert settings["openai_prompt_cache_key"] == key
    assert "openai_previous_response_id" not in settings
    assert "openai_conversation_id" not in settings
    # The app never puts the internal user ID into the context it builds.
    built = [
        t
        for t in user_texts(chat.seen[0])
        if t.startswith((ACCOUNT_CONTEXT_HEADER, TURN_CONTEXT_HEADER))
    ]
    assert all(f'"user_id": {ESTABLISHED_USER}' not in t for t in built)
    assert key != str(ESTABLISHED_USER)


async def test_a_turn_reads_one_content_snapshot(db_path: Path, keys: Keys) -> None:
    """Publishing mid-turn doesn't change what the running turn's `read_document` sees."""

    async def publish_then_read(_messages: list[ModelMessage], _info: AgentInfo) -> Step:
        engine = create_engine(database_url(db_path))
        async with create_session_factory(engine)() as session:
            async with session.begin():
                from sqlalchemy import select

                from content_bundle.store import ContentDocument

                current = (
                    await session.scalars(select(ContentDocument).where(ContentDocument.active))
                ).all()
                sources = [
                    DocumentSource(d.name, d.content_class, d.load, d.body)  # pyright: ignore[reportArgumentType]
                    for d in current
                    if d.name != "policy_crisis"
                ]
            sources.append(
                DocumentSource("policy_crisis", "operator_policy", "on_demand", "CHANGED MID-TURN")
            )
            await publish(session, sources)
        await engine.dispose()
        return Step(calls=[("read_document", {"name": "policy_crisis"})])

    chat = ScriptedModel(
        [
            publish_then_read,
            Step("Done."),
            Step(calls=[("read_document", {"name": "policy_crisis"})]),
            Step("Again."),
        ]
    )
    async with running_app(db_path, keys, chat) as h:
        await h.send(ESTABLISHED_USER, "First turn")
        await h.send(ESTABLISHED_USER, "Second turn")
    first = [p.content for p in chat.seen[1].messages[-1].parts if isinstance(p, ToolReturnPart)]
    second = [p.content for p in chat.seen[3].messages[-1].parts if isinstance(p, ToolReturnPart)]
    assert "988" in str(first[0])
    assert str(second[0]).strip() == "CHANGED MID-TURN"


async def test_a_turn_goes_straight_to_the_chat_model_and_traces_no_text(
    db_path: Path, keys: Keys
) -> None:
    """No auxiliary model call precedes the reply; time to first token is on the turn span,
    and no message text reaches any span."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    aux = Auxiliary()
    secret = "my private question about tortillas"
    async with running_app(
        db_path,
        keys,
        ScriptedModel([Step("A secret answer.")]),
        auxiliary=aux,
        tracer_provider=provider,
    ) as h:
        await h.send(ESTABLISHED_USER, secret)
    assert aux.summary_calls == 0
    spans = exporter.get_finished_spans()
    turn = next(s for s in spans if s.name == "capper.turn")
    assert "capper.time_to_first_token_ms" in dict(turn.attributes or {})
    for span in spans:
        dumped = str(span.to_json())
        assert secret not in dumped and "A secret answer" not in dumped, span.name


async def test_a_context_limit_rejection_is_named_but_never_quoted(
    db_path: Path, keys: Keys, caplog: pytest.LogCaptureFixture
) -> None:
    """The trace says what failed and where; neither the trace, the log nor the client sees the
    provider's message, which can echo the request."""
    secret = "my private question about tortillas"

    def reject(_request: httpx2.Request) -> httpx2.Response:
        error = {
            "message": f"Input too long: {secret}",
            "type": "invalid_request_error",
            "code": "context_length_exceeded",
        }
        return httpx2.Response(400, json={"error": error})

    client = AsyncOpenAI(
        api_key="spec", http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(reject))
    )
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # Requests are allowed only because the transport above answers them in-process.
    with override_allow_model_requests(True):
        async with running_app(
            db_path,
            keys,
            ScriptedModel(),
            chat_model=openai_model("spec-model", client),
            tracer_provider=provider,
        ) as h:
            status, events = await h.send(ESTABLISHED_USER, secret)
    assert status == 200 and events[-1]["type"] == "error"
    assert secret not in json.dumps(events)
    spans = exporter.get_finished_spans()
    turn_span = next(s for s in spans if s.name == "capper.turn")
    usage = [dict(e.attributes or {}) for e in turn_span.events if e.name == "context.usage"]
    assert usage and usage[0]["budget_tokens"] == h.settings.history_budget_tokens
    turn = dict(turn_span.attributes or {})
    assert turn["error.type"] == "context_limit"
    assert turn["capper.provider_error_code"] == "context_length_exceeded"
    assert turn["http.response.status_code"] == 400
    assert turn["capper.status"] == "error" and turn["capper.turn_id"]
    assert turn["capper.model"] == h.settings.chat_model
    assert all(secret not in str(span.to_json()) for span in spans)
    assert "context_limit" in caplog.text and secret not in caplog.text
