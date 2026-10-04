"""Empirical-Bayes shrinkage: conjugate priors fitted by moments, and prior/data blending.

- Rates: a Gamma-Poisson prior (mean, strength in exposure units) [R-11].
- Proportions: a Beta-Binomial prior (mean, strength in trials).
- Blend: per-unit estimate = (k * prior + total) / (k + units); k is chosen on selection data by
  the lowest absolute error over a fixed grid [R-12].
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


@dataclass(frozen=True)
class RatePrior:
    """Gamma-Poisson prior for a rate: mean `mu`, strength `k` exposure units."""

    mu: float
    k: float


@dataclass(frozen=True)
class PctPrior:
    """Beta-Binomial prior for a shooting %: mean `p`, strength `k` attempts."""

    p: float
    k: float


def fit_rate_prior(counts: np.ndarray, exposure: np.ndarray) -> RatePrior:
    """Method-of-moments Gamma-Poisson fit [R-11]: between-unit variance net of Poisson noise."""
    keep = exposure > 0
    x, m = counts[keep].astype(float), exposure[keep].astype(float)
    mu = x.sum() / m.sum()
    r = x / m
    observed = float(np.sum(m * (r - mu) ** 2) / m.sum())
    noise = mu * keep.sum() / m.sum()
    tau2 = max(observed - noise, 1e-12)
    return RatePrior(mu=float(mu), k=float(mu / tau2))


def fit_pct_prior(makes: np.ndarray, attempts: np.ndarray) -> PctPrior:
    """Method-of-moments Beta-Binomial fit: the prior strength is in attempts."""
    keep = attempts > 0
    x, n = makes[keep].astype(float), attempts[keep].astype(float)
    p = x.sum() / n.sum()
    observed = float(np.sum(n * (x / n - p) ** 2) / n.sum())
    noise = p * (1 - p) * keep.sum() / n.sum()
    tau2 = max(observed - noise, 1e-12)
    return PctPrior(p=float(p), k=float(max(p * (1 - p) / tau2 - 1, 1.0)))


K_GRID = (0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0, 30.0, 50.0, 80.0, 120.0, 200.0, 1e9)


def blend(prior: Array, total: NDArray[np.number], units: NDArray[np.number], k: float) -> Array:
    """Per-unit estimate: k units' worth of prior plus the data so far."""
    units = np.asarray(units, dtype=float)
    total = np.asarray(total, dtype=float)
    out: Array = (k * prior + total) / np.maximum(k + units, 1e-12)
    return out


def choose_k(  # noqa: PLR0913 - the blend's inputs plus the period being predicted
    prior: Array,
    total: NDArray[np.number],
    units: NDArray[np.number],
    next_units: NDArray[np.number],
    next_actual: NDArray[np.number],
    *,
    grid: tuple[float, ...] = K_GRID,
) -> float:
    """The k on the grid with the lowest MAE on the next period (selection data only)."""
    wn = np.asarray(next_units, dtype=float)
    wy = np.asarray(next_actual, dtype=float)
    errors = [float(np.abs(wy - wn * blend(prior, total, units, k)).mean()) for k in grid]
    return grid[int(np.argmin(errors))]
