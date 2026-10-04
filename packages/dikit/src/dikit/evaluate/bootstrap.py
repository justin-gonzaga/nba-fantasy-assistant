"""Bootstrap resampling and percentile intervals.

Clustered (block) bootstraps resample whole clusters (e.g. weeks or days) so that within-cluster
dependence is kept [R-55]; the statistic is a ratio of sums, so clusters weigh by their size.
Cluster order is fixed (sorted), so a seed always gives the same interval.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def resample_idx(n: int, n_boot: int, rng: np.random.Generator) -> NDArray[np.int64]:
    """(n_boot, n) indices drawn with replacement."""
    return np.asarray(rng.integers(0, n, size=(n_boot, n)), dtype=np.int64)


def idx(n: int, n_boot: int, seed: int) -> NDArray[np.int64]:
    return resample_idx(n, n_boot, np.random.default_rng(seed))


def ci(samples: NDArray[np.floating]) -> tuple[float, float]:
    """Central 95 % percentile interval of bootstrap samples."""
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return float(lo), float(hi)


def _quantiles(boot: NDArray[np.inexact]) -> tuple[float, float]:
    return float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def mean_ci(x: NDArray[np.floating], n_boot: int, rng: np.random.Generator) -> tuple[float, float]:
    """95 % interval of the mean, resampling observations independently."""
    boot = x[resample_idx(len(x), n_boot, rng)].mean(axis=1)
    return _quantiles(boot)


def ratio_ci(
    sums: NDArray[np.floating], counts: NDArray[np.number], n_boot: int, rng: np.random.Generator
) -> tuple[float, float]:
    """95 % interval of sum(sums) / sum(counts), resampling clusters (one entry per cluster)."""
    i = resample_idx(len(sums), n_boot, rng)
    boot = sums[i].sum(axis=1) / counts[i].sum(axis=1)
    return _quantiles(boot)


def clustered_mean_ci(
    x: NDArray[np.floating], clusters: NDArray[np.generic], n_boot: int, rng: np.random.Generator
) -> tuple[float, float]:
    """95 % interval of the mean of x, resampling whole clusters (block bootstrap)."""
    uniq = np.unique(clusters)
    sums = np.array([x[clusters == c].sum() for c in uniq])
    counts = np.array([(clusters == c).sum() for c in uniq])
    return ratio_ci(sums, counts, n_boot, rng)
