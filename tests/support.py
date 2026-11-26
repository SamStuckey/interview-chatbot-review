"""Test helpers: a scripted model, settings, a seeded database, an app client, and tokens.

Specs never call a real model (`ALLOW_MODEL_REQUESTS = False`) and each test
gets its own copy of a migrated, seeded, ingested database.
"""

import asyncio
import json
import os
import shutil
from collections.abc import AsyncGenerator, AsyncIterator, Awaitable, Callable, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import jwt
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, DeltaToolCalls, FunctionModel

from capper.app import create_app
from capper.config import Settings
from capper.db import create_engine, create_session_factory
from capper.time import Clock, utc_now
from ingestion import ingest
from scripts.seed import seed

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "supporting-files" / "Carton Caps Data.sqlite"
MANIFEST = ROOT / "content" / "manifest.toml"
ISSUER = "carton-caps-auth"
AUDIENCE = "capper"

ESTABLISHED_USER = 1
PARALLEL_USER = 2
GUIDANCE_USER = 3


# ---------- Scripted models ----------


@dataclass
class Step:
    """One model response: optional text, then tool calls `(name, args)`."""

    text: str = ""
    calls: list[tuple[str, dict[str, Any]]] = field(
        default_factory=list[tuple[str, dict[str, Any]]]
    )


type StepFn = Callable[[list[ModelMessage], AgentInfo], Step | Awaitable[Step]]


@dataclass
class Seen:
    messages: list[ModelMessage]
    info: AgentInfo


def estimated_input_tokens(messages: list[ModelMessage], instructions: str | None) -> int:
    """Roughly 4 characters per token over everything sent, as a provider would count it."""
    chars = len(instructions or "")
    for message in messages:
        parts = message.parts
        chars += sum(
            len(str(getattr(part, "content", "") or getattr(part, "args", ""))) for part in parts
        )
    return chars // 4


class MeasuredFunctionModel(FunctionModel):
    """A `FunctionModel` whose streamed responses report a realistic input-token count.

    The stock streamed response always reports ~50 input tokens, which would anchor the
    Harness budget far too low for compaction to ever trigger in a spec.
    """

    @asynccontextmanager
    async def request_stream(  # pyright: ignore[reportIncompatibleMethodOverride]
        self,
        messages: list[ModelMessage],
        model_settings: Any,
        model_request_parameters: Any,
        run_context: Any = None,
    ) -> AsyncGenerator[Any]:
        from pydantic_ai.usage import RequestUsage

        async with super().request_stream(
            messages, model_settings, model_request_parameters, run_context
        ) as response:
            instructions = next(
                (
                    m.instructions
                    for m in reversed(messages)
                    if isinstance(m, ModelRequest) and m.instructions is not None
                ),
                None,
            )
            response._usage = RequestUsage(  # pyright: ignore[reportPrivateUsage]
                input_tokens=estimated_input_tokens(messages, instructions)
            )
            yield response


