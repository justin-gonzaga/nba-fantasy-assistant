import numpy as np
import polars as pl
import pytest

from dikit.errors import LeakageError
from dikit.methods import shrinkage
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.project import project_pool, residual_sds, with_uncertainty
from fantasy_models.preseason.schema import (
    PER_GAME_STATS,
    assert_no_future,
    history_before,
    season_of,
    start_year,
)
from fantasy_models.preseason.synthetic import TRUE_RATES, make_league

SEASONS, DRAFT = make_league()
TARGET = "2025-26"
HIST = history_before(SEASONS, TARGET)


# ---------------------------------------------------------------- leakage (AC3)
@pytest.mark.parametrize(
    "fn",
    [m.last_season, m.marcel, m.empirical_bayes, m.window, m.league_rates, m.fit_eb],
)
def test_no_future_seasons(fn: object) -> None:
    with pytest.raises(LeakageError, match="2025-26"):
        fn(SEASONS, TARGET)  # type: ignore[operator]


def test_no_future_seasons_in_rookie_priors_and_pool() -> None:
    with pytest.raises(LeakageError):
        m.rookie_priors(SEASONS, DRAFT, TARGET)
    # project_pool filters history itself, so the full frame is safe to pass
    pool = DRAFT.select("nba_player_id", "overall_pick")
    out = project_pool(SEASONS, DRAFT, pool, TARGET, m.marcel)
    assert out.height == pool.height


def test_assert_no_future_allows_earlier_seasons() -> None:
    assert_no_future(HIST, TARGET)


def test_season_helpers() -> None:
    assert start_year("2025-26") == 2025
    assert season_of(1999) == "1999-00"
    with pytest.raises(ValueError, match="season"):
        start_year("2025")


# ---------------------------------------------------------------- window + baselines
def test_window_uses_only_the_three_prior_seasons_with_recency_weights() -> None:
    w = m.window(HIST, TARGET)
    pid = HIST.filter(pl.col("season") == "2024-25").get_column("nba_player_id")[0]
    rows = HIST.filter(
        (pl.col("nba_player_id") == pid) & pl.col("season").is_in(["2024-25", "2023-24", "2022-23"])
    )
    weights = {"2024-25": 1.0, "2023-24": 0.8, "2022-23": 0.6}
    expected = sum(r["minutes"] * weights[r["season"]] for r in rows.iter_rows(named=True))
    got = w.filter(pl.col("nba_player_id") == pid).get_column("w_minutes")[0]
    assert got == pytest.approx(expected)


def test_last_season_is_previous_season_per_game() -> None:
    b0 = m.last_season(HIST, TARGET)
    row = HIST.filter(pl.col("season") == "2024-25").row(0, named=True)
    got = b0.filter(pl.col("nba_player_id") == row["nba_player_id"]).row(0, named=True)
    assert got["pts"] == pytest.approx(row["pts"] / row["games_played"])
    assert got["games"] == row["games_played"]


def test_marcel_regresses_low_minute_players_to_the_league_rate() -> None:
    lg = m.league_rates(HIST, TARGET)
    tiny = pl.DataFrame(
        [
            {
                **HIST.row(0, named=True),
                "season": "2024-25",
                "nba_player_id": 1,
                "minutes": 5.0,
                "games_played": 1,
                "reb": 5,
                "age": 29.0,
            }
        ]
    )
    b1 = m.marcel(pl.concat([HIST, tiny]), TARGET)
    r = b1.filter(pl.col("nba_player_id") == 1).row(0, named=True)
    # 5 rebounds in 5 minutes (1.0/min) is pulled almost all the way to the league rate
    assert r["reb"] / r["mpg"] == pytest.approx(lg["reb"], rel=0.05)


def test_marcel_age_factor_direction() -> None:
    f = pl.select(
        m.marcel_age_factor(pl.lit(23.0)).alias("y"), m.marcel_age_factor(pl.lit(35.0)).alias("o")
    )
    assert f["y"][0] > 1 > f["o"][0]


# ---------------------------------------------------------------- EB
def test_rate_prior_recovers_known_spread() -> None:
    rng = np.random.default_rng(1)
    mu, shape = 0.2, 8.0
    true = rng.gamma(shape, mu / shape, 4000)
    exposure = rng.uniform(200, 2500, 4000)
    prior = shrinkage.fit_rate_prior(rng.poisson(true * exposure), exposure)
    assert prior.mu == pytest.approx(mu, rel=0.03)
    assert prior.k == pytest.approx(mu / (mu**2 / shape), rel=0.15)  # k = mu / tau^2 = shape / mu


