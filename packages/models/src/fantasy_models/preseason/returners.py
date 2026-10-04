"""Games fraction for players returning after a lost season (DRAFT-022, ml-methodology-plan §25).

Cohort: last season under 25 % of team games (no row counts as 0), the season before at least
60 % with 22+ mpg. Variant R lifts a cohort player's games forecast to the mean games fraction
that earlier cohorts realised, never lowers it. Frozen before any run; nothing here is tuned.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from fantasy_models.preseason.schema import (
    assert_no_future,
    history_before,
    season_of,
    start_year,
)

LOST_BELOW = 0.25
ROTATION_AT_LEAST = 0.6
ROTATION_MPG = 22.0
MIN_ROWS = 30


@dataclass(frozen=True)
class BaseRate:
    rate: float
    n: int


def cohort(history: pl.DataFrame, target: str) -> pl.DataFrame:
    """Cohort players for `target`: nba_player_id, gp_frac_1, gp_frac_2, mpg_2."""
    assert_no_future(history, target)
    t = start_year(target)
    frac = pl.col("games_played") / pl.col("season_team_games")
    two_back = (
        history.filter(pl.col("season") == season_of(t - 2))
        .select(
            "nba_player_id",
            frac.alias("gp_frac_2"),
            (pl.col("minutes") / pl.col("games_played")).alias("mpg_2"),
        )
        .filter((pl.col("gp_frac_2") >= ROTATION_AT_LEAST) & (pl.col("mpg_2") >= ROTATION_MPG))
    )
    last = history.filter(pl.col("season") == season_of(t - 1)).select(
        "nba_player_id", frac.alias("gp_frac_1")
    )
    return (
        two_back.join(last, on="nba_player_id", how="left")
        .with_columns(pl.col("gp_frac_1").fill_null(0.0))
        .filter(pl.col("gp_frac_1") < LOST_BELOW)
        .select("nba_player_id", "gp_frac_1", "gp_frac_2", "mpg_2")
        .sort("nba_player_id")
    )


def realised(history: pl.DataFrame, season: str) -> pl.DataFrame:
    """Cohort players of `season` who played at least one game in it: nba_player_id, games_frac.

    `history` may hold `season` itself (this is the evaluation view); the cohort is built from
    earlier seasons only."""
    members = cohort(history_before(history, season), season).select("nba_player_id")
    played = history.filter((pl.col("season") == season) & (pl.col("games_played") > 0)).select(
        "nba_player_id",
        (pl.col("games_played") / pl.col("season_team_games")).alias("games_frac"),
    )
    return members.join(played, on="nba_player_id", how="inner").sort("nba_player_id")


def base_rate(history: pl.DataFrame, target: str) -> BaseRate | None:
    """Mean realised games fraction of returners in the seasons before `target`, or None when
    fewer than MIN_ROWS such rows exist."""
    assert_no_future(history, target)
    seasons = sorted(history.get_column("season").unique().to_list())
    frames = [realised(history, s) for s in seasons]
    allrows = pl.concat(frames) if frames else pl.DataFrame({"games_frac": []})
    if allrows.height < MIN_ROWS:
        return None
    return BaseRate(rate=float(allrows.get_column("games_frac").mean()), n=allrows.height)  # type: ignore[arg-type]


def floors(history: pl.DataFrame, target: str, season_games: int) -> pl.DataFrame | None:
    """Per cohort player the games floor (base rate x season games), or None when R does nothing."""
    br = base_rate(history, target)
    if br is None:
        return None
    return cohort(history, target).select(
        "nba_player_id", pl.lit(br.rate * season_games).alias("games_floor")
    )
