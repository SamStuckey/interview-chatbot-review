"""The Capper agent: model, settings, tools and capabilities.

Builds provider clients from configuration. Tests can inject a `Model`
instead of using the configured provider.
"""

import hashlib
import hmac
from dataclasses import dataclass

from openai import AsyncOpenAI, Timeout
from opentelemetry.trace import TracerProvider
from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.capabilities import Instrumentation
from pydantic_ai.models import Model
from pydantic_ai.models.instrumented import InstrumentationSettings
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai_harness.compaction import ReportContextUsage

from capper.agent.deps import CapperDeps
from capper.agent.tools import display, documents, lookup, memory
from capper.agent.tools.guard import ToolGuard
from capper.config import Settings
from capper.context.builder import build_instructions
from capper.context.compaction import CompactionLimits, build_clearing, build_compaction

# The SDK retries a request (connection errors, 429, 5xx) before it starts; a streamed
# response is never retried, and the agent turn is never replayed.
SDK_MAX_RETRIES = 2
# Requests past the tool-call limit: the answer after the last tool round, plus room for
# the summarizer, whose requests count against the same limit.
REQUEST_LIMIT_HEADROOM = 4

TOOLS: tuple[Tool[CapperDeps], ...] = (
    Tool(lookup.search_products, strict=True),
    Tool(lookup.get_promotions, strict=True),
    Tool(lookup.get_my_referral_code, strict=True),
    Tool(lookup.get_my_purchases, strict=True),
    Tool(lookup.get_popular_products, strict=True),
    Tool(lookup.search_my_history, strict=True),
    Tool(documents.read_document, strict=True),
    Tool(display.show_products, strict=True),
    Tool(display.show_promotions, strict=True),
    Tool(memory.avoid_product, strict=True),
    Tool(memory.unavoid_product, strict=True),
    Tool(memory.get_my_avoid_list, strict=True),
    Tool(memory.add_guidance, strict=True),
    Tool(memory.update_guidance, strict=True),
    Tool(memory.remove_guidance, strict=True),
)


def build_model(name: str, settings: Settings) -> Model:
    """A configured provider model. Only OpenAI is wired in the MVP."""
    provider, _, model_name = name.partition(":")
    if provider != "openai" or not model_name:
        raise ValueError(f"unsupported model {name!r}: expected 'openai:<model>'")
    client = AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=Timeout(
            settings.turn_timeout_seconds, connect=settings.model_connect_timeout_seconds
        ),
        max_retries=SDK_MAX_RETRIES,
    )
    return openai_model(model_name, client)


def openai_model(model_name: str, client: AsyncOpenAI) -> Model:
    """Every request from this model opts out of storage, the summarizer's included.

    The Harness summarizer runs its own agent without our settings, so this is set on the
    model, which every agent using it inherits.
    """
    return OpenAIResponsesModel(
        model_name,
        provider=OpenAIProvider(openai_client=client),
        settings=OpenAIResponsesModelSettings(openai_store=False),
    )


def base_model_settings(settings: Settings) -> OpenAIResponsesModelSettings:
    """The settings every turn shares. The cache key is added per user at run time."""
    return OpenAIResponsesModelSettings(
        openai_reasoning_context="current_turn",
        openai_send_reasoning_ids=False,
        openai_truncation="disabled",
        cache=True,
        max_tokens=settings.max_output_tokens,
    )


def opaque_user_key(secret: str, user_id: int) -> str:
    """HMAC-SHA256 of the user ID: the prompt cache key and the run's conversation ID."""
    return hmac.new(secret.encode(), str(user_id).encode(), hashlib.sha256).hexdigest()


def run_model_settings(opaque_key: str) -> OpenAIResponsesModelSettings:
    """Per-user settings: the prompt cache key is the opaque user key."""
    return OpenAIResponsesModelSettings(openai_prompt_cache_key=opaque_key)


def compaction_limits(settings: Settings) -> CompactionLimits:
    return CompactionLimits(
        trigger_tokens=settings.compaction_trigger_tokens,
        keep_tokens=settings.compaction_keep_tokens,
        keep_pairs=settings.max_tool_calls_per_turn + settings.tool_results_kept,
        min_clear_tokens=settings.min_clear_tokens,
    )


def instrumentation(tracer_provider: TracerProvider | None) -> Instrumentation:
    """Tracing with message content off."""
    return Instrumentation(
        settings=InstrumentationSettings(
            tracer_provider=tracer_provider,
            include_content=False,
            include_binary_content=False,
        )
    )


def instructions(ctx: RunContext[CapperDeps]) -> str:
    return build_instructions(ctx.deps.snapshot)


@dataclass(frozen=True)
class CapperAgent:
    agent: Agent[CapperDeps, str]
    model_name: str
    request_limit: int


def build_agent(
    settings: Settings,
    *,
    chat_model: Model,
    compaction_model: Model,
    tracer_provider: TracerProvider | None,
) -> CapperAgent:
    """Capabilities in order: instrumentation, tool guard, clearing, compaction, usage.

    The request-only context capability is added per run, last.
    """
    limits = compaction_limits(settings)
    agent = Agent[CapperDeps, str](
        chat_model,
        deps_type=CapperDeps,
        output_type=str,
        name="capper",
        instructions=instructions,
        model_settings=base_model_settings(settings),
        retries={"output": settings.output_retries},
        tools=TOOLS,
        capabilities=[
            instrumentation(tracer_provider),
            ToolGuard(),
            build_clearing(limits),
            build_compaction(limits, compaction_model),
            # Measured against the history budget, so the reading is the budget used.
            ReportContextUsage(context_window=settings.history_budget_tokens),
        ],
    )
    return CapperAgent(
        agent=agent,
        model_name=settings.chat_model,
        request_limit=settings.max_tool_calls_per_turn + REQUEST_LIMIT_HEADROOM,
    )
