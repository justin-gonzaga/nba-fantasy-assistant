from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from dikit.errors import NaiveDatetimeError
from dikit.time import calendar

NY = ZoneInfo("America/New_York")


def test_local_date_crosses_midnight_by_time_zone() -> None:
    ts = datetime(2026, 1, 10, 3, 0, tzinfo=UTC)  # 22:00 the previous evening in New York
    assert calendar.local_date(ts, NY) == date(2026, 1, 9)
    with pytest.raises(NaiveDatetimeError):
        calendar.local_date(datetime(2026, 1, 10, 3, 0), NY)  # noqa: DTZ001


@pytest.mark.parametrize(("d", "hours"), [(date(2026, 3, 8), 23), (date(2026, 11, 1), 25)])
def test_day_bounds_handle_dst(d: date, hours: int) -> None:
    start, end = calendar.day_bounds_utc(d, NY)
    assert end - start == timedelta(hours=hours)
