"""Database plumbing: the declarative base, a UTC timestamp type, and the async engine.

Sessions use `expire_on_commit=False` and relationships `lazy="raise"`;
transactions stay short.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import CursorResult, Result, String, event
from sqlalchemy.engine import Dialect, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator

type SessionFactory = async_sessionmaker[AsyncSession]


class Base(DeclarativeBase):
    """Base for every table the service owns or reads."""


class UtcDateTime(TypeDecorator[datetime]):
    """A timezone-aware UTC datetime stored as ISO 8601 text.

    SQLite has no timezone-aware type, so values are normalized to UTC and
    stored as text, which also keeps them sortable.
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("naive datetimes are not stored; use an aware UTC datetime")
        return value.astimezone(UTC).isoformat()

    def process_result_value(self, value: Any, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def parse_legacy_timestamp(value: str) -> datetime:
    """Timestamps in the supplied tables are naive ISO text; they are UTC."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def create_engine(database_url: str) -> AsyncEngine:
    """Create the async engine; SQLite enforces foreign keys and waits briefly on locks.

    Bound values stay out of error messages, so a logged error never carries message text.
    """
    url = make_url(database_url)
    engine = create_async_engine(database_url, hide_parameters=True)

    if url.get_backend_name() == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:  # pyright: ignore[reportUnusedFunction]
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()

    return engine


def rowcount(result: Result[Any]) -> int:
    """Rows matched by an UPDATE or DELETE."""
    return result.rowcount if isinstance(result, CursorResult) else 0


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    return async_sessionmaker(engine, expire_on_commit=False)
