"""Saved sims per user (SIM-005): practice drafts and season-replay leagues, kept with the account.

Retention (owner delegated, 2026-10-04): the latest 30 practice runs keep their full detail,
older ones shrink to a summary, at most 200 summaries; up to 10 pins, never pruned; up to 5 replay
leagues. Pruning happens in the same write that adds a run (no cron). Pure: the store applies the
plan atomically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Literal

SimKind = Literal["practice", "league"]
FULL_RUNS = 30
SUMMARIES = 200
PINS = 10
LEAGUES = 5
MAX_DETAIL_BYTES = 256 * 1024
MAX_SUMMARY_BYTES = 4 * 1024
SIM_ID = re.compile(r"^[A-Za-z0-9:_.-]{1,80}$")
SEASON = re.compile(r"^\d{4}-\d{2}$")


@dataclass(frozen=True)
class Sim:
    id: str  # the client's id (a practice run's seed + start time), so re-saving is idempotent
    kind: SimKind
    season: str
    title: str
    summary: dict[str, Any]
    detail: dict[str, Any] | None  # None once trimmed to a summary
    pinned: bool
    created_at: datetime
    updated_at: datetime
    version: int = 1


@dataclass(frozen=True)
class Plan:
    """What to write and delete for one user, decided from their current sims."""

    upserts: tuple[Sim, ...] = ()
    deletes: tuple[str, ...] = ()


class SimRuleError(Exception):
    """A retention limit; `kind` is the problem type (409)."""

    def __init__(self, kind: str, message: str) -> None:
        super().__init__(message)
        self.kind = kind


def prune(sims: list[Sim]) -> Plan:
    """Trim practice runs past the latest 30 to a summary, delete past 200; pins are untouched."""
    runs = sorted(
        (s for s in sims if s.kind == "practice" and not s.pinned),
        key=lambda s: (s.created_at, s.id),
        reverse=True,
    )
    old = runs[FULL_RUNS:SUMMARIES]
    trims = tuple(replace(s, detail=None) for s in old if s.detail is not None)
    return Plan(upserts=trims, deletes=tuple(s.id for s in runs[SUMMARIES:]))


def plan_save(sims: list[Sim], new: Sim) -> tuple[Plan, Sim]:
    """Saving a sim: idempotent for an existing id (the stored copy wins), a 6th league is refused,
    and practice runs are pruned in the same write."""
    existing = next((s for s in sims if s.id == new.id), None)
    if existing is not None:
        return Plan(), existing
    if new.kind == "league" and sum(s.kind == "league" for s in sims) >= LEAGUES:
        raise SimRuleError(
            "too-many-leagues", f"You can keep {LEAGUES} replay leagues: delete one first."
        )
    after = prune([*sims, new])
    return Plan(upserts=(new, *after.upserts), deletes=after.deletes), new


def plan_pin(sims: list[Sim], sim_id: str, pinned: bool, now: datetime) -> tuple[Plan, Sim | None]:
    target = next((s for s in sims if s.id == sim_id), None)
    if target is None:
        return Plan(), None
    if pinned and not target.pinned and sum(s.pinned for s in sims) >= PINS:
        raise SimRuleError("too-many-pins", f"You can pin {PINS} runs: unpin one first.")
    updated = replace(target, pinned=pinned, updated_at=now, version=target.version + 1)
    after = prune([updated if s.id == sim_id else s for s in sims])  # an unpinned old run may trim
    return Plan(upserts=(updated, *after.upserts), deletes=after.deletes), updated
