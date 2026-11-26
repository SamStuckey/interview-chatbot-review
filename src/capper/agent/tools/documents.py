"""`read_document`: an on-demand policy from the turn's content snapshot.

The name is a plain string, so the tool definition never changes with
content; it's checked against this turn's snapshot when the tool runs.
"""

from pydantic_ai import RunContext

from capper.agent.deps import CapperDeps
from capper.errors import InvalidRequest


async def read_document(ctx: RunContext[CapperDeps], name: str) -> str:
    """Read one of your on-demand policy documents by name, and follow it in your answer.

    Your core instructions list the names you can read.

    Args:
        name: The document's name, for example one listed in your do-no-harm core.
    """
    on_demand = ctx.deps.snapshot.with_load("on_demand")
    document = next((doc for doc in on_demand if doc.name == name), None)
    if document is None:
        valid = ", ".join(doc.name for doc in on_demand)
        raise InvalidRequest(f"no on-demand document named {name!r}; valid names: {valid}")
    return document.body
