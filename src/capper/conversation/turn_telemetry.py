"""What a turn records on its root span, beside the framework's own spans.

Counts, IDs, timings and outcomes only: never message text. A failed
run is named by its category (`error.type`), never by the provider's message,
which can echo the request.
"""

from typing import Any

from opentelemetry.trace import Span, Status, StatusCode
from pydantic_ai.exceptions import (
    ModelAPIError,
    ModelContextWindowExceededError,
    ModelHTTPError,
    UsageLimitExceeded,
)
from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart
from pydantic_ai.usage import RunUsage

from capper.context.compaction import CLEARED_PLACEHOLDER
from capper.conversation.service import EndStatus


def estimated_cost(usage: RunUsage, prices: tuple[float, float, float] | None) -> float | None:
    """Tokens priced by the configured estimates, per million tokens."""
    if prices is None:
        return None
    input_price, cached_price, output_price = prices
    uncached = max(usage.input_tokens - usage.cache_read_tokens, 0)
    total = (
        uncached * input_price
        + usage.cache_read_tokens * cached_price
        + usage.output_tokens * output_price
    )
    return round(total / 1_000_000, 6)


def clearing_ran(messages: list[ModelMessage]) -> bool:
    return any(
        isinstance(part, ToolReturnPart) and part.content == CLEARED_PLACEHOLDER
        for message in messages
        if isinstance(message, ModelRequest)
        for part in message.parts
    )


def failure_attributes(error: BaseException) -> dict[str, Any]:
    """Why a run failed, without any of the error's text."""
    if isinstance(error, ModelContextWindowExceededError):
        attributes: dict[str, Any] = {"error.type": "context_limit"}
    elif isinstance(error, ModelAPIError):
        attributes = {"error.type": "model_api_error"}
    elif isinstance(error, UsageLimitExceeded):
        attributes = {"error.type": "usage_limit"}
    else:
        attributes = {"error.type": type(error).__name__}
    if isinstance(error, ModelAPIError) and error.provider_error_code:
        attributes["capper.provider_error_code"] = error.provider_error_code
    if isinstance(error, ModelHTTPError):
        attributes["http.response.status_code"] = error.status_code
    return attributes


def record_loaded_summary(span: Span, summary_id: int | None) -> None:
    """The summary row the turn's history starts from; the row holds its cutoff."""
    if summary_id is not None:
        span.add_event("context.summary_loaded", {"summary_id": summary_id})


def record_compaction(span: Span, *, previous_cutoff: int | None, kept_from: int) -> None:
    """A compaction ran during the turn. Its new cutoff isn't a message row until it's saved,
    so the kept suffix is given as a position in the turn's history (loaded, then new)."""
    attributes: dict[str, Any] = {"kept_from_position": kept_from}
    if previous_cutoff is not None:
        attributes["previous_cutoff_message_id"] = previous_cutoff
    span.add_event("context.compaction", attributes)


def record_unplaced_compaction(span: Span) -> None:
    """A compaction whose result has an unexpected shape, so its summary isn't saved."""
    span.add_event("context.compaction", {"saved": False, "error": "unexpected_shape"})


def record_saved_summary(span: Span, summary_id: int | None) -> None:
    """The new summary row, recorded only once its transaction has committed."""
    if summary_id is not None:
        span.add_event("context.summary_saved", {"summary_id": summary_id})


def record_outcome(
    span: Span,
    *,
    status: EndStatus,
    failure: dict[str, Any],
    usage: RunUsage | None,
    tool_calls: int,
    compacted: bool,
    cleared: bool,
    first_token_ms: int | None,
    prices: tuple[float, float, float] | None,
) -> None:
    attributes: dict[str, Any] = {
        "capper.status": status,
        "capper.tool_calls": tool_calls,
        "capper.compacted": compacted,
        "capper.cleared": cleared,
        **failure,
    }
    if first_token_ms is not None:
        attributes["capper.time_to_first_token_ms"] = first_token_ms
    if usage is not None:
        attributes |= {
            "capper.input_tokens": usage.input_tokens,
            "capper.output_tokens": usage.output_tokens,
            "capper.cached_tokens": usage.cache_read_tokens,
        }
        cost = estimated_cost(usage, prices)
        if cost is not None:
            attributes["capper.estimated_cost_usd"] = cost
    span.set_attributes(attributes)
    if status == "error":
        span.set_status(Status(StatusCode.ERROR))
