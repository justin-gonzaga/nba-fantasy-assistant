"""Scoring rules for probabilistic forecasts and rankings.

- CRPS: exact on an integer support for count forecasts, the sample estimator otherwise [R-41].
- Randomized PIT for discrete forecasts, and its deviation from uniform [R-43, R-44].
- Spearman rank correlation along the last axis (a leading bootstrap axis is allowed).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


def crps_counts(cdf: Array, y: NDArray[np.integer] | Array) -> Array:
    """Exact CRPS on the integer support: sum_k (F(k) - 1{y <= k})^2."""
    k = np.arange(cdf.shape[1])
    step = (k[None, :] >= np.asarray(y)[:, None]).astype(float)
    out: Array = np.sum((cdf - step) ** 2, axis=1)
    return out


def crps_samples(samples: Array, y: Array) -> Array:
    """CRPS from samples (rows = forecasts): E|X - y| - 0.5 E|X - X'| (sorted-sample identity)."""
    s = np.sort(samples, axis=1)
    m = s.shape[1]
    term1 = np.mean(np.abs(s - y[:, None]), axis=1)
    weights = 2 * np.arange(1, m + 1) - m - 1
    term2 = np.sum(s * weights, axis=1) / (m * m)
    out: Array = term1 - term2
    return out


def pit_counts(cdf: Array, y: NDArray[np.integer], rng: np.random.Generator) -> Array:
    """Randomized PIT: F(y-1) + V (F(y) - F(y-1)), V ~ U(0, 1)."""
    y = np.asarray(y)
    i = np.arange(len(y))
    upper = cdf[i, np.minimum(y, cdf.shape[1] - 1)]
    lower = np.where(y > 0, cdf[i, np.maximum(y - 1, 0)], 0.0)
    out: Array = lower + rng.uniform(size=len(y)) * (upper - lower)
    return out


def pit_deviation(pit: Array, bins: int = 10) -> float:
    """Mean absolute deviation of the PIT histogram from uniform (0 = perfectly calibrated)."""
    hist, _ = np.histogram(pit, bins=bins, range=(0.0, 1.0))
    return float(np.mean(np.abs(hist / hist.sum() - 1.0 / bins)))


def ranks(x: NDArray[np.floating]) -> Array:
    return np.argsort(np.argsort(x, axis=-1), axis=-1).astype(float)


def spearman(x: NDArray[np.floating], y: NDArray[np.floating]) -> Array:
    """Spearman correlation along the last axis (supports a leading bootstrap axis)."""
    rx, ry = ranks(x), ranks(y)
    rx = rx - rx.mean(axis=-1, keepdims=True)
    ry = ry - ry.mean(axis=-1, keepdims=True)
    return np.asarray((rx * ry).sum(axis=-1) / np.sqrt((rx**2).sum(axis=-1) * (ry**2).sum(axis=-1)))
