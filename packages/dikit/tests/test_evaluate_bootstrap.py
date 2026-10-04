import numpy as np
import pytest

from dikit.evaluate import bootstrap as bs


def test_resample_idx_shape_and_range() -> None:
    idx = bs.resample_idx(7, 50, np.random.default_rng(0))
    assert idx.shape == (50, 7)
    assert idx.min() >= 0
    assert idx.max() <= 6


def test_idx_is_seeded() -> None:
    assert (bs.idx(10, 20, seed=3) == bs.idx(10, 20, seed=3)).all()


def test_ci_is_the_central_95_percent() -> None:
    lo, hi = bs.ci(np.arange(1001, dtype=float))
    assert (lo, hi) == pytest.approx((25.0, 975.0))


def test_mean_ci_contains_the_mean_and_shrinks_with_n() -> None:
    rng = np.random.default_rng(1)
    small = rng.normal(0, 1, 50)
    big = rng.normal(0, 1, 5000)
    lo_s, hi_s = bs.mean_ci(small, 500, np.random.default_rng(2))
    lo_b, hi_b = bs.mean_ci(big, 500, np.random.default_rng(2))
    assert lo_s < small.mean() < hi_s
    assert hi_b - lo_b < hi_s - lo_s


def test_ratio_ci_resamples_whole_clusters() -> None:
    # every cluster has the same ratio, so every resample does too
    sums, counts = np.array([2.0, 4.0, 6.0]), np.array([4.0, 8.0, 12.0])
    assert bs.ratio_ci(sums, counts, 200, np.random.default_rng(0)) == pytest.approx((0.5, 0.5))


def test_clustered_mean_ci_groups_by_cluster_in_sorted_order() -> None:
    x = np.array([1.0, 3.0, 10.0, 20.0])
    clusters = np.array([5, 5, 1, 1])
    shuffled = bs.clustered_mean_ci(x[::-1], clusters[::-1], 300, np.random.default_rng(4))
    assert bs.clustered_mean_ci(x, clusters, 300, np.random.default_rng(4)) == shuffled
    same = bs.ratio_ci(np.array([30.0, 4.0]), np.array([2.0, 2.0]), 300, np.random.default_rng(4))
    assert shuffled == same
