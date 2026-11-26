"""Guidance-note and avoid-list queries, always scoped to one user."""

from datetime import datetime

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from capper.catalog.models import Product
from capper.db import rowcount
from capper.memory.models import AvoidedProduct, GuidanceNote


def avoided_ids_query(user_id: int) -> Select[int]:
    """A subquery of the user's avoided product IDs, for filtering inside other queries."""
    return select(AvoidedProduct.product_id).where(AvoidedProduct.user_id == user_id)


async def list_notes(session: AsyncSession, user_id: int, now: datetime) -> list[GuidanceNote]:
    """Unexpired notes, oldest first, so a newer note reads as superseding an older one."""
    rows = await session.scalars(
        select(GuidanceNote)
        .where(
            GuidanceNote.user_id == user_id,
            (GuidanceNote.expires_at.is_(None)) | (GuidanceNote.expires_at > now),
        )
        .order_by(GuidanceNote.created_at, GuidanceNote.id)
    )
    return list(rows.all())


async def count_notes(session: AsyncSession, user_id: int) -> int:
    return (
        await session.scalar(
            select(func.count()).select_from(GuidanceNote).where(GuidanceNote.user_id == user_id)
        )
        or 0
    )


async def get_note(session: AsyncSession, user_id: int, note_id: int) -> GuidanceNote | None:
    return await session.scalar(
        select(GuidanceNote).where(GuidanceNote.id == note_id, GuidanceNote.user_id == user_id)
    )


async def delete_note(session: AsyncSession, user_id: int, note_id: int) -> bool:
    result = await session.execute(
        delete(GuidanceNote).where(GuidanceNote.id == note_id, GuidanceNote.user_id == user_id)
    )
    return rowcount(result) > 0


async def list_avoided(session: AsyncSession, user_id: int) -> list[tuple[int, str]]:
    """The avoid list with product names, oldest first."""
    rows = await session.execute(
        select(AvoidedProduct.product_id, Product.name)
        .join(Product, Product.id == AvoidedProduct.product_id)
        .where(AvoidedProduct.user_id == user_id)
        .order_by(AvoidedProduct.created_at, AvoidedProduct.product_id)
    )
    return [(product_id, name) for product_id, name in rows]


async def products_named(session: AsyncSession, term: str, limit: int) -> list[tuple[int, str]]:
    """Catalog products whose name contains `term` (lowercase), exact names first."""
    name = func.lower(Product.name)
    rows = await session.execute(
        select(Product.id, Product.name)
        .where(name.contains(term, autoescape=True))
        .order_by((name == term).desc(), Product.name, Product.id)
        .limit(limit)
    )
    return [(product_id, product_name) for product_id, product_name in rows]


async def count_avoided(session: AsyncSession, user_id: int) -> int:
    return (
        await session.scalar(
            select(func.count())
            .select_from(AvoidedProduct)
            .where(AvoidedProduct.user_id == user_id)
        )
        or 0
    )


async def delete_avoided(session: AsyncSession, user_id: int, product_id: int) -> bool:
    result = await session.execute(
        delete(AvoidedProduct).where(
            AvoidedProduct.user_id == user_id, AvoidedProduct.product_id == product_id
        )
    )
    return rowcount(result) > 0
