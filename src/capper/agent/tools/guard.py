"""The shared adapter around every tool call.

For each call it claims one unit of the turn's tool budget (calls past the
limit, even inside one parallel batch, aren't run), writes the audit row with
free-text arguments redacted, turns domain errors into error results for the
model, and refuses a result over the size cap instead of cutting it. A call
that never returns (stopped, timed out, or failed unexpectedly) is audited as
an error before the exception continues.
"""

import json
import time
from dataclasses import dataclass
from typing import Any

from pydantic_ai import RunContext
from pydantic_ai.capabilities import AbstractCapability, WrapToolExecuteHandler
from pydantic_ai.messages import ToolCallPart
from pydantic_ai.tools import ToolDefinition
from pydantic_core import to_jsonable_python

from capper.agent.deps import CapperDeps
from capper.errors import DomainError

LIMIT_REACHED = {"error": "tool-call limit reached; answer with what you have"}
REDACTED_ARGUMENTS = frozenset({"text", "query", "product_name"})


def redact(arguments: dict[str, Any]) -> dict[str, Any]:
    """Free text the user may have written is replaced by its length."""
    return {
        key: f"[redacted {len(str(value))} chars]"
        if key in REDACTED_ARGUMENTS and value is not None
        else value
        for key, value in arguments.items()
    }


def elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def too_large(result: Any, max_chars: int) -> bool:
    return len(json.dumps(to_jsonable_python(result), ensure_ascii=False)) > max_chars


def result_too_large(max_chars: int) -> dict[str, str]:
    return {
        "error": f"result too large (over {max_chars} characters); narrow the request, "
        "for example with a smaller limit or a more specific query"
    }


@dataclass
class ToolGuard(AbstractCapability[CapperDeps]):
    async def wrap_tool_execute(
        self,
        ctx: RunContext[CapperDeps],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
        handler: WrapToolExecuteHandler,
    ) -> Any:
        deps = ctx.deps
        if not deps.tool_budget.take():
            await self._audit(deps, call.tool_name, args, "error", 0)
            return LIMIT_REACHED
        started = time.perf_counter()
        status = "ok"
        try:
            result = await handler(args)
        except DomainError as error:
            status, result = "error", {"error": error.message}
        except BaseException:
            await self._audit(deps, call.tool_name, args, "error", elapsed_ms(started))
            raise
        if status == "ok" and too_large(result, deps.tool_result_max_chars):
            status, result = "error", result_too_large(deps.tool_result_max_chars)
        await self._audit(deps, call.tool_name, args, status, elapsed_ms(started))
        return result

    async def _audit(
        self, deps: CapperDeps, tool_name: str, args: dict[str, Any], status: str, latency_ms: int
    ) -> None:
        await deps.services.audit.record(
            user_id=deps.user_id,
            turn_id=deps.turn_id,
            tool_name=tool_name,
            arguments=redact(to_jsonable_python(args)),
            status=status,
            latency_ms=latency_ms,
        )