def test_pct_prior_recovers_known_spread() -> None:
    rng = np.random.default_rng(2)
    p_true = rng.beta(0.78 * 60, 0.22 * 60, 4000)
    att = rng.integers(20, 600, 4000)
    prior = shrinkage.fit_pct_prior(rng.binomial(att, p_true), att)
    assert prior.p == pytest.approx(0.78, abs=0.01)
    assert prior.k == pytest.approx(60, rel=0.2)


def test_priors_never_degenerate() -> None:
    same = shrinkage.fit_rate_prior(np.array([10, 10, 10]), np.array([100, 100, 100]))
    assert np.isfinite(same.k)
    assert same.k > 0


def test_eb_shrinks_more_with_fewer_minutes() -> None:
    lg = m.fit_eb(HIST, TARGET).rates["blk"].mu
    base = {**HIST.row(0, named=True), "season": "2024-25", "age": 27.0, "blk": 0}
    small = pl.DataFrame(
        [{**base, "nba_player_id": 1, "minutes": 50.0, "games_played": 5, "blk": 5}]
    )
    big = pl.DataFrame(
        [{**base, "nba_player_id": 2, "minutes": 2500.0, "games_played": 80, "blk": 250}]
    )
    c1 = m.empirical_bayes(pl.concat([HIST, small, big]), TARGET)
    r = {
        row["nba_player_id"]: row["blk"] / row["mpg"]
        for row in c1.filter(pl.col("nba_player_id") < 3).iter_rows(named=True)
    }
    # both observed 0.1 blk/min; the 50-minute player is pulled much closer to the prior mean
    assert abs(r[1] - lg) < abs(r[2] - lg)
    assert r[2] == pytest.approx(0.1, rel=0.2)


def test_eb_beats_raw_rates_on_synthetic_truth() -> None:
    """With known true rates, EB-shrunk rates have lower error than raw last-season rates."""
    c1 = m.empirical_bayes(HIST, TARGET)
    b0 = m.last_season(HIST, TARGET)
    actual = SEASONS.filter(pl.col("season") == TARGET)
    joined = (
        actual.select("nba_player_id", (pl.col("stl") / pl.col("minutes")).alias("true_rate"))
        .join(
            c1.select("nba_player_id", (pl.col("stl") / pl.col("mpg")).alias("c1")),
            on="nba_player_id",
        )
        .join(
            b0.select("nba_player_id", (pl.col("stl") / pl.col("mpg")).alias("b0")),
            on="nba_player_id",
        )
    )

    def err(col: str) -> float:
        diff = (joined.get_column(col) - joined.get_column("true_rate")).abs()
        return float(diff.mean())  # type: ignore[arg-type]

    assert err("c1") < err("b0")


def test_aging_fit_finds_decline_after_peak() -> None:
    coefs = m.fit_aging(HIST, ("reb",))
    a, b, c = coefs["reb"]

    def step(age: float) -> float:
        return float(a * age**2 + b * age + c)

    assert step(22) > step(34)


def test_aging_needs_enough_pairs() -> None:
    assert m.fit_aging(HIST.head(10), ("reb",)) == {}


def test_eb_with_aging_runs() -> None:
    pri = m.fit_eb(HIST, TARGET, aging=True)
    assert "reb" in pri.aging
    out = m.empirical_bayes(HIST, TARGET, priors=pri)
    assert out.height > 0


# ---------------------------------------------------------------- rookies + pool
def test_rookie_priors_by_bucket() -> None:
    pri = m.rookie_priors(HIST, DRAFT, TARGET)
    assert pri.get_column("n_rookies").sum() > 0
    assert set(pri.get_column("bucket")) <= {b for *_, b in m.PICK_BUCKETS} | {m.OTHER_BUCKET}


def test_projection_schema() -> None:
    """AC1: every pool player gets a mean and sd per stat; makes <= attempts; pts identity."""
    pool = DRAFT.select("nba_player_id", "overall_pick")
    proj = project_pool(SEASONS, DRAFT, pool, TARGET, m.empirical_bayes)
    assert proj.get_column("nba_player_id").n_unique() == pool.height
    assert set(proj.get_column("source")) <= {"history", "rookie_prior"}
    for mk, att in (("fgm", "fga"), ("fg3m", "fg3a"), ("ftm", "fta")):
        assert (proj.get_column(mk) <= proj.get_column(att) + 1e-9).all()
    pts = 2 * proj.get_column("fgm") + proj.get_column("fg3m") + proj.get_column("ftm")
    assert np.allclose(proj.get_column("pts").to_numpy(), pts.to_numpy())

    actual = SEASONS.filter(pl.col("season") == TARGET).select(
        "nba_player_id",
        (pl.col("minutes") / pl.col("games_played")).alias("mpg"),
        pl.col("games_played").cast(pl.Float64).alias("games"),
        *[(pl.col(s) / pl.col("games_played")).alias(s) for s in PER_GAME_STATS],
    )
    sds = residual_sds(proj, actual)
    long = with_uncertainty(proj, sds)
    assert long.filter(pl.col("sd").is_null()).height == 0
    assert (long.get_column("sd") > 0).all()
    assert long.group_by("nba_player_id").len().get_column("len").unique().to_list() == [
        len(PER_GAME_STATS) + 2
    ]
    rookie = long.filter(pl.col("source") == "rookie_prior")
    if rookie.height:
        assert float(rookie.get_column("sd").min()) > 0  # type: ignore[arg-type]


