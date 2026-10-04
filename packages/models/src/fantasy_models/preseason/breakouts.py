"""Pre-season minutes model (M1) and breakout probability (M2).

DRAFT-007, plan Part 1b (G-23 / D-54).

Features use only data from before the target season, plus the target season's opening roster
(the team each player starts the season with; in backtests the first team they played for, U10).
- M1 predicts the change in minutes per game from last season: ridge regression (closed form)
  or LightGBM [R-20, R-21]. Role conditions production [R-84]; trades matter [R-85]; vacated
  usage redistributes unevenly towards efficient players [R-87] (the vacated x talent term).
- M2: L2 logistic regression, class-weighted for the rare breakout class [R-89], with a
  prior correction of the intercept so the probabilities stay calibrated.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from dikit.methods.regression import Regressor
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.schema import assert_no_future, history_before, season_of, start_year

CATS = ("pts", "reb", "ast", "stl", "blk", "fg3m")
INJURY_GP_FRAC = 0.6  # DRAFT-012: below this share of games, last season's mpg isn't trusted
M1_FEATURES = (
    "mpg_last",
    "mpg_window",
    "gp_frac_last",
    "age",
    "age_sq",
    "experience",
    "talent",
    "usage",
    "changed_team",
    "net_vacated_min",
    "net_vacated_usage",
    "vacated_x_talent",
)
M2_FEATURES = (*M1_FEATURES, "value_rank_last", "rank_trajectory", "talent_gap")
# DRAFT-008 (G-24 / D-57): pre-season role, games up to 2 days before opening night only.
PRE_FEATURES = (
    "pre_mpg",
    "pre_mpg_delta",
    "pre_team_minutes_share",
    "pre_start_share",
    "pre_start_missing",
    "pre_games",
)
M1_PRE_FEATURES = (*M1_FEATURES, *PRE_FEATURES)
M2_PRE_FEATURES = (*M2_FEATURES, *PRE_FEATURES)


def add_preseason(feats: pl.DataFrame, pre: pl.DataFrame) -> pl.DataFrame:
    """Join one season's pre-season role (int_preseason_role rows for the target season).

    No pre-season games -> zeros with pre_games = 0. Starts unknown (source quality) ->
    pre_start_missing = 1 and share 0, so the model sees the gap explicitly.
    """
    cols = ["nba_player_id", "pre_games", "pre_mpg", "pre_team_minutes_share", "pre_start_share"]
    j = feats.join(pre.select(cols), on="nba_player_id", how="left")
    return j.with_columns(
        pl.col("pre_games").fill_null(0).cast(pl.Float64),
        pl.col("pre_mpg").fill_null(0.0),
        pl.col("pre_team_minutes_share").fill_null(0.0),
        (pl.col("pre_start_share").is_null() & pl.col("pre_games").is_not_null())
        .cast(pl.Float64)
        .alias("pre_start_missing"),
        pl.col("pre_start_share").fill_null(0.0),
        pl.when(pl.col("pre_games").fill_null(0) > 0)
        .then(pl.col("pre_mpg") - pl.col("mpg_last"))
        .otherwise(0.0)
        .alias("pre_mpg_delta"),
    )


MPG_CAP = 42.0


def rosters_from_season(seasons: pl.DataFrame, target: str) -> pl.DataFrame:
    """Opening-roster proxy for a past season: the first team each player played for (U10)."""
    return seasons.filter(pl.col("season") == target).select(
        "nba_player_id", pl.col("first_nba_team_id").alias("team")
    )


def _zsum(df: pl.DataFrame, per: str | None) -> np.ndarray:
    """9-cat z-sum (TO negative; FG%/FT% as volume-weighted impact), optionally per minute."""
    scale = df.get_column(per).to_numpy() if per else np.ones(df.height)
    scale = np.where(scale > 0, scale, np.nan)
    fg = float(df.get_column("fgm").sum()) / max(float(df.get_column("fga").sum()), 1.0)
    ft = float(df.get_column("ftm").sum()) / max(float(df.get_column("fta").sum()), 1.0)
    cols = [df.get_column(c).to_numpy() / scale for c in CATS]
    cols.append(-df.get_column("tov").to_numpy() / scale)
    cols.append((df.get_column("fgm") - fg * df.get_column("fga")).to_numpy() / scale)
    cols.append((df.get_column("ftm") - ft * df.get_column("fta")).to_numpy() / scale)
    z = [(c - np.nanmean(c)) / (np.nanstd(c) or 1.0) for c in cols]
    return np.nan_to_num(np.sum(z, axis=0))


def season_value_ranks(seasons: pl.DataFrame, season: str) -> pl.DataFrame:
    """Realised season-total 9-cat value rank of everyone who played `season`."""
    df = seasons.filter(pl.col("season") == season)
    return (
        df.select("nba_player_id")
        .with_columns(pl.Series("value", _zsum(df, None)))
        .with_columns(pl.col("value").rank("ordinal", descending=True).cast(pl.Int64).alias("rank"))
    )


def features(
    history: pl.DataFrame, rosters: pl.DataFrame, target: str, *, injury_robust: bool = False
) -> pl.DataFrame:
    """One row per rostered player who played last season. `rosters`: nba_player_id, team.

    `injury_robust` (DRAFT-012, pre-registered): after a short season (< 60 % of team games),
    `mpg_last` is the 3-season window mpg, since injury-return minutes understate the role."""
    assert_no_future(history, target)
    last = season_of(start_year(target) - 1)
    prev = history.filter(pl.col("season") == last)
    w = m.window(history, target)
    usage = (pl.col("fga") + 0.44 * pl.col("fta") + pl.col("tov")) / pl.col("minutes")
    prev_f = prev.select(
        "nba_player_id",
        (pl.col("minutes") / pl.col("games_played")).alias("mpg_last"),
        (pl.col("games_played") / pl.col("season_team_games")).alias("gp_frac_last"),
        pl.col("last_nba_team_id").alias("team_last"),
        pl.col("minutes").alias("min_last"),
        usage.alias("usage"),
        (pl.col("fga") + 0.44 * pl.col("fta") + pl.col("tov")).alias("poss_last"),
    ).with_columns(pl.Series("talent", _zsum(prev, "minutes")))
    exp = history.group_by("nba_player_id").agg(pl.len().alias("experience"))
    ranks = season_value_ranks(history, last).select(
        "nba_player_id", pl.col("rank").alias("value_rank_last")
    )
    before = season_of(start_year(target) - 2)
    ranks2 = (
        season_value_ranks(history, before).select("nba_player_id", pl.col("rank").alias("rank2"))
        if (history.get_column("season") == before).any()
        else pl.DataFrame(schema={"nba_player_id": pl.Int64, "rank2": pl.Int64})
    )
    roster = rosters.select("nba_player_id", pl.col("team").cast(pl.Int64))
    # vacated: last-season minutes of players who ended last season on team T but don't open on it
    moved = prev_f.join(roster, on="nba_player_id", how="left")
    left = (
        moved.filter(pl.col("team").is_null() | (pl.col("team") != pl.col("team_last")))
        .group_by(pl.col("team_last").alias("team"))
        .agg(pl.col("min_last").sum().alias("out_min"), pl.col("poss_last").sum().alias("out_poss"))
    )
    came = (
        moved.filter(pl.col("team").is_not_null() & (pl.col("team") != pl.col("team_last")))
        .group_by("team")
        .agg(pl.col("min_last").sum().alias("in_min"), pl.col("poss_last").sum().alias("in_poss"))
    )
    df = (
        roster.join(prev_f, on="nba_player_id", how="inner")
        .join(
            w.select("nba_player_id", "w_minutes", "w_games_played", "target_age"),
            on="nba_player_id",
            how="left",
        )
        .join(exp, on="nba_player_id", how="left")
        .join(left, on="team", how="left")
        .join(came, on="team", how="left")
        .join(ranks, on="nba_player_id", how="left")
        .join(ranks2, on="nba_player_id", how="left")
        .with_columns(pl.col("talent").rank(descending=True).alias("talent_rank"))
    )
    sd = df.get_column("talent").std()
    talent_sd = float(sd) if isinstance(sd, int | float) and sd else 1.0
    out = (
        df.select(
            "nba_player_id",
            "mpg_last",
            (pl.col("w_minutes") / pl.col("w_games_played")).alias("mpg_window"),
            "gp_frac_last",
            pl.col("target_age").fill_null(27.0).alias("age"),
            (pl.col("target_age").fill_null(27.0) ** 2 / 100).alias("age_sq"),
            pl.col("experience").cast(pl.Float64),
            "talent",
            "usage",
            (pl.col("team") != pl.col("team_last")).cast(pl.Float64).alias("changed_team"),
            ((pl.col("out_min").fill_null(0) - pl.col("in_min").fill_null(0)) / 1000).alias(
                "net_vacated_min"
            ),
            ((pl.col("out_poss").fill_null(0) - pl.col("in_poss").fill_null(0)) / 1000).alias(
                "net_vacated_usage"
            ),
            (
                (pl.col("out_min").fill_null(0) - pl.col("in_min").fill_null(0))
                / 1000
                * pl.col("talent")
                / talent_sd
            ).alias("vacated_x_talent"),
            pl.col("value_rank_last").cast(pl.Float64),
            (pl.col("rank2") - pl.col("value_rank_last"))
            .fill_null(0)
            .cast(pl.Float64)
            .alias("rank_trajectory"),
            (pl.col("value_rank_last") - pl.col("talent_rank"))
            .cast(pl.Float64)
            .alias("talent_gap"),
        )
        .fill_nan(0)
        .fill_null(0)
    )
    if injury_robust:
        out = out.with_columns(
            pl.when(pl.col("gp_frac_last") < INJURY_GP_FRAC)
            .then(pl.col("mpg_window"))
            .otherwise(pl.col("mpg_last"))
            .alias("mpg_last")
        )
    return out


def training_rows(
    seasons: pl.DataFrame,
    targets: list[str],
    min_games: int = 20,
    preseason: pl.DataFrame | None = None,
    *,
    injury_robust: bool = False,
) -> pl.DataFrame:
    """Features for each past target season joined to its realised mpg (the M1 label)."""
    out = []
    for t in targets:
        f = features(
            history_before(seasons, t),
            rosters_from_season(seasons, t),
            t,
            injury_robust=injury_robust,
        )
        if preseason is not None:
            f = add_preseason(f, preseason.filter(pl.col("season") == t))
        y = seasons.filter((pl.col("season") == t) & (pl.col("games_played") >= min_games)).select(
            "nba_player_id", (pl.col("minutes") / pl.col("games_played")).alias("mpg")
        )
        out.append(
            f.join(y, on="nba_player_id", how="inner").with_columns(pl.lit(t).alias("target"))
        )
    return pl.concat(out)


class GBM:
    """LightGBM regressor (native API) with small, fixed hyperparameters chosen a priori."""

    PARAMS: dict[str, Any] = {  # noqa: RUF012
        "objective": "regression",
        "learning_rate": 0.03,
        "num_leaves": 15,
        "min_data_in_leaf": 30,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "feature_fraction": 0.8,
        "seed": 0,
        "verbose": -1,
    }
    ROUNDS = 300

    def __init__(self) -> None:
        self.booster: Any = None

    def fit(self, x: np.ndarray, y: np.ndarray) -> GBM:
        import lightgbm as lgb  # noqa: PLC0415 - heavy import only when used

        self.booster = lgb.train(self.PARAMS, lgb.Dataset(x, label=y), num_boost_round=self.ROUNDS)
        return self

    def predict(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(self.booster.predict(x))


def matrix(df: pl.DataFrame, cols: tuple[str, ...]) -> np.ndarray:
    return df.select(cols).to_numpy().astype(float)


def predict_mpg(
    model: Regressor, train: pl.DataFrame, feats: pl.DataFrame, cols: tuple[str, ...] = M1_FEATURES
) -> pl.DataFrame:
    """Fit on the change in mpg; predict mpg = last + predicted change, capped to [0, MPG_CAP]."""
    y = train.get_column("mpg").to_numpy() - train.get_column("mpg_last").to_numpy()
    model.fit(matrix(train, cols), y)
    pred = feats.get_column("mpg_last").to_numpy() + model.predict(matrix(feats, cols))
    return feats.select("nba_player_id").with_columns(
        pl.Series("mpg_m1", np.clip(pred, 0, MPG_CAP))
    )


# ---------------------------------------------------------------- M2 breakouts
def breakout_labels(
    seasons: pl.DataFrame, target: str, jump: int = 50, top: int = 150
) -> pl.DataFrame:
    """1 if the season-total value rank improved by >= `jump` and finished inside `top`."""
    now = season_value_ranks(seasons, target)
    before = season_value_ranks(seasons, season_of(start_year(target) - 1))
    df = now.join(before, on="nba_player_id", suffix="_last")
    hit = ((pl.col("rank_last") - pl.col("rank")) >= jump) & (pl.col("rank") <= top)
    return df.select("nba_player_id", hit.cast(pl.Int64).alias("breakout"), "rank", "rank_last")
