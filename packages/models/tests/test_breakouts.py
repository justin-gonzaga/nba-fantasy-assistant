import numpy as np
import polars as pl
import pytest

from dikit.errors import LeakageError
from dikit.methods import regression as rg
from fantasy_models.preseason import breakouts as b
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.schema import history_before
from fantasy_models.preseason.synthetic import make_league

SEASONS, DRAFT = make_league(seed=21, n_players=300)
T = "2025-26"
HIST = history_before(SEASONS, T)
ROSTER = b.rosters_from_season(SEASONS, T)


def test_no_future_features() -> None:
    """AC1: features for a target never read the target season (beyond the opening roster)."""
    with pytest.raises(LeakageError, match="2025-26"):
        b.features(SEASONS, ROSTER, T)
    f = b.features(HIST, ROSTER, T)
    assert set(b.M2_FEATURES) <= set(f.columns)
    assert f.height > 50
    assert f.select(b.M2_FEATURES).null_count().sum_horizontal()[0] == 0


def test_vacated_minutes_counts_players_who_left() -> None:
    last = HIST.filter(pl.col("season") == "2024-25")
    team = int(last.get_column("last_nba_team_id")[0])
    on_team = last.filter(pl.col("last_nba_team_id") == team)
    leaver = int(on_team.get_column("nba_player_id")[0])
    stay = on_team.filter(pl.col("nba_player_id") != leaver).select(
        "nba_player_id", pl.lit(team, pl.Int64).alias("team")
    )
    roster = pl.concat(
        [
            stay,
            pl.DataFrame(
                {"nba_player_id": [leaver], "team": [team + 1]},
                schema={"nba_player_id": pl.Int64, "team": pl.Int64},
            ),
        ]
    )
    f = b.features(HIST, roster, T).filter(
        pl.col("nba_player_id").is_in(stay["nba_player_id"].to_list())
    )
    left_min = float(on_team.filter(pl.col("nba_player_id") == leaver)["minutes"][0])
    assert f["net_vacated_min"].to_list()[0] == pytest.approx(left_min / 1000, rel=1e-6)
    moved = b.features(HIST, roster, T).filter(pl.col("nba_player_id") == leaver)
    assert moved["changed_team"][0] == 1.0


def test_ridge_recovers_a_linear_relation() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(size=(2000, 3))
    y = 2.0 * x[:, 0] - 1.0 * x[:, 2] + 5 + rng.normal(0, 0.1, 2000)
    pred = rg.Ridge(alpha=0.1).fit(x, y).predict(x)
    assert np.abs(pred - y).mean() < 0.2


def test_gbm_fits() -> None:
    rng = np.random.default_rng(1)
    x = rng.normal(size=(500, 2))
    y = np.where(x[:, 0] > 0, 3.0, -3.0)
    assert np.abs(b.GBM().fit(x, y).predict(x) - y).mean() < 0.5


def test_logistic_is_calibrated_despite_class_weights() -> None:
    rng = np.random.default_rng(2)
    x = rng.normal(size=(20000, 2))
    logit = -3.0 + 1.5 * x[:, 0]
    y = (rng.uniform(size=20000) < 1 / (1 + np.exp(-logit))).astype(float)
    p = rg.Logistic(l2=1.0).fit(x, y).predict_proba(x)
    assert p.mean() == pytest.approx(y.mean(), rel=0.1)  # prior correction keeps it calibrated
    assert p[x[:, 0] > 1].mean() > p[x[:, 0] < -1].mean()


def test_breakout_label_definition() -> None:
    lab = b.breakout_labels(SEASONS, T, jump=50, top=150)
    hits = lab.filter(pl.col("breakout") == 1)
    assert ((hits["rank_last"] - hits["rank"]) >= 50).all()
    assert (hits["rank"] <= 150).all()
    assert 0 < float(lab["breakout"].mean()) < 0.5  # type: ignore[arg-type]


def test_predict_mpg_and_override_in_hybrid() -> None:
    train = b.training_rows(SEASONS, ["2022-23", "2023-24", "2024-25"])
    feats = b.features(HIST, ROSTER, T)
    pred = b.predict_mpg(rg.Ridge(), train, feats)
    assert pred["mpg_m1"].is_between(0, b.MPG_CAP).all()
    h = m.hybrid(HIST, T, aging=False, mpg_override=pred)
    j = h.join(pred, on="nba_player_id")
    assert np.allclose(j["mpg"].to_numpy(), j["mpg_m1"].to_numpy())


def test_add_preseason_features_and_missing_flags() -> None:
    feats = b.features(HIST, ROSTER, T)
    ids = feats["nba_player_id"].to_list()[:3]
    pre = pl.DataFrame(
        {
            "season": [T] * 2,
            "nba_player_id": ids[:2],
            "pre_games": [5, 4],
            "pre_mpg": [30.0, 12.0],
            "pre_team_minutes_share": [0.15, 0.06],
            "pre_start_share": [1.0, None],
        },
        schema_overrides={"pre_start_share": pl.Float64},
    )
    out = (
        b.add_preseason(feats, pre).filter(pl.col("nba_player_id").is_in(ids)).sort("nba_player_id")
    )
    by = {r["nba_player_id"]: r for r in out.iter_rows(named=True)}
    a, c, none = by[ids[0]], by[ids[1]], by[ids[2]]
    assert a["pre_mpg_delta"] == pytest.approx(30.0 - a["mpg_last"])
    assert (a["pre_start_missing"], c["pre_start_missing"]) == (
        0.0,
        1.0,
    )  # unknown starts are flagged
    assert (none["pre_games"], none["pre_mpg_delta"], none["pre_start_missing"]) == (0.0, 0.0, 0.0)
    assert set(b.PRE_FEATURES) <= set(out.columns)


# ------------------------------------------------------------------ DRAFT-012: injury-robust input
def test_injury_robust_swaps_last_mpg_for_the_window_after_a_short_season() -> None:
    plain = b.features(HIST, ROSTER, T)
    robust = b.features(HIST, ROSTER, T, injury_robust=True)
    j = plain.join(robust, on="nba_player_id", suffix="_r")
    short = j.filter(pl.col("gp_frac_last") < b.INJURY_GP_FRAC)
    full = j.filter(pl.col("gp_frac_last") >= b.INJURY_GP_FRAC)
    assert short.height > 0
    assert full.height > 0
    assert (short["mpg_last_r"] - short["mpg_window"]).abs().max() < 1e-9  # type: ignore[operator]
    assert (full["mpg_last_r"] - full["mpg_last"]).abs().max() < 1e-9  # type: ignore[operator]
    others = [c for c in plain.columns if c not in {"nba_player_id", "mpg_last"}]
    assert j.select(others).equals(
        j.select([f"{c}_r" for c in others]).rename({f"{c}_r": c for c in others})
    )