def test_true_rates_fixture_sanity() -> None:
    lg = m.league_rates(HIST, TARGET)
    assert lg["fga"] == pytest.approx(TRUE_RATES["fga"], rel=0.25)


def test_hybrid_uses_last_season_minutes_with_window_fallback() -> None:
    """H1 (G-21b / D-51): EB per-minute rates x last season's mpg x Marcel games."""
    h1 = m.hybrid(HIST, TARGET)
    c1 = m.empirical_bayes(HIST, TARGET)
    b0 = m.last_season(HIST, TARGET)
    both = h1.join(b0.select("nba_player_id", pl.col("mpg").alias("mpg_b0")), on="nba_player_id")
    assert np.allclose(both.get_column("mpg").to_numpy(), both.get_column("mpg_b0").to_numpy())
    # same per-minute rates as C1
    j = h1.join(c1, on="nba_player_id", suffix="_c1")
    assert np.allclose((j["reb"] / j["mpg"]).to_numpy(), (j["reb_c1"] / j["mpg_c1"]).to_numpy())
    # a player who skipped last season falls back to the window mpg
    skipped = set(h1.get_column("nba_player_id")) - set(b0.get_column("nba_player_id"))
    if skipped:
        pid = next(iter(skipped))
        assert h1.filter(pl.col("nba_player_id") == pid)["mpg"][0] == pytest.approx(
            c1.filter(pl.col("nba_player_id") == pid)["mpg"][0]
        )


def test_old_draft_picks_do_not_count_as_rookie_priors() -> None:
    """A returning veteran drafted years ago (e.g. #5 in 2015) is not a top-5 rookie."""
    draft = pl.concat(
        [
            DRAFT,
            pl.DataFrame(
                {"nba_player_id": [7001, 7002], "draft_year": [2015, 2025], "overall_pick": [5, 5]}
            ),
        ]
    )
    picks = m.this_draft_pick(pl.DataFrame({"nba_player_id": [7001, 7002]}), draft, TARGET)
    got = dict(zip(picks["nba_player_id"], picks["overall_pick"], strict=True))
    assert got == {7001: None, 7002: 5}
    pool = pl.DataFrame({"nba_player_id": [7001, 7002], "overall_pick": [5, 5]})
    proj = project_pool(SEASONS, draft, pool, TARGET, m.hybrid)
    by = {r["nba_player_id"]: r["mpg"] for r in proj.iter_rows(named=True)}
    assert by[7001] != by[7002]  # different buckets -> different priors


def test_hybrid_aging_adjusts_rates_by_age() -> None:
    plain = m.hybrid(HIST, TARGET)
    aged = m.hybrid_aging(HIST, TARGET)
    j = plain.join(aged, on="nba_player_id", suffix="_aged")
    assert np.allclose(j["mpg"].to_numpy(), j["mpg_aged"].to_numpy())  # minutes unchanged
    assert not np.allclose(j["reb"].to_numpy(), j["reb_aged"].to_numpy())  # rates age-adjusted


# ------------------------------------------------------------------ DRAFT-012: three-season games
def test_three_season_games_uses_the_preregistered_weights() -> None:
    w = pl.DataFrame({"gp_frac_1": [0.44, 1.0], "gp_frac_2": [0.82, 1.0], "gp_frac_3": [0.89, 1.0]})
    two = w.select(m.expected_games(w))["games"].to_list()
    three = w.select(m.expected_games(w, three_season=True))["games"].to_list()
    assert two[0] == pytest.approx((0.5 * 0.44 + 0.1 * 0.82 + 0.25) * 82)
    assert three[0] == pytest.approx((0.35 * 0.44 + 0.25 * 0.82 + 0.15 * 0.89 + 0.25) * 82)
    assert three[1] == pytest.approx(82.0)  # a fully healthy player is capped at the season
