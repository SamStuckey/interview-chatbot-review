"""`search_my_history`'s backing query: bounded, user-scoped, text only.

Words, a range of the user's local calendar days, or both. The date range is
converted to UTC and applied in the query with the user filter, before the
limit.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from capper.agent.deps import HistoryMatch
from capper.conversation import repository
from capper.db import SessionFactory
from capper.errors import InvalidRequest
from capper.time import local_days_in_utc


def fts_query(query: str) -> str | None:
    """Each term quoted for FTS5 (so operators and punctuation are literal), any term matching."""
    terms = [term.replace('"', '""') for term in query.split() if term.strip('"')]
    return " OR ".join(f'"{term}"' for term in terms) or None


def search_date_span(
    first_day: date | None, last_day: date | None, zone: ZoneInfo
) -> tuple[datetime, datetime] | None:
    """Validate an optional local date range and convert it to a UTC span."""
    if first_day is None and last_day is None:
        return None
    if first_day is None or last_day is None:
        raise InvalidRequest("give both start_date and end_date (the same date for one day)")
    if first_day > last_day:
        raise InvalidRequest("start_date is after end_date")
    return local_days_in_utc(first_day, last_day, zone)


class HistorySearchService:
    def __init__(self, sessions: SessionFactory) -> None:
        self._sessions = sessions

    async def search(
        self,
        user_id: int,
        *,
        query: str | None,
        first_day: date | None,
        last_day: date | None,
        zone: ZoneInfo,
        limit: int,
    ) -> list[HistoryMatch]:
        """Best matches first for words; oldest first for a date range alone."""
        date_span = search_date_span(first_day, last_day, zone)
        text_match = fts_query(query) if query else None
        if text_match is None and date_span is None:
            raise InvalidRequest("give words to look for, a date range, or both")
        async with self._sessions() as session:
            rows = await repository.search_messages(session, user_id, text_match, date_span, limit)
        return [
            HistoryMatch(
                message_id=message_id,
                created_at=created_at,
                role=role,
                snippet=snippet,
            )
            for message_id, snippet, role, created_at in rows
        ]
