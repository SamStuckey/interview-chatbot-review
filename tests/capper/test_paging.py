"""A cursor carries its list's sort key; malformed cursors produce an explicit error."""

import base64
import json
from datetime import UTC, datetime

import pytest

from capper.errors import InvalidRequest
from capper.paging import decode_cursor, encode_cursor, next_page


def raw_cursor(key: list[object]) -> str:
    return base64.urlsafe_b64encode(json.dumps(key).encode()).decode().rstrip("=")


def test_a_cursor_round_trips_its_key() -> None:
    ends = datetime(2026, 11, 18, 12, tzinfo=UTC)
    assert decode_cursor(encode_cursor([ends, 7]), (datetime, int)) == [ends, 7]
    assert decode_cursor(None, (str, int)) is None


@pytest.mark.parametrize(
    ("key", "fields"),
    [
        ([1, "x"], (str, int)),
        (["Apples", True], (str, int)),
        (["not a date", 1], (datetime, int)),
        # `fromisoformat` accepts this, but the database type refuses a date without a timezone.
        (["2026-01-01T00:00:00", 1], (datetime, int)),
        (["Apples"], (str, int)),
    ],
)
def test_a_cursor_with_bad_fields_is_an_explicit_error(
    key: list[object], fields: tuple[type, ...]
) -> None:
    with pytest.raises(InvalidRequest, match="cursor is not valid"):
        decode_cursor(raw_cursor(key), fields)


def test_next_page_cuts_the_extra_row_into_a_cursor() -> None:
    assert next_page([1, 2], 2, lambda n: (n,)) == ([1, 2], None)
    rows, cursor = next_page([1, 2, 3], 2, lambda n: (n,))
    assert rows == [1, 2] and decode_cursor(cursor, (int,)) == [2]
