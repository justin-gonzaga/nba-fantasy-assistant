import numpy as np
import pytest
from scipy import stats

from dikit.evaluate import scoring as sc

RNG = np.random.default_rng(7)


def _poisson_cdf(mu: float, n: int, kmax: int = 80) -> np.ndarray:
    return np.tile(stats.poisson.cdf(np.arange(kmax + 1), mu), (n, 1))


def test_crps_of_a_point_forecast_is_the_absolute_error() -> None:
    cdf = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]])  # all mass on 5
    assert sc.crps_counts(cdf, np.array([2]))[0] == pytest.approx(3.0)


def test_sample_crps_matches_the_exact_value() -> None:
    exact = sc.crps_counts(_poisson_cdf(7.0, 1), np.array([7]))[0]
    samples = RNG.poisson(7.0, (1, 20_000)).astype(float)
    assert sc.crps_samples(samples, np.array([7.0]))[0] == pytest.approx(exact, rel=0.03)


def test_randomized_pit_is_uniform_under_the_true_model() -> None:
    x = RNG.poisson(4.0, 20_000)
    pit = sc.pit_counts(_poisson_cdf(4.0, len(x)), x, RNG)
    assert sc.pit_deviation(pit) < 0.01
    assert sc.pit_deviation(np.full(1000, 0.05)) > 0.1  # everything in one bin


def test_spearman_matches_definition_and_supports_batches() -> None:
    x = np.array([3.0, 1.0, 2.0, 5.0])
    assert sc.spearman(x, x) == pytest.approx(1.0)
    assert sc.spearman(x, -x) == pytest.approx(-1.0)
    batch = np.stack([x, -x])
    assert sc.spearman(batch, np.stack([x, x])).tolist() == pytest.approx([1.0, -1.0])