class ScriptedModel:
    """A `FunctionModel` playing `steps` in order (then "Done."), recording each request."""

    def __init__(self, steps: Sequence[Step | StepFn] = ()) -> None:
        self.steps: list[Step | StepFn] = list(steps)
        self.seen: list[Seen] = []
        self.model = MeasuredFunctionModel(
            self._call, stream_function=self._stream, model_name="scripted"
        )

    async def _next(self, messages: list[ModelMessage], info: AgentInfo) -> Step:
        self.seen.append(Seen(list(messages), info))
        if not self.steps:
            return Step("Done.")
        step = self.steps.pop(0)
        if isinstance(step, Step):
            return step
        result = step(messages, info)
        return await result if isinstance(result, Awaitable) else result

    async def _call(self, messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        step = await self._next(messages, info)
        parts: list[TextPart | ToolCallPart] = [TextPart(step.text)] if step.text else []
        parts += [ToolCallPart(name, args) for name, args in step.calls]
        return ModelResponse(parts=parts)

    async def _stream(
        self, messages: list[ModelMessage], info: AgentInfo
    ) -> AsyncIterator[str | DeltaToolCalls]:
        step = await self._next(messages, info)
        if step.text:
            for word in step.text.split(" "):
                yield word + " " if word else " "
        for index, (name, args) in enumerate(step.calls):
            yield {index: DeltaToolCall(name=name, json_args=json.dumps(args))}


DEFAULT_SUMMARY = (
    "## Goals and constraints the user stated\nThe user asked Capper for snack ideas.\n\n"
    "## IDs mentioned\nNone.\n\n## What happened\nCapper answered.\n\n## Open questions\nNone."
)


@dataclass
class Auxiliary:
    """The compaction model: `summaries` are returned in order (the last repeats)."""

    summaries: list[str] = field(default_factory=lambda: [DEFAULT_SUMMARY])
    summary_calls: int = 0
    summary_prompts: list[str] = field(default_factory=list[str])

    @property
    def model(self) -> FunctionModel:
        return FunctionModel(self._answer, model_name="auxiliary")

    async def _answer(self, messages: list[ModelMessage], _info: AgentInfo) -> ModelResponse:
        self.summary_prompts.append(_last_user_text(messages))
        index = min(self.summary_calls, len(self.summaries) - 1)
        self.summary_calls += 1
        return ModelResponse(parts=[TextPart(self.summaries[index])])


def _last_user_text(messages: list[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                    return part.content
    return ""


class SteppingClock:
    """A clock for specs: returns `now`, then moves on a second, so one turn's rows keep order."""

    def __init__(self, start: datetime | None = None) -> None:
        self.now = start or datetime(2026, 1, 1, tzinfo=UTC)

    def __call__(self) -> datetime:
        current = self.now
        self.now += timedelta(seconds=1)
        return current


# ---------- Keys, settings, database ----------


@dataclass(frozen=True)
class Keys:
    private_path: Path
    public_path: Path
    private_pem: str


def make_keys(directory: Path) -> Keys:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "private.pem").write_bytes(private_pem)
    (directory / "public.pem").write_bytes(public_pem)
    return Keys(directory / "private.pem", directory / "public.pem", private_pem.decode())


def database_url(path: Path) -> str:
    return f"sqlite+aiosqlite:///{path}"


def migrate(path: Path, revision: str = "head", *, down: bool = False) -> None:
    previous = os.environ.get("CAPPER_DATABASE_URL")
    os.environ["CAPPER_DATABASE_URL"] = database_url(path)
    try:
        config = Config(str(ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "alembic"))
        if down:
            command.downgrade(config, revision)
        else:
            command.upgrade(config, revision)
    finally:
        if previous is None:
            del os.environ["CAPPER_DATABASE_URL"]
        else:
            os.environ["CAPPER_DATABASE_URL"] = previous


async def seed_and_ingest(path: Path) -> None:
    engine = create_engine(database_url(path))
    try:
        sessions = create_session_factory(engine)
        async with sessions() as session:
            await seed(session)
        async with sessions() as session:
            await ingest(session, MANIFEST)
    finally:
        await engine.dispose()


def build_template(directory: Path) -> Path:
    """A migrated, seeded and ingested database, built once per test session."""
    path = directory / "template.db"
    shutil.copyfile(FIXTURE, path)
    migrate(path)
    asyncio.run(seed_and_ingest(path))
    return path


def make_settings(db_path: Path, keys: Keys, **overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "openai_api_key": "test-key",
        "cache_key_secret": "test-secret",
        "database_url": database_url(db_path),
        "jwt_public_key_path": str(keys.public_path),
        "jwt_private_key_path": str(keys.private_path),
        "jwt_issuer": ISSUER,
        "jwt_audience": AUDIENCE,
        "otlp_endpoint": None,
        "turn_timeout_seconds": 10.0,
        **overrides,
    }
    return Settings(**values)


def token(keys: Keys, user_id: int, **claims: Any) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        **claims,
    }
    return jwt.encode(payload, keys.private_pem, algorithm="RS256")


# ---------- The app under test ----------


@dataclass
class Harness:
    app: FastAPI
    client: httpx.AsyncClient
    chat: ScriptedModel
    keys: Keys
    settings: Settings

    def auth(self, user_id: int) -> dict[str, str]:
        return {"Authorization": f"Bearer {token(self.keys, user_id)}"}

    async def send(
        self, user_id: int, text: str, key: str | None = None
    ) -> tuple[int, list[dict[str, Any]]]:
        """POST a message and read the whole NDJSON stream."""
        headers = {**self.auth(user_id), "Idempotency-Key": key or os.urandom(8).hex()}
        response = await self.client.post(
            "/v1/conversation/messages", json={"text": text}, headers=headers
        )
        if response.status_code != 200:
            return response.status_code, [response.json()]
        events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
        return 200, events


@asynccontextmanager
async def running_app(
    db_path: Path,
    keys: Keys,
    chat: ScriptedModel,
    *,
    auxiliary: Auxiliary | None = None,
    chat_model: Model | None = None,
    compaction_model: Model | None = None,
    tracer_provider: TracerProvider | None = None,
    clock: Clock = utc_now,
    **overrides: Any,
) -> AsyncGenerator[Harness]:
    settings = make_settings(db_path, keys, **overrides)
    app = create_app(
        settings,
        chat_model=chat_model or chat.model,
        compaction_model=compaction_model or (auxiliary or Auxiliary()).model,
        tracer_provider=tracer_provider,
        clock=clock,
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield Harness(app, client, chat, keys, settings)


def events_of(events: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [event for event in events if event["type"] == kind]


def streamed_text(events: list[dict[str, Any]]) -> str:
    return "".join(event["text"] for event in events_of(events, "text.delta"))
