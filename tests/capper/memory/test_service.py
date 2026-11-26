"""Guidance and avoid-list caps, user scoping, and validation."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from capper.db import create_engine, create_session_factory
from capper.errors import InvalidRequest, LimitReached, NotFound
from capper.memory.service import MemoryService
from tests.support import ESTABLISHED_USER, GUIDANCE_USER, PARALLEL_USER, database_url


@pytest.fixture
async def memory(db_path: Path) -> AsyncIterator[MemoryService]:
    engine = create_engine(database_url(db_path))
    yield MemoryService(
        create_session_factory(engine),
        lambda: datetime.now(UTC),
        max_notes=3,
        max_chars=40,
        max_avoided=2,
    )
    await engine.dispose()


async def test_notes_are_saved_updated_and_removed(memory: MemoryService) -> None:
    note = await memory.add_note(ESTABLISHED_USER, "  Likes   pasta. ", None)
    assert note.text == "Likes pasta."
    updated = await memory.update_note(ESTABLISHED_USER, note.note_id, "Likes rice.", None)
    assert updated.text == "Likes rice."
    await memory.remove_note(ESTABLISHED_USER, note.note_id)
    notes = await memory.active_notes(ESTABLISHED_USER)
    assert note.note_id not in [n.note_id for n in notes]


async def test_notes_belong_to_their_user(memory: MemoryService) -> None:
    note = await memory.add_note(ESTABLISHED_USER, "Mine.", None)
    with pytest.raises(NotFound):
        await memory.update_note(PARALLEL_USER, note.note_id, "Theirs.", None)
    with pytest.raises(NotFound):
        await memory.remove_note(PARALLEL_USER, note.note_id)


async def test_the_guidance_cap_is_an_explicit_result(memory: MemoryService) -> None:
    # The seed gives ESTABLISHED_USER one note; the cap here is 3.
    await memory.add_note(ESTABLISHED_USER, "One.", None)
    await memory.add_note(ESTABLISHED_USER, "Two.", None)
    with pytest.raises(LimitReached, match="guidance full"):
        await memory.add_note(ESTABLISHED_USER, "Three.", None)


async def test_long_empty_or_past_notes_are_refused(memory: MemoryService) -> None:
    with pytest.raises(InvalidRequest):
        await memory.add_note(ESTABLISHED_USER, "x" * 41, None)
    with pytest.raises(InvalidRequest):
        await memory.add_note(ESTABLISHED_USER, "   ", None)
    with pytest.raises(InvalidRequest):
        await memory.add_note(ESTABLISHED_USER, "Old.", datetime.now(UTC) - timedelta(days=1))


async def test_expired_notes_are_left_out(db_path: Path) -> None:
    engine = create_engine(database_url(db_path))
    now = [datetime.now(UTC)]
    memory = MemoryService(
        create_session_factory(engine), lambda: now[0], max_notes=30, max_chars=300, max_avoided=5
    )
    await memory.add_note(ESTABLISHED_USER, "This week only.", now[0] + timedelta(days=1))
    assert "This week only." in [n.text for n in await memory.active_notes(ESTABLISHED_USER)]
    now[0] += timedelta(days=2)
    assert "This week only." not in [n.text for n in await memory.active_notes(ESTABLISHED_USER)]
    await engine.dispose()


async def test_avoid_list_cap_existence_and_scoping(memory: MemoryService) -> None:
    # GUIDANCE_USER already avoids one product (seed); the cap here is 2.
    added = await memory.avoid(GUIDANCE_USER, "frosted flakes cereal")
    assert added.name == "Frosted Flakes Cereal"
    assert (await memory.avoid(GUIDANCE_USER, "Frosted Flakes")).product_id == 1  # idempotent
    with pytest.raises(LimitReached, match="list full"):
        await memory.avoid(GUIDANCE_USER, "Sour Cream")
    with pytest.raises(NotFound):
        await memory.unavoid(ESTABLISHED_USER, product_name="frosted")
    assert [a.name for a in await memory.avoided(ESTABLISHED_USER)] == []
    await memory.unavoid(GUIDANCE_USER, product_id=1)


async def test_avoiding_by_name_resolves_one_product_or_asks(memory: MemoryService) -> None:
    # "Peanut Butter" is an exact name and wins over "Peanut Butter Crackers".
    assert (await memory.avoid(ESTABLISHED_USER, "  PEANUT   butter ")).name == "Peanut Butter"
    with pytest.raises(InvalidRequest, match=r"Granola Cereal Bars.*ask the user"):
        await memory.avoid(ESTABLISHED_USER, "cereal")
    with pytest.raises(NotFound):
        await memory.avoid(ESTABLISHED_USER, "kale chips")
    assert [a.name for a in await memory.avoided(ESTABLISHED_USER)] == ["Peanut Butter"]


async def test_removal_by_name_matches_the_users_own_list(memory: MemoryService) -> None:
    # Two avoided products share a word, so a name that matches both is refused.
    await memory.avoid(ESTABLISHED_USER, "Peanut Butter Crackers")
    await memory.avoid(ESTABLISHED_USER, "Peanut Butter")
    with pytest.raises(InvalidRequest, match="ask the user"):
        await memory.unavoid(ESTABLISHED_USER, product_name="peanut")
    removed = await memory.unavoid(ESTABLISHED_USER, product_name="crackers")
    assert removed.name == "Peanut Butter Crackers"
    with pytest.raises(InvalidRequest):
        await memory.unavoid(ESTABLISHED_USER, product_name="peanut", product_id=6)
    with pytest.raises(NotFound):
        await memory.unavoid(PARALLEL_USER, product_name="peanut butter")
    assert [a.name for a in await memory.avoided(ESTABLISHED_USER)] == ["Peanut Butter"]
