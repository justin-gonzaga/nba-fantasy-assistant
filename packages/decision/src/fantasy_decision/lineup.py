"""Daily lineup (DEC-007; methodology §19, D-61): the NBA binding of `dikit.decide.assign` [R-04].

Objective (lexicographic, pre-registered): first the number of active players who play today, then
the sum of their value. `Util` is the flex slot. `greedy` is the MVP rule it replaces (kept for
comparison).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from dikit.decide import assign

UTIL = "Util"


@dataclass(frozen=True)
class Candidate:
    pid: int
    value: float
    eligible: tuple[str, ...]  # G/F/C
    plays: bool  # has a game today and isn't Out


def _generic(cands: Sequence[Candidate]) -> list[assign.Candidate]:
    return [assign.Candidate(c.pid, c.value, c.eligible, c.plays) for c in cands]


def greedy(cands: Sequence[Candidate], slots: Mapping[str, int]) -> dict[int, str]:
    """Best value first; the scarcest eligible position slot, then Util (the MVP-003 rule)."""
    return assign.greedy(_generic(cands), slots, flex=UTIL)


def optimise(cands: Sequence[Candidate], slots: Mapping[str, int]) -> dict[int, str]:
    return assign.optimise(_generic(cands), slots, flex=UTIL)


def score(assignment: Mapping[int, str], cands: Sequence[Candidate]) -> tuple[int, float]:
    return assign.score(assignment, _generic(cands))


def legal(
    assignment: Mapping[int, str], cands: Sequence[Candidate], slots: Mapping[str, int]
) -> bool:
    return assign.legal(assignment, _generic(cands), slots, flex=UTIL)
