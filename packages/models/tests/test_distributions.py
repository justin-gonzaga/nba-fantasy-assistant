import numpy as np
import pytest

from dikit.evaluate import scoring as sc
from dikit.methods import counts as cnt

RNG = np.random.default_rng(7)


def test_poisson_data_shows_no_overdispersion() -> None:
    mu = RNG.uniform(1, 20, 20_000)
    x = RNG.poisson(mu)
    assert cnt.nb_size(x, mu) > 200  # effectively Poisson (size -> infinity)


def test_negative_binomial_size_is_recovered() -> None:
    mu = RNG.uniform(2, 15, 40_000)
    size = 4.0
    x = RNG.negative_binomial(size, size / (size + mu))
    assert cnt.nb_size(x, mu) == pytest.approx(size, rel=0.1)


def test_beta_binomial_correlation_is_recovered() -> None:
    n = RNG.integers(5, 25, 30_000)
    p = RNG.uniform(0.35, 0.6, 30_000)
    rho = 0.05
    a = p * (1 - rho) / rho
    b = (1 - p) * (1 - rho) / rho
    m = RNG.binomial(n, RNG.beta(a, b))
    assert cnt.betabin_rho(m, n, p) == pytest.approx(rho, abs=0.015)


def test_crps_of_a_point_forecast_is_the_absolute_error() -> None:
    cdf = cnt.count_cdf(np.array([0.0]), size=np.inf, kmax=10)  # all mass at 0
    assert sc.crps_counts(cdf, np.array([3]))[0] == pytest.approx(3.0)


def test_crps_prefers_the_true_distribution() -> None:
    mu = np.full(5_000, 8.0)
    x = RNG.negative_binomial(2.0, 2.0 / (2.0 + mu))
    kmax = int(x.max()) + 60
    nb = sc.crps_counts(cnt.count_cdf(mu, size=2.0, kmax=kmax), x).mean()
    pois = sc.crps_counts(cnt.count_cdf(mu, size=np.inf, kmax=kmax), x).mean()
    assert nb < pois


def test_sample_crps_matches_the_exact_value_for_counts() -> None:
    mu = np.array([5.0])
    exact = sc.crps_counts(cnt.count_cdf(mu, size=np.inf, kmax=60), np.array([7]))[0]
    samples = RNG.poisson(5.0, size=(1, 40_000)).astype(float)
    assert sc.crps_samples(samples, np.array([7.0]))[0] == pytest.approx(exact, rel=0.03)


def test_randomized_pit_is_uniform_under_the_true_model() -> None:
    mu = RNG.uniform(1, 10, 20_000)
    x = RNG.poisson(mu)
    cdf = cnt.count_cdf(mu, size=np.inf, kmax=int(x.max()) + 30)
    pit = sc.pit_counts(cdf, x, RNG)
    assert sc.pit_deviation(pit) < 0.01


def test_weekly_totals_scale_size_with_games() -> None:
    # The sum of n iid NB(size r, mean m) is NB(size n*r, mean n*m).
    assert cnt.total_size(3.0, 4) == pytest.approx(12.0)
    assert cnt.total_size(np.inf, 4) == np.inf


def test_size_is_recovered_from_weekly_totals() -> None:
    n = RNG.integers(1, 5, 30_000)
    m = RNG.uniform(2, 12, 30_000)
    size = 3.0
    y = RNG.negative_binomial(size * n, (size * n) / (size * n + m * n))
    assert cnt.nb_size(y, m * n, n) == pytest.approx(size, rel=0.1)
