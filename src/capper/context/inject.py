"""Request-only context and the tool-call limit's "answer now" request.

This capability is listed last, after clearing and compaction, so it
edits only the outgoing request: account context goes before the history and
turn context goes immediately before this turn's prompt. Nothing it adds
enters the run's message history, so it's never saved or summarized.
"""

from dataclasses import dataclass, replace

from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelMessage, ModelRequest, UserPromptPart
from pydantic_ai.models import ModelRequestContext

from capper.agent.deps import CapperDeps


def insert_request_context(
    messages: list[ModelMessage],
    *,
    account: ModelRequest,
    turn: ModelRequest,
    prompt: ModelRequest,
) -> list[ModelMessage]:
    """A new list: `account` first, `turn` right before the turn's prompt (pure)."""
    out = list(messages)
    index = next((i for i, m in enumerate(out) if m is prompt), None)
    if index is None:
        index = next((i for i in range(len(out) - 1, -1, -1) if out[i] == prompt), None)
    if index is None:
        # The prompt is always in the kept tail; as a last resort, use the latest user prompt.
        index = next(
            (
                i
                for i in range(len(out) - 1, -1, -1)
                if isinstance(out[i], ModelRequest)
                and any(isinstance(p, UserPromptPart) for p in out[i].parts)
            ),
            len(out),
        )
    out.insert(index, turn)
    out.insert(0, account)
    return out


@dataclass
class RequestContext(AbstractCapability[CapperDeps]):
    """One per run: the turn's prebuilt account and turn context."""

    account: ModelRequest
    turn: ModelRequest
    prompt: ModelRequest

    async def before_model_request(
        self, ctx: RunContext[CapperDeps], request_context: ModelRequestContext
    ) -> ModelRequestContext:
        messages = insert_request_context(
            list(request_context.messages), account=self.account, turn=self.turn, prompt=self.prompt
        )
        settings = request_context.model_settings
        if ctx.deps.tool_budget.exhausted:
            settings = {**(settings or {}), "tool_choice": "none"}
        return replace(request_context, messages=messages, model_settings=settings)
