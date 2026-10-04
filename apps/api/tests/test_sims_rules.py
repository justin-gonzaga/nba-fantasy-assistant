"""SIM-005 AC2: retention rules, pure (the store applies the plan atomically)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from fantasy_api.users.sims import (
    FULL_RUNS,
    LEAGUES,
    PINS,
    SUMMARIES,
    Sim,
    SimRuleError,
    plan_pin,
    plan_save,
    prune,
)

T0 = datetime(2026, 10, 4, tzinfo=UTC)


def run(i: int, *, pinned: bool = False, kind: str = "practice") -> Sim:
    at = T0 + timedelta(minutes=i)
    return Sim(
        id=f"r{i}",
        kind=kind,  # type: ignore[arg-type]
        season="2026-27",
        title="All categories",
        summary={"score": i},
        detail={"sales": [i]},
        pinned=pinned,
        created_at=at,
        updated_at=at,
    )


def apply(sims: list[Sim], plan_upserts: tuple[Sim, ...], deletes: tuple[str, ...]) -> list[Sim]:
    by_id = {s.id: s for s in sims}
    for s in plan_upserts:
        by_id[s.id] = s
    for d in deletes:
        by_id.pop(d, None)
    return list(by_id.values())


def test_retention_full_runs_then_summaries() -> None:
    sims = [run(i) for i in range(FULL_RUNS)]
    plan, _ = plan_save(sims, run(FULL_RUNS))
    after = apply(sims, plan.upserts, plan.deletes)
    trimmed = [s.id for s in after if s.detail is None]
    assert trimmed == ["r0"]  # the oldest of 31 keeps only its summary
    assert len(after) == FULL_RUNS + 1


def test_retention_summaries_are_capped() -> None:
    sims = [run(i) for i in range(SUMMARIES)]
    plan, _ = plan_save(sims, run(SUMMARIES))
    assert plan.deletes == ("r0",)


def test_retention_pins_are_never_pruned() -> None:
    sims = [run(0, pinned=True), *[run(i) for i in range(1, SUMMARIES + 1)]]
    plan, _ = plan_save(sims, run(SUMMARIES + 1))
    after = apply(sims, plan.upserts, plan.deletes)
    r0 = next(s for s in after if s.id == "r0")
    assert r0.detail is not None  # pinned: kept in full, never deleted
    assert "r1" in plan.deletes


def test_retention_pin_limit() -> None:
    sims = [run(i, pinned=i < PINS) for i in range(PINS + 1)]
    with pytest.raises(SimRuleError) as e:
        plan_pin(sims, f"r{PINS}", True, T0)
    assert e.value.kind == "too-many-pins"
    _, updated = plan_pin(sims, "r0", False, T0)  # unpinning is always fine
    assert updated is not None
    assert not updated.pinned


def test_retention_league_limit() -> None:
    leagues = [run(i, kind="league") for i in range(LEAGUES)]
    with pytest.raises(SimRuleError) as e:
        plan_save(leagues, run(99, kind="league"))
    assert e.value.kind == "too-many-leagues"
    plan, _ = plan_save(leagues, run(100))  # practice runs aren't limited by leagues
    assert plan.upserts[0].id == "r100"


def test_saving_the_same_id_again_is_idempotent() -> None:
    sims = [run(1)]
    plan, stored = plan_save(sims, run(1))
    assert plan.upserts == ()
    assert stored == sims[0]


def test_prune_of_nothing_is_nothing() -> None:
    assert prune([]).upserts == ()
