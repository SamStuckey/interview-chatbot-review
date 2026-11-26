"""Content publishing and versioning."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from capper.db import create_engine, create_session_factory
from content_bundle import DocumentSource, publish, read_active
from content_bundle.store import ContentDocument
from tests.support import database_url


@pytest.fixture
async def session(db_path: Path) -> AsyncIterator[AsyncSession]:
    engine = create_engine(database_url(db_path))
    async with create_session_factory(engine)() as session:
        yield session
    await engine.dispose()


async def current_sources(session: AsyncSession) -> list[DocumentSource]:
    active = await read_active(session)
    return [
        DocumentSource(d.name, d.content_class, d.load, d.body)  # pyright: ignore[reportArgumentType]
        for d in active.documents
    ]


async def test_republishing_unchanged_content_changes_nothing(session: AsyncSession) -> None:
    before = await read_active(session)
    result = await publish(session, await current_sources(session))
    assert result.published == () and result.version == before.version


async def test_a_body_change_flips_active_and_never_edits_old_text(session: AsyncSession) -> None:
    sources = await current_sources(session)
    old = next(s for s in sources if s.name == "policy_crisis")
    changed = [
        DocumentSource(s.name, s.content_class, s.load, "New crisis text.\n")
        if s.name == "policy_crisis"
        else s
        for s in sources
    ]
    before = await read_active(session)
    result = await publish(session, changed)
    assert result.published == ("policy_crisis",) and result.version != before.version
    rows = (
        await session.scalars(
            select(ContentDocument).where(ContentDocument.name == "policy_crisis")
        )
    ).all()
    assert sorted((r.active, r.body) for r in rows) == [
        (False, old.body),
        (True, "New crisis text.\n"),
    ]


async def test_a_load_or_class_change_alone_is_a_new_version(session: AsyncSession) -> None:
    sources = await current_sources(session)
    before = await read_active(session)
    moved = [
        DocumentSource(s.name, s.content_class, "always", s.body)
        if s.name == "policy_crisis"
        else s
        for s in sources
    ]
    result = await publish(session, moved)
    assert result.published == ("policy_crisis",) and result.version != before.version
    reclassed = [
        DocumentSource(s.name, "user_knowledge", s.load, s.body) if s.name == "policy_crisis" else s
        for s in moved
    ]
    again = await publish(session, reclassed)
    assert again.version != result.version


async def test_a_document_dropped_from_the_set_is_deactivated(session: AsyncSession) -> None:
    sources = [s for s in await current_sources(session) if s.name != "policy_crisis"]
    result = await publish(session, sources)
    assert result.deactivated == ("policy_crisis",)
    assert (await read_active(session)).get("policy_crisis") is None


async def test_bad_sets_are_refused(session: AsyncSession) -> None:
    doc = DocumentSource("x", "operator_policy", "always", "x")
    with pytest.raises(ValueError):
        await publish(session, [doc, doc])
    with pytest.raises(ValueError):
        await publish(session, [DocumentSource("y", "operator_policy", "sometimes", "y")])  # pyright: ignore[reportArgumentType]
