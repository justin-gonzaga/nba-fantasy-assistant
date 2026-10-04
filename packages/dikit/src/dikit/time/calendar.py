"""Local calendar days of aware instants, and a local day's bounds in UTC (DST-safe)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from dikit.errors import NaiveDatetimeError


def local_date(ts: datetime, tz: ZoneInfo) -> date:
    """Calendar date of an aware instant in time zone `tz`."""
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise NaiveDatetimeError(f"local_date needs an aware datetime, got {ts!r}")
    return ts.astimezone(tz).date()


def day_bounds_utc(d: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    """[start, end) of calendar day `d` in `tz`, in UTC. Handles 23/25-hour DST days."""
    start = datetime.combine(d, time.min, tzinfo=tz)
    end = datetime.combine(d + timedelta(days=1), time.min, tzinfo=tz)
    return start.astimezone(UTC), end.astimezone(UTC)
