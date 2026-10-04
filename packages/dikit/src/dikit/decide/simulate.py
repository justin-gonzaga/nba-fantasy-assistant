"""Monte Carlo head-to-head over categories.

Each side's period totals are simulated per category: negative-binomial counts (per-unit size r, so
a member's period has size units * r), and for ratio categories negative-binomial attempts with
beta-binomial successes. P(side A wins a category) = the share of draws A beats B (ties count half;
lower-is-better categories reversed). One seed drives both sides, so two line-ups compared with the
same seed share their random numbers (common random numbers [R-61]).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


@dataclass(frozen=True)
class Ratio:
    attempts: str  # the key in Side.attempts
    attempts_size: float  # per-unit NB size of attempts
    rho: float  # beta-binomial intra-class correlation of successes


@dataclass(frozen=True)
class Categories:
    counts: Mapping[str, float]  # name -> per-unit NB size, in simulation order
    ratios: Mapping[str, Ratio]  # name -> attempts and dispersion, simulated after the counts
    lower_is_better: frozenset[str] = frozenset()

    @property
    def names(self) -> tuple[str, ...]:
        return (*self.counts, *self.ratios)


@dataclass(frozen=True)
class Side:
    """Per-member period expectations: counts[cat], attempts[key], pct[ratio cat], units."""

    counts: dict[str, Array]
    attempts: dict[str, Array]
    pct: dict[str, Array]
    units: NDArray[np.integer]


@dataclass(frozen=True)
class Result:
    probs: dict[str, float]
    expected_categories: float
    se_expected_categories: float
    p_win: float  # P(more than half of the categories)


def _nb(mean: Array, size: Array, draws: int, rng: np.random.Generator) -> NDArray[np.integer]:
    """(members, draws) negative-binomial draws; members with zero mean draw 0."""
    mean = np.maximum(mean, 1e-9)[:, None]
    size = size[:, None]
    return np.asarray(rng.negative_binomial(size, size / (size + mean), (len(mean), draws)))


def totals(side: Side, cats: Categories, draws: int, rng: np.random.Generator) -> dict[str, Array]:
    """Simulated period totals per category (ratios as total successes / total attempts)."""
    units = np.maximum(side.units, 1).astype(float)
    out: dict[str, Array] = {}
    for c, size in cats.counts.items():
        out[c] = _nb(side.counts[c], units * size, draws, rng).sum(axis=0).astype(float)
    for cat, r in cats.ratios.items():
        att = _nb(side.attempts[r.attempts], units * r.attempts_size, draws, rng)
        p = np.clip(side.pct[cat], 0.01, 0.99)[:, None]
        a, b = p * (1 - r.rho) / r.rho, (1 - p) * (1 - r.rho) / r.rho
        makes = rng.binomial(
            att, rng.beta(np.broadcast_to(a, att.shape), np.broadcast_to(b, att.shape))
        )
        tot_att = att.sum(axis=0)
        out[cat] = np.where(tot_att > 0, makes.sum(axis=0) / np.maximum(tot_att, 1), 0.0)
    return out


def matchup(
    side_a: Side, side_b: Side, cats: Categories, *, draws: int = 2000, seed: int = 0
) -> Result:
    rng = np.random.default_rng(seed)
    ta, tb = totals(side_a, cats, draws, rng), totals(side_b, cats, draws, rng)
    wins = np.zeros(draws)
    probs = {}
    for c in cats.names:
        a, b = (tb[c], ta[c]) if c in cats.lower_is_better else (ta[c], tb[c])
        per_draw = (a > b) + 0.5 * (a == b)
        probs[c] = float(per_draw.mean())
        wins += per_draw
    majority = len(cats.names) / 2
    return Result(
        probs,
        float(wins.mean()),
        float(wins.std(ddof=1) / np.sqrt(draws)),
        float((wins > majority).mean() + 0.5 * (wins == majority).mean()),
    )
