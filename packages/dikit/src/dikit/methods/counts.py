"""Count distributions: negative binomial for over-dispersed counts, beta-binomial for makes.

- Counts: negative binomial parameterised by mean and size r (var = m + m^2/r; r -> infinity is
  Poisson) [R-30, R-31]. A total of n iid units has size n*r and mean n*m.
- Successes given trials: beta-binomial with intra-class correlation rho (rho = 0 is binomial).
- Dispersions by the method of moments on (observation, predicted mean) pairs.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy import stats

Array = NDArray[np.float64]
MAX_SIZE = 1e6  # "no over-dispersion": treated as Poisson


def nb_size(
    x: NDArray[np.integer] | Array, mu: Array, units: NDArray[np.integer] | None = None
) -> float:
    """Moment estimate of the per-unit NB size r from observations and predicted means.
    Per unit: E[(x - mu)^2 - mu] = mu^2 / r. For totals over n units (mean mu = n * m):
    E[(x - mu)^2 - mu] = mu^2 / (n r). Returns inf when there's no over-dispersion."""
    x = np.asarray(x, dtype=float)
    n = np.ones_like(x) if units is None else np.asarray(units, dtype=float)
    excess = float(np.sum((x - mu) ** 2 - mu))
    if excess <= 0:
        return float(np.inf)
    r = float(np.sum(mu**2 / n)) / excess
    return float(np.inf) if r > MAX_SIZE else r


def betabin_rho(makes: NDArray[np.integer], att: NDArray[np.integer], p: Array) -> float:
    """Moment estimate of beta-binomial rho: Var(M | n) = n p (1-p) [1 + (n-1) rho]."""
    m, n = np.asarray(makes, dtype=float), np.asarray(att, dtype=float)
    num = float(np.sum((m - n * p) ** 2 - n * p * (1 - p)))
    den = float(np.sum(n * (n - 1) * p * (1 - p)))
    return max(0.0, num / den) if den > 0 else 0.0


def total_size(size: float, units: int | NDArray[np.integer]) -> float | Array:
    """Size of a total over n iid units: n * r (inf stays inf)."""
    if not np.isfinite(size):
        return float(np.inf)
    if isinstance(units, int):
        return float(size * units)
    return np.asarray(units, dtype=np.float64) * size


def count_cdf(mean: Array, *, size: float | Array, kmax: int) -> Array:
    """CDF on 0..kmax for each forecast: shape (len(mean), kmax + 1)."""
    k = np.arange(kmax + 1)
    mean = np.asarray(mean, dtype=float)[:, None]
    size_arr = np.broadcast_to(np.asarray(size, dtype=float), mean.shape[:1])[:, None]
    pois = stats.poisson.cdf(k, mean)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = np.where(np.isfinite(size_arr), size_arr / (size_arr + mean), 1.0)
        nb = stats.nbinom.cdf(k, np.where(np.isfinite(size_arr), size_arr, 1.0), p)
    out: Array = np.where(np.isfinite(size_arr), nb, pois)
    return out


def sample_makes(
    att: NDArray[np.integer], p: Array, rho: float, rng: np.random.Generator
) -> NDArray[np.integer]:
    """Makes given attempts: binomial (rho = 0) or beta-binomial."""
    if rho <= 0:
        return np.asarray(rng.binomial(att, p), dtype=np.int64)
    a = p * (1 - rho) / rho
    b = (1 - p) * (1 - rho) / rho
    return np.asarray(rng.binomial(att, rng.beta(a, b)), dtype=np.int64)


def sample_counts(
    mean: Array, size: float | Array, draws: int, rng: np.random.Generator
) -> NDArray[np.integer]:
    """Draws (rows = forecasts) from Poisson (size inf) or NB(size, mean)."""
    mean = np.asarray(mean, dtype=float)[:, None]
    size_arr = np.broadcast_to(np.asarray(size, dtype=float), mean.shape[:1])[:, None]
    finite = np.isfinite(size_arr)
    pois = rng.poisson(np.broadcast_to(mean, (mean.shape[0], draws)))
    safe = np.where(finite, size_arr, 1.0)
    nb = rng.negative_binomial(
        np.broadcast_to(safe, (mean.shape[0], draws)),
        np.broadcast_to(safe / (safe + mean), (mean.shape[0], draws)),
    )
    out: NDArray[np.integer] = np.where(finite, nb, pois)
    return out
