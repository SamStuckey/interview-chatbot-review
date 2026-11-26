"""Time: the injected clock, and users' local calendar days.

Timestamps are stored in UTC. A user's time zone only decides how local dates
and times are shown and how a calendar day maps onto UTC.
"""

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logger = logging.getLogger(__name__)

type Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(UTC)


def valid_zone(name: str) -> bool:
    try:
        ZoneInfo(name)
    except ZoneInfoNotFoundError, ValueError:
        return False
    return True


def user_zone(name: str | None, default: str) -> ZoneInfo:
    """The user's IANA time zone, or the configured default when it's unset or unknown."""
    if name and valid_zone(name):
        return ZoneInfo(name)
    if name:
        logger.warning("unknown time zone %r on a user; using the default", name)
    return ZoneInfo(default)


def local_days_in_utc(first: date, last: date, zone: ZoneInfo) -> tuple[datetime, datetime]:
    """The UTC span `[start, end)` covering local days `first` through `last` in `zone`.

    Midnight is resolved in `zone` itself, so a day that gains or loses an hour
    (daylight saving) is 25 or 23 hours long.
    """
    start = datetime.combine(first, time.min, tzinfo=zone)
    end = datetime.combine(last + timedelta(days=1), time.min, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)
