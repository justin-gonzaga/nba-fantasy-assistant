"""ANL-010: estimators for team/coach effects, checked on synthetic data with known answers."""

import numpy as np
import polars as pl
import pytest

from fantasy_evaluation import team_effects as te


def _seasons() -> pl.DataFrame:
    """Two seasons, three teams: 1 moves A→B, 2 stays on A, 3 stays on B, 4 leaves A (gone in t)."""
    rows = [
        # season, player, first team, last team, fga
        ("2023-24", 1, 10, 10, 500),
        ("2023-24", 2, 10, 10, 300),
        ("2023-24", 3, 20, 20, 400),
        ("2023-24", 4, 10, 10, 200),
        ("2024-25", 1, 20, 20, 450),
        ("2024-25", 2, 10, 10, 320),
        ("2024-25", 3, 20, 20, 380),
        ("2024-25", 5, 30, 30, 999),  # the future: nothing about t may leak into the flags
    ]
    return pl.DataFrame(
        rows,
        schema=["season", "nba_player_id", "first_nba_team_id", "last_nba_team_id", "fga"],
        orient="row",
    )


def _context() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": ["2023-24", "2023-24", "2023-24", "2024-25", "2024-25", "2024-25"],
            "nba_team_id": [10, 20, 30, 10, 20, 30],
            "new_coach": [None, None, None, True, False, None],
            "pace": [98.0, 102.0, 100.0, 120.0, 130.0, 140.0],  # t paces are absurd on purpose
        }
    )


def test_context_flags_use_only_draft_time_information() -> None:
    f = te.context_flags(_seasons(), _context(), "2024-25").sort("nba_player_id")
    by = {r["nba_player_id"]: r for r in f.iter_rows(named=True)}
    assert by[1]["moved"] is True
    assert by[2]["moved"] is False
    assert by[3]["moved"] is False
    assert by[2]["new_coach"] is True
    assert by[1]["new_coach"] is False
    # pace change from LAST season's paces: B (102) - A (98) for the mover, 0 for stayers
    assert by[1]["pace_change"] == pytest.approx(4.0)
    assert by[2]["pace_change"] == pytest.approx(0.0)
    # team A lost players 1 and 4: (500 + 200) / (500 + 300 + 200) of its t-1 shots
    assert by[2]["usage_freed"] == pytest.approx(0.7)
    assert by[3]["usage_freed"] == pytest.approx(0.0)  # B lost nobody (1 arrived)


def test_no_future_context() -> None:
    """Changing anything measured in t (pace in t, a coach in t+1) must not change the flags."""
    a = te.context_flags(_seasons(), _context(), "2024-25")
    later = _context().with_columns(
        pl.when(pl.col("season") == "2024-25")
        .then(pl.lit(50.0))
        .otherwise(pl.col("pace"))
        .alias("pace")
    )
    b = te.context_flags(_seasons(), later, "2024-25")
    assert a.equals(b)
    assert (
        5 not in a["nba_player_id"].to_list()
        or a.filter(pl.col("nba_player_id") == 5)["moved"].item() is not None
    )


def test_ols_recovers_a_planted_effect_and_its_variance_share() -> None:
    rng = np.random.default_rng(0)
    n = 4000
    flag = rng.integers(0, 2, n).astype(float)
    noise = rng.normal(0, 1, n)
    y = 0.5 * flag + noise
    fit = te.ols(y, {"flag": flag, "junk": rng.normal(0, 1, n)})
    assert fit["flag"].coef == pytest.approx(0.5, abs=0.08)
    assert fit["flag"].ci[0] < 0.5 < fit["flag"].ci[1]
    assert fit["flag"].p < 1e-6
    # the flag explains 0.25·0.25 / (0.0625 + 1) ≈ 5.9 % of the variance
    assert fit["flag"].share == pytest.approx(0.059, abs=0.015)
    assert fit["junk"].ci[0] < 0 < fit["junk"].ci[1]


def test_ols_null_case_covers_zero() -> None:
    rng = np.random.default_rng(1)
    n = 3000
    fit = te.ols(rng.normal(0, 1, n), {"a": rng.normal(0, 1, n), "b": rng.integers(0, 2, n) * 1.0})
    for r in fit.values():
        assert r.ci[0] < 0 < r.ci[1]
        assert r.share < 0.005


def test_holm_adjusts_in_step_down_order() -> None:
    assert te.holm([0.01, 0.04, 0.03, 0.20]) == pytest.approx([0.04, 0.09, 0.09, 0.20])


def test_decision_rule_is_the_pre_registered_one() -> None:
    def fit(share: float, p: float) -> te.Term:
        return te.Term(coef=1.0, se=0.1, ci=(0.8, 1.2), p=p, share=share)

    go = te.decide({"moved": fit(0.03, 0.001), "pace_change": fit(0.001, 0.5)})
    assert go.go
    assert go.reasons == ["moved"]
    small = te.decide({"moved": fit(0.015, 0.0001)})  # significant but under 2 %
    assert not small.go
    weak = te.decide({"moved": fit(0.05, 0.03), "a": fit(0.0, 0.9), "b": fit(0.0, 0.9)})
    # 0.03 x 3 tests = 0.09 after Holm: not significant
    assert not weak.go


def test_team_share_beats_the_permutation_null_only_when_planted() -> None:
    rng = np.random.default_rng(2)
    teams = rng.integers(0, 30, 3000)
    effect = rng.normal(0, 1, 30)
    planted = effect[teams] + rng.normal(0, 1, 3000)
    share, null = te.group_share(planted, teams, n_perm=100, seed=3)
    assert share > 0.4
    assert share > null + 0.3
    flat = rng.normal(0, 1, 3000)
    share0, null0 = te.group_share(flat, teams, n_perm=100, seed=3)
    assert abs(share0 - null0) < 0.01
