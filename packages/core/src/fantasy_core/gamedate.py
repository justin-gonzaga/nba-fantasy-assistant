"""NBA game dates: the US/Eastern calendar date on which a game tips off."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from dikit.time import calendar

NBA_TZ = ZoneInfo("America/New_York")


def game_date(ts: datetime) -> date:
    """US/Eastern calendar date of an aware instant (e.g. a tip-off time)."""
    return calendar.local_date(ts, NBA_TZ)


def et_day_bounds_utc(d: date) -> tuple[datetime, datetime]:
    """[start, end) of US/Eastern calendar day `d`, in UTC. Handles 23/25-hour DST days."""
    return calendar.day_bounds_utc(d, NBA_TZ)
