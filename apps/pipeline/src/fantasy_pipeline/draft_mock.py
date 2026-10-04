"""Mock auction replay on real values (DRAFT-005 AC1/AC4): every pick re-runs the helper, timed."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Any

from fantasy_models import draft_live

FOLLOW_TARGET = 0.7  # share of picks where the simulated room takes the helper's top target
PRICE_NOISE = (0.8, 1.2)


@dataclass(frozen=True)
class MockResult:
    picks: int
    rosters_full: bool
    spent: float
    p50_ms: float
    max_ms: float


def run_mock(
    players: list[dict[str, Any]], teams: list[str], budget: int, slots: int, seed: int = 1
) -> MockResult:
    rng = random.Random(seed)  # noqa: S311 - simulation, not security
    picks: list[dict[str, Any]] = []
    times = []
    for _ in range(len(teams) * slots):
        t0 = time.perf_counter()
        adv = draft_live.advise(players, picks, teams, teams[0], budget, slots)
        times.append(time.perf_counter() - t0)
        pid = (
            adv["targets"][0] if rng.random() < FOLLOW_TARGET else rng.choice(list(adv["players"]))
        )
        team = rng.choice([t for t in teams if adv["teams"][t]["open"] > 0])
        price = round(adv["players"][pid]["adj"] * rng.uniform(*PRICE_NOISE))
        picks.append(
            {
                "pid": pid,
                "team": team,
                "price": max(1, min(int(adv["teams"][team]["max_bid"]), price)),
            }
        )
    final = draft_live.team_state(picks, teams, budget, slots)
    times.sort()
    return MockResult(
        picks=len(picks),
        rosters_full=all(s["open"] == 0 and s["left"] >= 0 for s in final.values()),
        spent=sum(s["spent"] for s in final.values()),
        p50_ms=times[len(times) // 2] * 1000,
        max_ms=times[-1] * 1000,
    )
