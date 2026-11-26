"""History search: user-scoped and bounded, by words, local days, or both."""

from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import aiosqlite
import pytest

from capper.conversation.history_search import HistorySearchService, fts_query
from capper.db import create_engine, create_session_factory
from capper.errors import InvalidRequest
from tests.support import (
    ESTABLISHED_USER,
    PARALLEL_USER,
    Keys,
    ScriptedModel,
    Step,
    SteppingClock,
    database_url,
    running_app,
)

PACIFIC = ZoneInfo("America/Los_Angeles")
UTC_ZONE = ZoneInfo("UTC")
TUESDAY = date(2026, 11, 17)


@pytest.fixture
async def search(db_path: Path) -> AsyncIterator[HistorySearchService]:
    engine = create_engine(database_url(db_path))
    yield HistorySearchService(create_session_factory(engine))
    await engine.dispose()


def test_queries_are_quoted_term_by_term() -> None:
    assert fts_query('pasta OR "NEAR" -x') == '"pasta" OR "OR" OR """NEAR""" OR "-x"'
    assert fts_query('  ""  ') is None


async def test_search_is_scoped_bounded_and_ranked(
    db_path: Path, keys: Keys, search: HistorySearchService
) -> None:
    chat = ScriptedModel([Step(f"Reply about tortillas number {i}.") for i in range(7)])
    async with running_app(db_path, keys, chat) as h:
        for i in range(6):
            await h.send(ESTABLISHED_USER, f"Tell me about tortillas {i}")
        await h.send(PARALLEL_USER, "I also love tortillas")
    mine = await search.search(
        ESTABLISHED_USER, query="tortillas", first_day=None, last_day=None, zone=UTC_ZONE, limit=5
    )
    theirs = await search.search(
        PARALLEL_USER, query="tortillas", first_day=None, last_day=None, zone=UTC_ZONE, limit=5
    )
    nothing = await search.search(
        ESTABLISHED_USER, query="spaceship", first_day=None, last_day=None, zone=UTC_ZONE, limit=5
    )
    assert len(mine) == 5
    assert all("tortillas" in match.snippet.lower() for match in mine)
    assert {m.role for m in theirs} == {"user", "assistant"}  # only their own two messages
    assert len(theirs) == 2
    assert nothing == []
    assert mine[0].created_at.tzinfo == UTC


async def test_dates_are_the_users_local_days(
    db_path: Path, keys: Keys, search: HistorySearchService
) -> None:
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE Users SET time_zone = 'America/Los_Angeles' WHERE id = ?", (ESTABLISHED_USER,)
        )
        await db.commit()
    clock = SteppingClock()
    sends = [
        (ESTABLISHED_USER, datetime(2026, 11, 16, 23, 58, tzinfo=PACIFIC), "Monday tortillas"),
        (ESTABLISHED_USER, datetime(2026, 11, 17, 0, 0, tzinfo=PACIFIC), "Tuesday tortillas"),
        (ESTABLISHED_USER, datetime(2026, 11, 17, 23, 58, tzinfo=PACIFIC), "Tuesday snacks"),
        (PARALLEL_USER, datetime(2026, 11, 17, 12, 0, tzinfo=PACIFIC), "Someone else's Tuesday"),
        (ESTABLISHED_USER, datetime(2026, 11, 18, 0, 0, tzinfo=PACIFIC), "Wednesday tortillas"),
    ]
    chat = ScriptedModel([Step("Noted.") for _ in sends])
    async with running_app(db_path, keys, chat, clock=clock) as h:
        for user, when, text in sends:
            clock.now = when.astimezone(UTC)
            await h.send(user, text)

    tuesday = await search.search(
        ESTABLISHED_USER, query=None, first_day=TUESDAY, last_day=TUESDAY, zone=PACIFIC, limit=5
    )
    assert [m.snippet.strip() for m in tuesday] == [
        "Tuesday tortillas",
        "Noted.",
        "Tuesday snacks",
        "Noted.",
    ]
    both = await search.search(
        ESTABLISHED_USER,
        query="tortillas",
        first_day=TUESDAY,
        last_day=TUESDAY,
        zone=PACIFIC,
        limit=5,
    )
    assert [m.snippet.strip() for m in both] == ["Tuesday tortillas"]
    words = await search.search(
        ESTABLISHED_USER, query="tortillas", first_day=None, last_day=None, zone=PACIFIC, limit=5
    )
    assert len(words) == 3
    week = await search.search(
        ESTABLISHED_USER,
        query=None,
        first_day=date(2026, 11, 16),
        last_day=date(2026, 11, 18),
        zone=PACIFIC,
        limit=5,
    )
    assert [m.snippet.strip() for m in week][:2] == ["Monday tortillas", "Noted."]
    assert len(week) == 5


@pytest.mark.parametrize(
    ("query", "first", "last"),
    [
        (None, TUESDAY, None),
        (None, None, TUESDAY),
        (None, TUESDAY, TUESDAY - timedelta(days=1)),
        (None, None, None),
        ("  ", None, None),
    ],
)
async def test_incomplete_or_reversed_ranges_are_refused(
    search: HistorySearchService, query: str | None, first: date | None, last: date | None
) -> None:
    with pytest.raises(InvalidRequest):
        await search.search(
            ESTABLISHED_USER, query=query, first_day=first, last_day=last, zone=UTC_ZONE, limit=5
        )
