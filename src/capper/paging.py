"""The cursor contract for lists: limit, opaque keyset cursor, totals.

A cursor is the sort key of the last item returned, encoded so callers treat
it as opaque. Every list orders by a key that ends in a unique ID, so paging
is stable.
"""

import base64
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from capper.errors import InvalidRequest

DEFAULT_LIMIT = 10
MAX_LIMIT = 50


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total_count: int
    next_cursor: str | None


def clamp_limit(
    limit: int | None, *, default: int = DEFAULT_LIMIT, maximum: int = MAX_LIMIT
) -> int:
    if limit is None:
        return default
    if limit < 1:
        raise InvalidRequest("limit must be at least 1")
    return min(limit, maximum)


def encode_cursor(key: Sequence[object]) -> str:
    """A row's sort key as an opaque string; datetimes travel as ISO 8601 text."""
    values = [value.isoformat() if isinstance(value, datetime) else value for value in key]
    return base64.urlsafe_b64encode(json.dumps(values).encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None, fields: tuple[type, ...]) -> list[Any] | None:
    """The sort key a cursor carries, checked against the list's key types."""
    if cursor is None:
        return None
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        key = json.loads(base64.urlsafe_b64decode(padded.encode()))
        if not isinstance(key, list) or len(key) != len(fields):  # pyright: ignore[reportUnknownArgumentType]
            raise ValueError("wrong shape")
        return [_field(value, kind) for value, kind in zip(key, fields, strict=True)]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    except (TypeError, ValueError, UnicodeDecodeError) as error:
        raise InvalidRequest("cursor is not valid; start again without a cursor") from error


def _field(value: object, kind: type) -> object:
    if kind is datetime and isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:  # `UtcDateTime` refuses these when the query binds them
            raise ValueError("a cursor datetime needs a timezone")
        return parsed
    if type(value) is not kind:  # exact, so True isn't accepted as an int
        raise TypeError(f"expected {kind.__name__}")
    return value


def next_page[R](
    rows: list[R], size: int, key: Callable[[R], Sequence[object]]
) -> tuple[list[R], str | None]:
    """Rows fetched with `size + 1`: the page, and a cursor if more remain."""
    if len(rows) <= size:
        return rows, None
    return rows[:size], encode_cursor(key(rows[size - 1]))
