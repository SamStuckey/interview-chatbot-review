"""Memory tools: the avoid list and guidance notes.

Each write saves immediately and returns what was saved, so Capper can say so.
"""

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

from pydantic_ai import RunContext

from capper.agent.deps import CapperDeps
from capper.memory.service import SavedNote


def _note(note: SavedNote, zone: ZoneInfo) -> dict[str, Any]:
    expires = note.expires_at.astimezone(zone).date().isoformat() if note.expires_at else None
    return {"note_id": note.note_id, "text": note.text, "expires_at": expires}


def _end_of_day(day: date | None, zone: ZoneInfo) -> datetime | None:
    """The end of the user's local day: a note "until Friday" lasts all of their Friday."""
    return datetime.combine(day, time.max, tzinfo=zone) if day else None


async def avoid_product(ctx: RunContext[CapperDeps], product_name: str) -> dict[str, Any]:
    """Add a product to the user's avoid list, so it's never suggested or shown again.

    The name is matched against the catalog, ignoring case: an exact name wins, otherwise a
    product whose name contains it. If several match, nothing is saved and the error lists
    them: ask the user which one they mean, then call again with its exact name.

    Args:
        product_name: The product's name, or the words the user used for it.
    """
    item = await ctx.deps.services.memory.avoid(ctx.deps.user_id, product_name)
    return {"avoided": {"product_id": item.product_id, "name": item.name}}


async def unavoid_product(
    ctx: RunContext[CapperDeps], product_name: str | None = None, product_id: int | None = None
) -> dict[str, Any]:
    """Remove a product from the user's avoid list, by name or by ID: give exactly one.

    A name is matched against the avoid list the way `avoid_product` matches the catalog. If
    several match, nothing is removed and the error lists them: ask the user which one.

    Args:
        product_name: The product's name, or the words the user used for it.
        product_id: The product's ID, from `get_my_avoid_list`.
    """
    item = await ctx.deps.services.memory.unavoid(
        ctx.deps.user_id, product_name=product_name, product_id=product_id
    )
    return {"removed_from_avoid_list": {"product_id": item.product_id, "name": item.name}}


async def get_my_avoid_list(ctx: RunContext[CapperDeps]) -> dict[str, Any]:
    """List the products on the user's avoid list, oldest first, for when they ask about it.

    Name these products in text: avoided products can't be shown as cards. They're already
    left out of every lookup and card, so you don't need this list to filter results.
    """
    items = await ctx.deps.services.memory.avoided(ctx.deps.user_id)
    return {"items": [{"product_id": i.product_id, "name": i.name} for i in items]}


async def add_guidance(
    ctx: RunContext[CapperDeps], text: str, expires_at: date | None = None
) -> dict[str, Any]:
    """Save a guidance note the user clearly asked you to remember.

    Write one short, consistent statement in the third person (for example "Prefers quick
    weeknight meals."). One note per call. A note that's too long is refused with the limit.

    Args:
        text: The note: one short statement.
        expires_at: Optional last day the note applies (YYYY-MM-DD, the user's local day),
            for temporary guidance.
    """
    zone = ctx.deps.time_zone
    note = await ctx.deps.services.memory.add_note(
        ctx.deps.user_id, text, _end_of_day(expires_at, zone)
    )
    return {"saved": _note(note, zone)}


async def update_guidance(
    ctx: RunContext[CapperDeps], note_id: int, text: str, expires_at: date | None = None
) -> dict[str, Any]:
    """Replace a saved guidance note's text (and optional expiry).

    Args:
        note_id: The note's ID, from the account context.
        text: The new note: one short statement.
        expires_at: Optional last day the note applies (YYYY-MM-DD, the user's local day).
    """
    zone = ctx.deps.time_zone
    note = await ctx.deps.services.memory.update_note(
        ctx.deps.user_id, note_id, text, _end_of_day(expires_at, zone)
    )
    return {"updated": _note(note, zone)}


async def remove_guidance(ctx: RunContext[CapperDeps], note_id: int) -> dict[str, Any]:
    """Delete a saved guidance note.

    Args:
        note_id: The note's ID, from the account context.
    """
    await ctx.deps.services.memory.remove_note(ctx.deps.user_id, note_id)
    return {"removed": note_id}
