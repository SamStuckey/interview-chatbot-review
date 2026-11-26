"""The composition root: settings, engine, services, agent, routes and lifespan.

Constructs settings and concrete dependencies for the service. Tests and evals
can inject models, a tracer provider, or a clock through the same app factory.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from importlib.metadata import version
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from opentelemetry.sdk.trace import TracerProvider
from pydantic_ai.models import Model

from capper.accounts.service import AccountService
from capper.agent.agent import build_agent, build_model
from capper.agent.deps import ToolServices
from capper.auth.service import DemoSessionIssuer, TokenVerifier
from capper.catalog.images import PRODUCT_IMAGES, URL_PREFIX
from capper.catalog.service import CatalogService
from capper.config import Settings
from capper.container import Services
from capper.context.builder import user_prompt_payload
from capper.conversation.api import router as conversation_router
from capper.conversation.audit import ToolAuditLog
from capper.conversation.history_search import HistorySearchService
from capper.conversation.runner import RunnerConfig, TurnRunner
from capper.conversation.service import ConversationService
from capper.conversation.stop import StopRegistry
from capper.db import create_engine, create_session_factory
from capper.demo.api import STATIC
from capper.demo.api import router as demo_router
from capper.errors import register_error_handlers
from capper.health.api import router as health_router
from capper.health.service import HealthService
from capper.memory.service import MemoryService
from capper.telemetry import configure_logging, create_tracer_provider
from capper.time import Clock, utc_now

logger = logging.getLogger(__name__)


def app_version(settings: Settings) -> str:
    """The package version, plus the git commit when known."""
    base = version("capper")
    return f"{base}+{settings.git_sha[:12]}" if settings.git_sha else base


def _read_key(path: str) -> str:
    key = Path(path)
    if not key.exists():
        raise RuntimeError(f"missing key file {path}: the init service creates it (README)")
    return key.read_text()


def create_app(
    settings: Settings | None = None,
    *,
    chat_model: Model | None = None,
    compaction_model: Model | None = None,
    tracer_provider: TracerProvider | None = None,
    clock: Clock = utc_now,
) -> FastAPI:
    settings = settings or Settings()  # pyright: ignore[reportCallIssue]
    current_version = app_version(settings)
    tracer_provider = tracer_provider or create_tracer_provider(
        settings.otlp_endpoint, app_version=current_version
    )
    engine = create_engine(settings.database_url)
    sessions = create_session_factory(engine)

    accounts = AccountService(sessions)
    catalog = CatalogService(sessions, clock)
    memory = MemoryService(
        sessions,
        clock,
        max_notes=settings.guidance_max_notes,
        max_chars=settings.guidance_max_chars,
        max_avoided=settings.avoid_list_max,
    )
    conversations = ConversationService(
        sessions,
        clock,
        max_message_chars=settings.max_message_chars,
        model_name=settings.chat_model,
        app_version=current_version,
        prompt_payload=user_prompt_payload,
    )
    chat = chat_model or build_model(settings.chat_model, settings)
    summarizer = compaction_model or build_model(settings.compaction_model, settings)
    capper = build_agent(
        settings, chat_model=chat, compaction_model=summarizer, tracer_provider=tracer_provider
    )
    stops = StopRegistry()
    runner = TurnRunner(
        capper=capper,
        conversations=conversations,
        accounts=accounts,
        memory=memory,
        tool_services=ToolServices(
            catalog=catalog,
            memory=memory,
            accounts=accounts,
            history=HistorySearchService(sessions),
            audit=ToolAuditLog(sessions, clock),
        ),
        stops=stops,
        tracer=tracer_provider.get_tracer("capper"),
        clock=clock,
        config=RunnerConfig(
            cache_key_secret=settings.cache_key_secret.get_secret_value(),
            default_timezone=settings.default_timezone,
            turn_timeout_seconds=settings.turn_timeout_seconds,
            max_tool_calls_per_turn=settings.max_tool_calls_per_turn,
            tool_result_max_chars=settings.tool_result_max_chars,
            compaction_model=settings.compaction_model,
            model_prices=settings.model_prices,
        ),
    )
    services = Services(
        accounts=accounts,
        conversations=conversations,
        runner=runner,
        stops=stops,
        verifier=TokenVerifier(
            _read_key(settings.jwt_public_key_path),
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            accounts=accounts,
        ),
        demo_sessions=DemoSessionIssuer(
            _read_key(settings.jwt_private_key_path),
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            lifetime=timedelta(minutes=settings.demo_session_minutes),
            clock=clock,
            accounts=accounts,
        ),
        health=HealthService(sessions),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        configure_logging()
        recovered = await conversations.recover_stale_turns()
        if recovered:
            logger.info("marked %d interrupted turn(s) as error", recovered)
        try:
            yield
        finally:
            await runner.shutdown()
            await engine.dispose()
            tracer_provider.shutdown()

    app = FastAPI(title="Capper", version=current_version, lifespan=lifespan)
    app.state.services = services
    register_error_handlers(app)
    app.include_router(conversation_router)
    app.include_router(demo_router)
    app.include_router(health_router)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")
    app.mount(URL_PREFIX, StaticFiles(directory=PRODUCT_IMAGES), name="product-images")
    return app
