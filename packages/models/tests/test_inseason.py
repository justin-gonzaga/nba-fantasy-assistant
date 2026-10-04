import numpy as np
import polars as pl
import pytest

from dikit.methods import shrinkage
from fantasy_models import inseason as ins

PRIOR = np.array([10.0, 20.0])
TOTAL = np.array([60.0, 60.0])  # season-to-date totals
GAMES = np.array([3, 3])


def test_k_zero_is_season_to_date_and_huge_k_is_the_prior() -> None:
    assert shrinkage.blend(PRIOR, TOTAL, GAMES, 0.0) == pytest.approx([20.0, 20.0])
    assert shrinkage.blend(PRIOR, TOTAL, GAMES, 1e9) == pytest.approx(PRIOR, rel=1e-6)


def test_the_weight_on_data_grows_with_games() -> None:
    few = shrinkage.blend(np.array([10.0]), np.array([20.0]), np.array([1]), 4.0)[0]  # 1 game at 20
    many = shrinkage.blend(np.array([10.0]), np.array([400.0]), np.array([20]), 4.0)[
        0
    ]  # 20 games at 20
    assert 10 < few < many < 20


def test_choose_k_recovers_the_best_weight_on_known_data() -> None:
    rng = np.random.default_rng(0)
    n = 20_000
    talent = rng.normal(15, 4, n)
    prior = talent + rng.normal(0, 2, n)  # the prior is informative but noisy
    games = rng.integers(1, 40, n)
    total = rng.poisson(np.clip(talent, 0.1, None) * games)
    week_n = np.full(n, 3)
    week_y = rng.poisson(np.clip(talent, 0.1, None) * week_n)
    k = shrinkage.choose_k(prior, total, games, week_n, week_y)
    assert 0 < k < 1e6  # neither ignores the prior nor the season so far

    def mae(kk: float) -> float:
        return float(np.abs(week_y - week_n * shrinkage.blend(prior, total, games, kk)).mean())

    assert mae(k) <= min(mae(0.0), mae(1e9))


def test_update_long_blends_shipped_stats_and_leaves_the_rest() -> None:
    per_game = pl.DataFrame(
        {"nba_player_id": [1, 1, 2], "stat": ["pts", "games", "pts"], "mean": [10.0, 70.0, 12.0]}
    )
    season = pl.DataFrame({"nba_player_id": [1], "games": [3], "pts": [60.0]})
    out = {
        (r["nba_player_id"], r["stat"]): r["mean"]
        for r in ins.update_long(per_game, season).iter_rows(named=True)
    }
    k = ins.K_SHIPPED["pts"]
    assert out[(1, "pts")] == pytest.approx((k * 10 + 60) / (k + 3))
    assert out[(1, "games")] == 70.0  # not a blended stat
    assert out[(2, "pts")] == 12.0  # no games yet this season
