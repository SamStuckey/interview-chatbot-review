"""A user's local calendar days map onto UTC across daylight-saving changes."""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from capper.time import local_days_in_utc, user_zone

PACIFIC = ZoneInfo("America/Los_Angeles")


def test_a_local_day_maps_onto_utc_through_daylight_saving() -> None:
    # Clocks go back on 2026-11-01 (a 25-hour day) and forward on 2026-03-08 (23 hours).
    assert local_days_in_utc(date(2026, 11, 1), date(2026, 11, 1), PACIFIC) == (
        datetime(2026, 11, 1, 7, tzinfo=UTC),
        datetime(2026, 11, 2, 8, tzinfo=UTC),
    )
    start, end = local_days_in_utc(date(2026, 3, 8), date(2026, 3, 8), PACIFIC)
    assert (end - start).total_seconds() == 23 * 3600
    start, end = local_days_in_utc(date(2026, 11, 17), date(2026, 11, 18), ZoneInfo("UTC"))
    assert (start, end) == (datetime(2026, 11, 17, tzinfo=UTC), datetime(2026, 11, 19, tzinfo=UTC))


def test_users_without_a_known_zone_get_the_default() -> None:
    assert user_zone("America/Los_Angeles", "UTC") == PACIFIC
    assert user_zone(None, "America/New_York") == ZoneInfo("America/New_York")
    assert user_zone("Not/AZone", "UTC") == ZoneInfo("UTC")
