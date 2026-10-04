from datetime import UTC, datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dikit.errors import DikitError
from dikit.time.clock import AsOf, FrozenClock, SystemClock

aware = st.datetimes(
    min_value=datetime(2000, 1, 1),  # noqa: DTZ001 - hypothesis bounds must be naive
    max_value=datetime(2100, 1, 1),  # noqa: DTZ001
    timezones=st.sampled_from([UTC, timezone(timedelta(hours=11)), timezone(timedelta(hours=-5))]),
)


def test_system_clock_is_aware_utc() -> None:
    now = SystemClock().now()
    assert now.tzinfo is UTC


def test_frozen_clock_returns_fixed_time_and_advances() -> None:
    t0 = datetime(2026, 10, 20, 23, 30, tzinfo=UTC)
    clock = FrozenClock(t0)
    assert clock.now() == t0
    clock.advance(timedelta(minutes=15))
    assert clock.now() == t0 + timedelta(minutes=15)


def test_frozen_clock_rejects_naive() -> None:
    with pytest.raises(DikitError):
        FrozenClock(datetime(2026, 10, 20))  # noqa: DTZ001 - deliberately naive


def test_asof_rejects_naive() -> None:
    with pytest.raises(DikitError):
        AsOf(datetime(2026, 10, 20, 12))  # noqa: DTZ001 - deliberately naive


@given(aware)
def test_asof_normalises_to_utc_same_instant(ts: datetime) -> None:
    a = AsOf(ts)
    assert a.ts.tzinfo is UTC
    assert a.ts == ts


def test_asof_ordering() -> None:
    early = AsOf(datetime(2026, 10, 20, tzinfo=UTC))
    late = AsOf(datetime(2026, 10, 21, tzinfo=UTC))
    assert early < late


def test_asof_now_uses_injected_clock() -> None:
    t0 = datetime(2026, 11, 4, 8, 0, tzinfo=UTC)
    assert AsOf.now(FrozenClock(t0)).ts == t0


def test_asof_comparison_with_other_types_is_unsupported() -> None:
    with pytest.raises(TypeError):
        _ = AsOf(datetime(2026, 1, 1, tzinfo=UTC)) < "2026-01-01"
