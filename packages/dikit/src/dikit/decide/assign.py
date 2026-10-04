"""Slot assignment: fill capacity-limited slots with eligible, available candidates.

Objective (lexicographic): first the number of candidates assigned, then the sum of their value.
Encoded as one linear objective: each assignment scores BIG + value, with BIG larger than any
possible value total, so one more assignment always wins. Solved exactly with HiGHS through SciPy
[R-04]. A `flex` slot, if named, accepts any candidate. `greedy` is the simple baseline.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp


@dataclass(frozen=True)
class Candidate:
    id: int
    value: float
    eligible: tuple[str, ...]
    available: bool


def _slots_for(c: Candidate, slots: Mapping[str, int], flex: str | None) -> list[str]:
    return [s for s in slots if slots[s] > 0 and (s == flex or s in c.eligible)]


def greedy(
    cands: Sequence[Candidate], slots: Mapping[str, int], flex: str | None = None
) -> dict[int, str]:
    """Best value first; the scarcest eligible slot, then the flex slot."""
    free = dict(slots)
    out: dict[int, str] = {}
    for c in sorted(cands, key=lambda c: -c.value):
        if not c.available:
            continue
        elig = [p for p in c.eligible if free.get(p, 0) > 0]
        slot = (
            min(elig, key=lambda p: free[p])
            if elig
            else (flex if flex is not None and free.get(flex, 0) > 0 else None)
        )
        if slot is not None:
            free[slot] -= 1
            out[c.id] = slot
    return out


def optimise(
    cands: Sequence[Candidate], slots: Mapping[str, int], flex: str | None = None
) -> dict[int, str]:
    pairs = [(i, s) for i, c in enumerate(cands) if c.available for s in _slots_for(c, slots, flex)]
    if not pairs:
        return {}
    big = 1.0 + sum(abs(c.value) for c in cands)
    cost = np.array([-(big + cands[i].value) for i, _ in pairs])
    rows = []
    upper = []
    for i in {i for i, _ in pairs}:  # each candidate at most one slot
        rows.append([1.0 if p == i else 0.0 for p, _ in pairs])
        upper.append(1.0)
    for s in slots:  # each slot within capacity
        rows.append([1.0 if q == s else 0.0 for _, q in pairs])
        upper.append(float(slots[s]))
    res = milp(
        cost,
        constraints=LinearConstraint(np.array(rows), -np.inf, np.array(upper)),
        integrality=np.ones(len(pairs), dtype=np.int64),
        bounds=Bounds(0, 1),
        options={
            "mip_rel_gap": 0.0
        },  # exact: the default 1e-4 gap can hide small value differences
    )
    if not res.success:  # pragma: no cover - a feasible problem always solves
        msg = f"slot assignment failed: {res.message}"
        raise RuntimeError(msg)
    return {cands[i].id: s for (i, s), x in zip(pairs, res.x, strict=True) if x > 0.5}  # noqa: PLR2004


def score(assign: Mapping[int, str], cands: Sequence[Candidate]) -> tuple[int, float]:
    value = {c.id: c.value for c in cands}
    return len(assign), round(sum(value[p] for p in assign), 9)


def legal(
    assign: Mapping[int, str],
    cands: Sequence[Candidate],
    slots: Mapping[str, int],
    flex: str | None = None,
) -> bool:
    by_id = {c.id: c for c in cands}
    for cid, s in assign.items():
        c = by_id[cid]
        if not c.available or s not in slots or (s != flex and s not in c.eligible):
            return False
    return all(list(assign.values()).count(s) <= n for s, n in slots.items())
