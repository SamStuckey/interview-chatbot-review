"""Display tools: show product and promotion cards.

The model passes IDs only. Each card is built from database records, sent to
the app as a `card` event, and the model learns only how many were shown.
"""

from dataclasses import asdict
from typing import Annotated, Any

from annotated_types import Len
from pydantic import Field
from pydantic_ai import RunContext

from capper.agent.deps import CapperDeps, Card

MAX_CARD_ITEMS = 10
CardIds = Annotated[list[int], Len(min_length=1, max_length=MAX_CARD_ITEMS)]
Heading = Annotated[str, Field(max_length=80)]


async def show_products(
    ctx: RunContext[CapperDeps], product_ids: CardIds, heading: Heading
) -> dict[str, Any]:
    """Show the user product cards: the only way to present products.

    Every ID must come from a lookup tool in this conversation. Unknown products and
    products on the user's avoid list are refused, and no card is shown.

    Args:
        product_ids: 1 to 10 product IDs, in display order.
        heading: A short heading for the cards, such as "Here are some ideas".
    """
    items = await ctx.deps.services.catalog.product_cards(ctx.deps.user_id, product_ids)
    await ctx.deps.emit_card(Card("product", heading, [asdict(item) for item in items]))
    return {"shown": len(items)}


async def show_promotions(
    ctx: RunContext[CapperDeps], promotion_ids: CardIds, heading: Heading
) -> dict[str, Any]:
    """Show the user Bonus Caps promotion cards: the only way to present promotions.

    Every ID must come from `get_promotions`. Inactive promotions and promotions on avoided
    products are refused, and no card is shown.

    Args:
        promotion_ids: 1 to 10 promotion IDs, in display order.
        heading: A short heading for the cards, such as "This week's Bonus Caps".
    """
    items = await ctx.deps.services.catalog.promotion_cards(ctx.deps.user_id, promotion_ids)
    await ctx.deps.emit_card(Card("promotion", heading, [asdict(item) for item in items]))
    return {"shown": len(items)}
