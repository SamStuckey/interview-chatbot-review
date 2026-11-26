"""Catalog queries. Avoided products are filtered inside each query, and every list
orders by a key ending in a unique ID so keyset paging is stable."""

from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, and_, func, literal, or_, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from capper.accounts.models import User
from capper.catalog.models import Product, Promotion, Purchase
from capper.db import UtcDateTime
from capper.memory.models import AvoidedProduct
from capper.memory.repository import avoided_ids_query


async def search_products(
    session: AsyncSession, user_id: int, query: str | None, limit: int, after: list[Any] | None
) -> tuple[list[Product], int]:
    """Case-insensitive match on name and description, by name then ID."""
    conditions: list[ColumnElement[bool]] = [Product.id.not_in(avoided_ids_query(user_id))]
    if query and query.strip():
        term = query.strip().lower()
        conditions.append(
            or_(
                func.lower(Product.name).contains(term, autoescape=True),
                func.lower(Product.description).contains(term, autoescape=True),
            )
        )
    total = await session.scalar(select(func.count()).select_from(Product).where(*conditions)) or 0
    statement = select(Product).where(*conditions)
    if after is not None:
        statement = statement.where(tuple_(Product.name, Product.id) > tuple_(after[0], after[1]))
    rows = await session.scalars(statement.order_by(Product.name, Product.id).limit(limit))
    return list(rows.all()), total


def _active_promotions(user_id: int, now: datetime) -> list[ColumnElement[bool]]:
    return [
        Promotion.starts_at <= now,
        Promotion.ends_at > now,
        Promotion.product_id.not_in(avoided_ids_query(user_id)),
    ]


async def active_promotions(
    session: AsyncSession, user_id: int, now: datetime, limit: int, after: list[Any] | None
) -> tuple[list[Promotion], int]:
    """Promotions running now, by end date then ID, excluding avoided products."""
    conditions = _active_promotions(user_id, now)
    total = (
        await session.scalar(select(func.count()).select_from(Promotion).where(*conditions)) or 0
    )
    statement = select(Promotion).where(*conditions)
    if after is not None:
        statement = statement.where(
            tuple_(Promotion.ends_at, Promotion.id)
            > tuple_(literal(after[0], UtcDateTime()), after[1])
        )
    rows = await session.scalars(statement.order_by(Promotion.ends_at, Promotion.id).limit(limit))
    return list(rows.all()), total


async def purchases(
    session: AsyncSession, user_id: int, limit: int, after: list[Any] | None
) -> tuple[list[tuple[Purchase, str]], int]:
    """The user's purchases, newest first."""
    total = (
        await session.scalar(
            select(func.count()).select_from(Purchase).where(Purchase.user_id == user_id)
        )
        or 0
    )
    statement = (
        select(Purchase, Product.name)
        .join(Product, Product.id == Purchase.product_id)
        .where(Purchase.user_id == user_id)
    )
    if after is not None:
        statement = statement.where(
            tuple_(Purchase.purchased_at, Purchase.id) < tuple_(after[0], after[1])
        )
    rows = await session.execute(
        statement.order_by(Purchase.purchased_at.desc(), Purchase.id.desc()).limit(limit)
    )
    return [(purchase, name) for purchase, name in rows], total


async def popular_products(
    session: AsyncSession, user_id: int, school_id: int | None, limit: int, after: list[Any] | None
) -> tuple[list[tuple[int, str, int]], int]:
    """Aggregate purchase counts among users at the school, or all users.

    Returns `(product_id, name, purchase_count)` only: never other users'
    identities or individual purchases. Avoided products are excluded.
    """
    count = func.count(Purchase.id).label("purchase_count")
    ranked = (
        select(Purchase.product_id.label("product_id"), count)
        .join(User, User.id == Purchase.user_id)
        .where(Purchase.product_id.not_in(avoided_ids_query(user_id)))
        .group_by(Purchase.product_id)
    )
    if school_id is not None:
        ranked = ranked.where(User.school_id == school_id)
    ranked_sub = ranked.subquery()
    total = await session.scalar(select(func.count()).select_from(ranked_sub)) or 0
    statement = select(ranked_sub.c.product_id, Product.name, ranked_sub.c.purchase_count).join(
        Product, Product.id == ranked_sub.c.product_id
    )
    if after is not None:
        statement = statement.where(
            or_(
                ranked_sub.c.purchase_count < after[0],
                and_(ranked_sub.c.purchase_count == after[0], ranked_sub.c.product_id > after[1]),
            )
        )
    rows = await session.execute(
        statement.order_by(ranked_sub.c.purchase_count.desc(), ranked_sub.c.product_id).limit(limit)
    )
    return [(pid, name, n) for pid, name, n in rows], total


async def products_by_ids(session: AsyncSession, ids: list[int]) -> dict[int, Product]:
    rows = await session.scalars(select(Product).where(Product.id.in_(ids)))
    return {product.id: product for product in rows.all()}


async def avoided_among(session: AsyncSession, user_id: int, ids: list[int]) -> set[int]:
    """Which of `ids` the user avoids."""
    found = await session.scalars(
        avoided_ids_query(user_id).where(AvoidedProduct.product_id.in_(ids))
    )
    return set(found.all())


async def promotions_by_ids(session: AsyncSession, ids: list[int]) -> dict[int, Promotion]:
    rows = await session.scalars(select(Promotion).where(Promotion.id.in_(ids)))
    return {promotion.id: promotion for promotion in rows.all()}
