"""Catalog use cases: lists for the model, and card contents built from database records."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from capper.catalog import repository
from capper.catalog.models import Product, Promotion
from capper.db import SessionFactory, parse_legacy_timestamp
from capper.errors import InvalidRequest
from capper.paging import Page, clamp_limit, decode_cursor, next_page
from capper.time import Clock

SHORT_DESCRIPTION_CHARS = 200


@dataclass(frozen=True)
class ProductSummary:
    id: int
    name: str
    description: str
    price: float


@dataclass(frozen=True)
class PromotionSummary:
    id: int
    product_id: int
    title: str
    description: str
    ends_at: datetime


@dataclass(frozen=True)
class PurchaseSummary:
    product_id: int
    product_name: str
    quantity: int
    purchased_at: datetime


@dataclass(frozen=True)
class PopularProduct:
    product_id: int
    name: str
    purchase_count: int


@dataclass(frozen=True)
class PopularPage:
    basis: Literal["school", "overall"]
    page: Page[PopularProduct]


@dataclass(frozen=True)
class ProductCardItem:
    id: int
    name: str
    price: float
    image_url: str | None


@dataclass(frozen=True)
class PromotionCardItem:
    id: int
    product_id: int
    title: str
    description: str
    image_url: str | None


def short_description(text: str | None) -> str:
    if not text:
        return ""
    return (
        text if len(text) <= SHORT_DESCRIPTION_CHARS else text[: SHORT_DESCRIPTION_CHARS - 1] + "…"
    )


def product_card_item(product: Product) -> ProductCardItem:
    """A card item from the database record only, never from model text."""
    return ProductCardItem(product.id, product.name, product.price, product.image_url)


def promotion_card_item(promotion: Promotion, product: Product) -> PromotionCardItem:
    return PromotionCardItem(
        promotion.id,
        promotion.product_id,
        promotion.title,
        promotion.description,
        product.image_url,
    )


class CatalogService:
    def __init__(self, sessions: SessionFactory, clock: Clock) -> None:
        self._sessions = sessions
        self._clock = clock

    async def search(
        self, user_id: int, query: str | None, limit: int | None, cursor: str | None
    ) -> Page[ProductSummary]:
        size = clamp_limit(limit)
        after = decode_cursor(cursor, (str, int))
        async with self._sessions() as session:
            rows, total = await repository.search_products(session, user_id, query, size + 1, after)
        rows, next_cursor = next_page(rows, size, lambda p: (p.name, p.id))
        items = [
            ProductSummary(p.id, p.name, short_description(p.description), p.price) for p in rows
        ]
        return Page(items, total, next_cursor)

    async def promotions(
        self, user_id: int, limit: int | None, cursor: str | None
    ) -> Page[PromotionSummary]:
        size = clamp_limit(limit)
        after = decode_cursor(cursor, (datetime, int))
        async with self._sessions() as session:
            rows, total = await repository.active_promotions(
                session, user_id, self._clock(), size + 1, after
            )
        rows, next_cursor = next_page(rows, size, lambda p: (p.ends_at, p.id))
        items = [
            PromotionSummary(p.id, p.product_id, p.title, p.description, p.ends_at) for p in rows
        ]
        return Page(items, total, next_cursor)

    async def purchases(
        self, user_id: int, limit: int | None, cursor: str | None
    ) -> Page[PurchaseSummary]:
        size = clamp_limit(limit)
        # `purchased_at` is the supplied table's naive text, compared as stored.
        after = decode_cursor(cursor, (str, int))
        async with self._sessions() as session:
            rows, total = await repository.purchases(session, user_id, size + 1, after)
        rows, next_cursor = next_page(rows, size, lambda row: (row[0].purchased_at, row[0].id))
        items = [
            PurchaseSummary(p.product_id, name, p.quantity, parse_legacy_timestamp(p.purchased_at))
            for p, name in rows
        ]
        return Page(items, total, next_cursor)

    async def popular(
        self, user_id: int, school_id: int | None, limit: int | None, cursor: str | None
    ) -> PopularPage:
        size = clamp_limit(limit)
        after = decode_cursor(cursor, (int, int))
        async with self._sessions() as session:
            rows, total = await repository.popular_products(
                session, user_id, school_id, size + 1, after
            )
        rows, next_cursor = next_page(rows, size, lambda row: (row[2], row[0]))
        items = [PopularProduct(pid, name, n) for pid, name, n in rows]
        page = Page(items, total, next_cursor)
        return PopularPage("school" if school_id is not None else "overall", page)

    async def product_cards(self, user_id: int, product_ids: list[int]) -> list[ProductCardItem]:
        """Card items for these products, in order; unknown or avoided IDs are refused."""
        ids = list(dict.fromkeys(product_ids))
        async with self._sessions() as session:
            products = await repository.products_by_ids(session, ids)
            avoided = await repository.avoided_among(session, user_id, ids)
        unknown = [i for i in ids if i not in products]
        refused = sorted(avoided)
        if unknown or refused:
            problems: list[str] = []
            if unknown:
                problems.append(f"unknown product IDs: {unknown}")
            if refused:
                problems.append(f"products on the user's avoid list: {refused}")
            raise InvalidRequest("; ".join(problems) + ". No card was shown.")
        return [product_card_item(products[i]) for i in ids]

    async def promotion_cards(
        self, user_id: int, promotion_ids: list[int]
    ) -> list[PromotionCardItem]:
        """Card items for active promotions on products not avoided; anything else is refused."""
        ids = list(dict.fromkeys(promotion_ids))
        now = self._clock()
        async with self._sessions() as session:
            promotions = await repository.promotions_by_ids(session, ids)
            product_ids = [p.product_id for p in promotions.values()]
            products = await repository.products_by_ids(session, product_ids)
            avoided = await repository.avoided_among(session, user_id, product_ids)
        problems: list[str] = []
        unknown = [i for i in ids if i not in promotions]
        inactive = [i for i, p in promotions.items() if not p.starts_at <= now < p.ends_at]
        on_avoided = [i for i, p in promotions.items() if p.product_id in avoided]
        if unknown:
            problems.append(f"unknown promotion IDs: {unknown}")
        if inactive:
            problems.append(f"promotions not active now: {sorted(inactive)}")
        if on_avoided:
            problems.append(f"promotions on products the user avoids: {sorted(on_avoided)}")
        if problems:
            raise InvalidRequest("; ".join(problems) + ". No card was shown.")
        return [promotion_card_item(promotions[i], products[promotions[i].product_id]) for i in ids]
