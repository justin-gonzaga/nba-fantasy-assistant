"""Preseason projection methods (ml-methodology-plan §1, approved G-21 / D-49).

- B0: last season per game (naive baseline [R-52]).
- B1: Marcel [R-13] (practitioner): 5/4/3 recency weights, regression to the league mean,
  Marcel age factor.
- C1: empirical Bayes [R-11, R-12]: a Gamma-Poisson prior per per-minute stat and a
  Beta-Binomial prior per shooting %, both estimated from our data by the method of moments.
  Per-stat prior strength = how reliable the stat is at a given sample size [R-75] (U5).
  Optional aging from our data (U6), by delta method with harmonic-mean minute weights;
  kept only if the backtest ablation supports it.

Every method returns one row per player: nba_player_id, mpg, games, and per-game PER_GAME_STATS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import polars as pl

from dikit.methods.shrinkage import PctPrior, RatePrior, fit_pct_prior, fit_rate_prior
from fantasy_models.preseason import returners as returners_mod
from fantasy_models.preseason.schema import (
    PCT_STATS,
    PER_GAME_STATS,
    RATE_STATS,
    assert_no_future,
    season_of,
    start_year,
)

RECENCY_WEIGHTS = (1.0, 0.8, 0.6)  # Marcel 5/4/3, normalised so the latest season counts once
MARCEL_REGRESSION_MINUTES = (
    1000.0  # fixed a priori (Marcel regresses a fixed amount of playing time)
)
MARCEL_PEAK_AGE = 29.0
SEASON_GAMES = 82
LAST_SEASON, SEASON_BEFORE_LAST = 1, 2  # window lags


# ---------------------------------------------------------------- shared window aggregation
def window(history: pl.DataFrame, target: str) -> pl.DataFrame:
    """Recency-weighted sums over the three seasons before `target`, one row per player."""
    assert_no_future(history, target)
    t = start_year(target)
    weights = pl.DataFrame(
        {
            "season": [season_of(t - k) for k in (1, 2, 3)],
            "w": list(RECENCY_WEIGHTS),
            "lag": [1, 2, 3],
        }
    )
    counts = ["minutes", "games_played", *RATE_STATS, *(m for m, _ in PCT_STATS.values())]
    df = history.join(weights, on="season", how="inner").with_columns(
        (pl.col("games_played") / pl.col("season_team_games")).alias("gp_frac")
    )
    return df.group_by("nba_player_id").agg(
        *[(pl.col(c) * pl.col("w")).sum().alias(f"w_{c}") for c in counts],
        pl.col("gp_frac")
        .filter(pl.col("lag") == LAST_SEASON)
        .first()
        .fill_null(0.0)
        .alias("gp_frac_1"),
        pl.col("gp_frac")
        .filter(pl.col("lag") == SEASON_BEFORE_LAST)
        .first()
        .fill_null(0.0)
        .alias("gp_frac_2"),
        pl.col("gp_frac")
        .filter(pl.col("lag") == 3)  # noqa: PLR2004 - the third season back
        .first()
        .fill_null(0.0)
        .alias("gp_frac_3"),
        (pl.col("age").sort_by("lag").first() + pl.col("lag").sort_by("lag").first()).alias(
            "target_age"
        ),
        pl.col("lag").min().alias("latest_lag"),
        (pl.col("minutes") / pl.col("games_played"))
        .filter(pl.col("lag") == LAST_SEASON)
        .first()
        .alias("mpg_last"),
    )


def league_rates(history: pl.DataFrame, target: str) -> dict[str, float]:
    """Minutes-weighted league per-minute rates over the same three seasons."""
    assert_no_future(history, target)
    t = start_year(target)
    df = history.filter(pl.col("season").is_in([season_of(t - k) for k in (1, 2, 3)]))
    mins = float(df.get_column("minutes").sum())
    stats = [*RATE_STATS, *(m for m, _ in PCT_STATS.values())]
    return {s: float(df.get_column(s).sum()) / mins for s in stats}


def expected_games(
    w: pl.DataFrame, season_games: int = SEASON_GAMES, *, three_season: bool = False
) -> pl.Expr:
    """Marcel-style playing time: 0.5·last + 0.1·previous + a constant, as a share of the season.

    `three_season` (DRAFT-012, pre-registered): 0.35·last + 0.25·previous + 0.15·third + 0.25, so
    one short season moves the forecast less."""
    if three_season:
        hist = 0.35 * pl.col("gp_frac_1") + 0.25 * pl.col("gp_frac_2") + 0.15 * pl.col("gp_frac_3")
    else:
        hist = 0.5 * pl.col("gp_frac_1") + 0.1 * pl.col("gp_frac_2")
    frac = (hist + 0.25).clip(0.0, 1.0)
    return (frac * season_games).alias("games")


def _finish(
    df: pl.DataFrame, rate_cols: dict[str, str], pct_cols: dict[str, str] | None
) -> pl.DataFrame:
    """Turn per-minute rates (+ optional shooting %) and mpg into per-game stats."""
    out = df.with_columns([(pl.col(rc) * pl.col("mpg")).alias(s) for s, rc in rate_cols.items()])
    if pct_cols is not None:
        out = out.with_columns(
            [
                (pl.col(att) * pl.col(pc)).alias(mk)
                for pc_name, pc in pct_cols.items()
                for mk, att in [PCT_STATS[pc_name]]
            ]
        )
    out = out.with_columns((2 * pl.col("fgm") + pl.col("fg3m") + pl.col("ftm")).alias("pts"))
    return out.select("nba_player_id", "mpg", "games", *PER_GAME_STATS)


# ---------------------------------------------------------------- B0
def last_season(history: pl.DataFrame, target: str) -> pl.DataFrame:
    assert_no_future(history, target)
    prev = season_of(start_year(target) - 1)
    df = history.filter(pl.col("season") == prev)
    gp = pl.col("games_played")
    return df.select(
        "nba_player_id",
        (pl.col("minutes") / gp).alias("mpg"),
        gp.cast(pl.Float64).alias("games"),
        *[(pl.col(s) / gp).alias(s) for s in PER_GAME_STATS],
    )


# ---------------------------------------------------------------- B1 Marcel
def marcel_age_factor(age: pl.Expr) -> pl.Expr:
    return (
        pl.when(age < MARCEL_PEAK_AGE)
        .then(1 + 0.006 * (MARCEL_PEAK_AGE - age))
        .otherwise(1 - 0.003 * (age - MARCEL_PEAK_AGE))
    )


def marcel(history: pl.DataFrame, target: str, season_games: int = SEASON_GAMES) -> pl.DataFrame:
    w = window(history, target)
    lg = league_rates(history, target)
    k = MARCEL_REGRESSION_MINUTES
    makes = {m: m for m, _ in PCT_STATS.values()}
    stats = {**{s: s for s in RATE_STATS}, **makes}
    age = marcel_age_factor(pl.col("target_age").fill_null(MARCEL_PEAK_AGE))
    df = w.with_columns(
        *[
            ((pl.col(f"w_{s}") + k * lg[s]) / (pl.col("w_minutes") + k) * age).alias(f"r_{s}")
            for s in stats
        ],
        (pl.col("w_minutes") / pl.col("w_games_played")).alias("mpg"),
        expected_games(w, season_games),
    )
    return _finish(df, {s: f"r_{s}" for s in stats}, None)


# ---------------------------------------------------------------- C1 empirical Bayes


@dataclass(frozen=True)
class EBPriors:
    rates: dict[str, RatePrior]
    pcts: dict[str, PctPrior]
    aging: dict[str, np.ndarray] = field(default_factory=dict)  # stat -> quadratic coefs in age


def fit_aging(
    history: pl.DataFrame, stats: tuple[str, ...], min_minutes: float = 200.0
) -> dict[str, np.ndarray]:
    """Per-stat age effect: weighted quadratic fit of log(rate_{t+1}/rate_t) on age at t.

    Delta method with harmonic-mean minute weights; survivor bias [R-71] is a known limitation,
    so the backtest ablation decides whether this term is used (U6).
    """
    df = history.filter(pl.col("minutes") >= min_minutes).with_columns(
        pl.col("season").map_elements(start_year, return_dtype=pl.Int64).alias("y")
    )
    nxt = df.with_columns((pl.col("y") - 1).alias("y"))
    pairs = df.join(nxt, on=["nba_player_id", "y"], suffix="_next")
    coefs: dict[str, np.ndarray] = {}
    if pairs.height < 30:  # noqa: PLR2004
        return coefs
    m1, m2 = pairs.get_column("minutes").to_numpy(), pairs.get_column("minutes_next").to_numpy()
    wts = 2 / (1 / m1 + 1 / m2)
    age = pairs.get_column("age").to_numpy()
    for s in stats:
        r1 = pairs.get_column(s).to_numpy() / m1
        r2 = pairs.get_column(f"{s}_next").to_numpy() / m2
        ok = (r1 > 0) & (r2 > 0)
        if ok.sum() < 30:  # noqa: PLR2004
            continue
        coefs[s] = np.polyfit(age[ok], np.log(r2[ok] / r1[ok]), 2, w=np.sqrt(wts[ok]))
    return coefs


def fit_eb(history: pl.DataFrame, target: str, n_seasons: int = 5, aging: bool = False) -> EBPriors:
    """Fit the EB priors on the `n_seasons` seasons before `target` (never later ones)."""
    assert_no_future(history, target)
    t = start_year(target)
    df = history.filter(pl.col("season").is_in([season_of(t - k) for k in range(1, n_seasons + 1)]))
    mins = df.get_column("minutes").to_numpy()
    rates = {s: fit_rate_prior(df.get_column(s).to_numpy(), mins) for s in RATE_STATS}
    pcts = {
        name: fit_pct_prior(df.get_column(mk).to_numpy(), df.get_column(att).to_numpy())
        for name, (mk, att) in PCT_STATS.items()
    }
    ages = fit_aging(df, RATE_STATS) if aging else {}
    return EBPriors(rates=rates, pcts=pcts, aging=ages)


def _age_step(coefs: np.ndarray | None, age: pl.Expr) -> pl.Expr:
    if coefs is None:
        return pl.lit(1.0)
    a, b, c = (float(v) for v in coefs)
    return (a * age.pow(2) + b * age + c).exp()


def empirical_bayes(  # noqa: PLR0913 - keyword-only options
    history: pl.DataFrame,
    target: str,
    priors: EBPriors | None = None,
    season_games: int = SEASON_GAMES,
    *,
    last_season_minutes: bool = False,
    mpg_override: pl.DataFrame | None = None,
    three_season_games: bool = False,
    returners: bool = False,
) -> pl.DataFrame:
    w = window(history, target)
    if mpg_override is not None:  # DRAFT-007 M1 minutes: nba_player_id, mpg_m1
        w = w.join(mpg_override.select("nba_player_id", "mpg_m1"), on="nba_player_id", how="left")
    pr = priors or fit_eb(history, target)
    window_mpg = pl.col("w_minutes") / pl.col("w_games_played")
    mpg = pl.coalesce("mpg_last", window_mpg) if last_season_minutes else window_mpg
    if mpg_override is not None:
        mpg = pl.coalesce("mpg_m1", mpg)
    age = pl.col("target_age").fill_null(27.0) - 1  # age at the latest observed season
    df = w.with_columns(
        *[
            (
                (pl.col(f"w_{s}") + pr.rates[s].k * pr.rates[s].mu)
                / (pl.col("w_minutes") + pr.rates[s].k)
                * _age_step(pr.aging.get(s), age)
            ).alias(f"r_{s}")
            for s in RATE_STATS
        ],
        *[
            (
                (pl.col(f"w_{mk}") + pr.pcts[name].k * pr.pcts[name].p)
                / (pl.col(f"w_{att}") + pr.pcts[name].k)
            ).alias(name)
            for name, (mk, att) in PCT_STATS.items()
        ],
        mpg.alias("mpg"),
        expected_games(w, season_games, three_season=three_season_games),
    )
    if returners:  # DRAFT-022 variant R: raise-only games floor for the lost-season cohort
        floor = returners_mod.floors(history, target, season_games)
        if floor is not None:
            df = (
                df.join(floor, on="nba_player_id", how="left")
                .with_columns(pl.max_horizontal("games", "games_floor").alias("games"))
                .drop("games_floor")
            )
    return _finish(df, {s: f"r_{s}" for s in RATE_STATS}, {n: n for n in PCT_STATS})


def hybrid(  # noqa: PLR0913 - keyword-only options
    history: pl.DataFrame,
    target: str,
    season_games: int = SEASON_GAMES,
    *,
    aging: bool = False,
    mpg_override: pl.DataFrame | None = None,
    three_season_games: bool = False,
    returners: bool = False,
) -> pl.DataFrame:
    """H1 (G-21b / D-51): C1 per-minute rates x last season's minutes per game x Marcel games.

    The backtest showed the 3-year weighted mpg is the weak component (last season's mpg
    predicts better); players who skipped last season fall back to the window mpg.
    """
    priors = fit_eb(history, target, aging=aging)
    return empirical_bayes(
        history,
        target,
        priors=priors,
        season_games=season_games,
        last_season_minutes=True,
        mpg_override=mpg_override,
        three_season_games=three_season_games,
        returners=returners,
    )


def hybrid_aging(
    history: pl.DataFrame, target: str, season_games: int = SEASON_GAMES
) -> pl.DataFrame:
    """H1+aging (D-52): H1 with the per-stat age curve estimated from our data [R-70, R-71]."""
    return hybrid(history, target, season_games, aging=True)


# ---------------------------------------------------------------- rookies / no history
PICK_BUCKETS = (
    (1, 5, "picks_1_5"),
    (6, 14, "picks_6_14"),
    (15, 30, "picks_15_30"),
    (31, 60, "picks_31_60"),
)
OTHER_BUCKET = "undrafted_or_other"


def pick_bucket(overall_pick: pl.Expr) -> pl.Expr:
    expr: Any = pl.when(overall_pick.is_null()).then(pl.lit(OTHER_BUCKET))
    for lo, hi, name in PICK_BUCKETS:
        expr = expr.when(overall_pick.is_between(lo, hi)).then(pl.lit(name))
    result: pl.Expr = expr.otherwise(pl.lit(OTHER_BUCKET))
    return result


def rookie_priors(history: pl.DataFrame, draft: pl.DataFrame, target: str) -> pl.DataFrame:
    """Per-game rookie-season averages by draft-pick bucket.

    Built only from rookie seasons before `target` [R-78].
    """
    assert_no_future(history, target)
    first = history.group_by("nba_player_id").agg(pl.col("season").min().alias("first_season"))
    rk = (
        history.join(first, on="nba_player_id")
        .filter(pl.col("season") == pl.col("first_season"))
        .with_columns(pl.col("season").map_elements(start_year, return_dtype=pl.Int64).alias("y"))
        .join(
            draft.select("nba_player_id", "draft_year", "overall_pick"),
            on="nba_player_id",
            how="left",
        )
        .with_columns(
            pick_bucket(
                pl.when(pl.col("draft_year") == pl.col("y")).then(pl.col("overall_pick"))
            ).alias("bucket")
        )
    )
    agg = [pl.col(c).sum() for c in ("minutes", "games_played", *PER_GAME_STATS)]
    per = rk.group_by("bucket").agg(
        *agg,
        (pl.col("games_played") / pl.col("season_team_games")).mean().alias("gp_frac"),
        pl.len().alias("n_rookies"),
    )
    gp = pl.col("games_played")
    return per.select(
        "bucket",
        "n_rookies",
        (pl.col("minutes") / gp).alias("mpg"),
        (pl.col("gp_frac") * SEASON_GAMES).alias("games"),
        *[(pl.col(s) / gp).alias(s) for s in PER_GAME_STATS],
    )


def this_draft_pick(players: pl.DataFrame, draft: pl.DataFrame, target: str) -> pl.DataFrame:
    """nba_player_id + overall_pick from the draft held just before `target` (else null).

    Only a pick in this year's draft identifies a rookie; an old pick (a veteran returning
    from overseas, say) must not borrow a lottery-pick prior.
    """
    year = start_year(target)
    picks = (
        draft.filter(pl.col("draft_year") == year)
        .select("nba_player_id", "overall_pick")
        .unique("nba_player_id")
    )
    return players.select("nba_player_id").join(picks, on="nba_player_id", how="left")


def rookie_projection(
    players: pl.DataFrame, priors: pl.DataFrame, season_games: int = SEASON_GAMES
) -> pl.DataFrame:
    """Players without history get their bucket's rookie averages.

    `players` has nba_player_id and overall_pick.
    """
    out = players.with_columns(pick_bucket(pl.col("overall_pick")).alias("bucket")).join(
        priors, on="bucket", how="left"
    )
    return out.select(
        "nba_player_id",
        "mpg",
        (pl.col("games") * season_games / SEASON_GAMES).alias("games"),
        *PER_GAME_STATS,
    )
