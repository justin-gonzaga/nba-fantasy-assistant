"""Time as an input: Clock protocol and the AsOf value type (software-engineering standard §4)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import total_ordering
from typing import Protocol

from dikit.errors import NaiveDatetimeError


def _require_aware(ts: datetime, what: str) -> datetime:
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise NaiveDatetimeError(f"{what} must be timezone-aware, got naive {ts!r}")
    return ts.astimezone(UTC)


class Clock(Protocol):
    def now(self) -> datetime:
        """Current time as an aware UTC datetime."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Deterministic clock for tests and replays."""

    def __init__(self, at: datetime) -> None:
        self._now = _require_aware(at, "FrozenClock time")

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        self._now += delta


@total_ordering
@dataclass(frozen=True, init=False)
class AsOf:
    """The instant at which knowledge is evaluated; always aware UTC."""

    ts: datetime

    def __init__(self, ts: datetime) -> None:
        object.__setattr__(self, "ts", _require_aware(ts, "AsOf"))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, AsOf):
            return NotImplemented
        return self.ts < other.ts

    @classmethod
    def now(cls, clock: Clock) -> AsOf:
        return cls(clock.now())
