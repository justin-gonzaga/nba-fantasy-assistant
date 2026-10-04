import numpy as np
import pytest

from dikit.methods import counts, regression, shrinkage

RNG = np.random.default_rng(3)


def test_nb_size_is_recovered_and_poisson_has_none() -> None:
    mu = RNG.uniform(2, 15, 40_000)
    x = RNG.negative_binomial(3.0, 3.0 / (3.0 + mu))
    assert counts.nb_size(x, mu) == pytest.approx(3.0, rel=0.1)
    assert (
        np.isinf(counts.nb_size(RNG.poisson(mu), mu)) or counts.nb_size(RNG.poisson(mu), mu) > 200
    )


def test_betabin_rho_is_recovered() -> None:
    n = RNG.integers(5, 30, 30_000)
    p = RNG.beta(0.5 * (1 - 0.05) / 0.05, 0.5 * (1 - 0.05) / 0.05, len(n))
    makes = RNG.binomial(n, p)
    assert counts.betabin_rho(makes, n, np.full(len(n), 0.5)) == pytest.approx(0.05, abs=0.01)


def test_total_size_scales_with_units() -> None:
    assert counts.total_size(2.0, 3) == 6.0
    assert np.isinf(counts.total_size(np.inf, 3))


def test_count_cdf_and_sampling_agree() -> None:
    cdf = counts.count_cdf(np.array([4.0]), size=2.0, kmax=60)
    draws = counts.sample_counts(np.array([4.0]), 2.0, 20_000, RNG)
    assert cdf[0, 4] == pytest.approx((draws <= 4).mean(), abs=0.01)
    makes = counts.sample_makes(np.full(10_000, 10), np.full(10_000, 0.4), 0.0, RNG)
    assert makes.mean() == pytest.approx(4.0, abs=0.1)


def test_rate_and_proportion_priors_recover_their_means() -> None:
    exposure = RNG.uniform(100, 2000, 3000)
    rates = RNG.gamma(4.0, 0.25 / 4.0, 3000)  # mean 0.25, strength 16
    prior = shrinkage.fit_rate_prior(RNG.poisson(rates * exposure), exposure)
    assert prior.mu == pytest.approx(0.25, rel=0.03)
    trials = RNG.integers(20, 400, 3000)
    pct = shrinkage.fit_pct_prior(RNG.binomial(trials, RNG.beta(40, 60, 3000)), trials)
    assert pct.p == pytest.approx(0.4, abs=0.01)
    assert 50 < pct.k < 200  # the true strength is 100 trials


def test_blend_moves_from_prior_to_data_and_choose_k_picks_the_truth() -> None:
    assert shrinkage.blend(np.array([10.0]), np.array([0.0]), np.array([0]), 5.0)[0] == 10.0
    assert shrinkage.blend(np.array([10.0]), np.array([200.0]), np.array([10]), 0.0)[0] == 20.0
    truth = RNG.uniform(5, 15, 4000)
    prior = truth + RNG.normal(0, 3, 4000)  # noisy prior
    units = np.full(4000, 5)
    total = RNG.poisson(truth * 5)
    nxt = RNG.poisson(truth * 5)
    k = shrinkage.choose_k(prior, total, units, units, nxt)
    assert 0 < k < 1e9  # neither pure data nor pure prior


def test_ridge_and_logistic_fit_simple_signals() -> None:
    x = RNG.normal(size=(2000, 3))
    y = 2.0 * x[:, 0] - x[:, 1] + RNG.normal(0, 0.1, 2000)
    pred = regression.Ridge(alpha=1.0).fit(x, y).predict(x)
    assert np.corrcoef(pred, y)[0, 1] > 0.99
    yb = (x[:, 0] + RNG.normal(0, 0.5, 2000) > 1.2).astype(float)  # rare positives
    p = regression.Logistic().fit(x, yb).predict_proba(x)
    assert p[yb == 1].mean() > p[yb == 0].mean() + 0.3
    assert p.mean() == pytest.approx(yb.mean(), abs=0.05)  # prior-corrected intercept
