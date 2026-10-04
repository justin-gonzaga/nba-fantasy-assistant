from datetime import UTC, date, datetime, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dikit.errors import DikitError
from fantasy_core.gamedate import et_day_bounds_utc, game_date

instants = st.datetimes(
    min_value=datetime(2015, 1, 1),  # noqa: DTZ001 - hypothesis bounds must be naive
    max_value=datetime(2040, 1, 1),  # noqa: DTZ001
    timezones=st.just(UTC),
)


def test_late_west_coast_tip_is_previous_et_date() -> None:
    # 10:30pm ET tip on 4 Nov 2026 (EST, UTC-5) = 03:30 UTC on 5 Nov.
    assert game_date(datetime(2026, 11, 5, 3, 30, tzinfo=UTC)) == date(2026, 11, 4)


def test_sydney_morning_maps_to_previous_et_date() -> None:
    # 11:00 AEDT on 5 Nov = 00:00 UTC 5 Nov = 19:00 EST 4 Nov.
    assert game_date(datetime(2026, 11, 5, 0, 0, tzinfo=UTC)) == date(2026, 11, 4)


def test_game_date_rejects_naive() -> None:
    with pytest.raises(DikitError):
        game_date(datetime(2026, 11, 5))  # noqa: DTZ001 - deliberately naive


@pytest.mark.parametrize(
    ("d", "hours"),
    [(date(2026, 3, 8), 23), (date(2026, 11, 1), 25), (date(2026, 11, 2), 24)],
)
def test_dst_day_lengths(d: date, hours: int) -> None:
    start, end = et_day_bounds_utc(d)
    assert end - start == timedelta(hours=hours)
    assert start.tzinfo is UTC


@given(instants)
def test_bounds_contain_instant(ts: datetime) -> None:
    d = game_date(ts)
    start, end = et_day_bounds_utc(d)
    assert start <= ts < end
    assert (end - start) in {timedelta(hours=h) for h in (23, 24, 25)}
