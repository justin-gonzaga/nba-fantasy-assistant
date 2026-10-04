"""DRAFT-003 job: league-aware auction values for the draft pool (all punt variants)."""

from __future__ import annotations

import numpy as np
import polars as pl

from fantasy_core.league import LeagueRules
from fantasy_models import valuation
from fantasy_models.preseason.project import project_pool
from fantasy_models.preseason.schema import season_of, start_year
from fantasy_pipeline.draft_projection import _inputs, adjustments, resolve_method, with_overrides
from fantasy_pipeline.warehouse import Warehouse

WEEKLY_SQL = """
select
  nba_player_id,
  date_trunc(game_date, week(monday)) as week,
  sum(minutes) as minutes,
  sum(fgm) as fgm, sum(fga) as fga, sum(fg3m) as fg3m, sum(fg3a) as fg3a,
  sum(ftm) as ftm, sum(fta) as fta, sum(reb) as reb, sum(ast) as ast,
  sum(stl) as stl, sum(blk) as blk, sum(tov) as tov, sum(pts) as pts
from staging.stg_nba_stats__player_game
where season = '{season}'
group by 1, 2
"""
POSITIONS_SQL = (
    "select nba_player_id, player_name, nba_position from intermediate.int_player_profile"
)
MIN_WEEKS = 10


def within_week_variance(
    weekly: pl.DataFrame, rules: LeagueRules, pool_size: int
) -> dict[str, float]:
    """Average week-to-week variance per category over the players with the most minutes [R-01].

    Ratio categories use the weekly volume-weighted impact (makes - league% x attempts).
    """
    top = (
        weekly.group_by("nba_player_id")
        .agg(pl.col("minutes").sum(), pl.len().alias("weeks"))
        .filter(pl.col("weeks") >= MIN_WEEKS)
        .sort("minutes", descending=True)
        .head(pool_size)
        .select("nba_player_id")
    )
    df = weekly.join(top, on="nba_player_id", how="semi")
    out = {}
    for cat in rules.categories:
        if cat.attempts:
            p = float(df.get_column(cat.stat).sum()) / float(df.get_column(cat.attempts).sum())
            x = pl.col(cat.stat) - p * pl.col(cat.attempts)
        else:
            x = pl.col(cat.stat).cast(pl.Float64)
        per_player = df.group_by("nba_player_id").agg(x.var().alias("v"))
        out[cat.code] = float(np.nanmean(per_player.get_column("v").to_numpy()))
    return out


HEALTHY_GAMES = 72.0  # WEB-019: everyone at the same games, so the rank is per-game quality


def project(wh: Warehouse, rules: LeagueRules, target: str, method: str) -> pl.DataFrame:
    """The per-game projection (with games) for every listed player."""
    del rules  # the projection doesn't depend on the league; kept for a uniform signature
    seasons, draft = _inputs(wh)
    positions = wh.read(POSITIONS_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
    pool = positions.select("nba_player_id", pl.lit(None, pl.Int64).alias("overall_pick"))
    fn = resolve_method(wh, seasons, method, target)
    return with_overrides(wh, project_pool(seasons, draft, pool, target, fn)).drop(
        "source", "mpg_band"
    )


def healthy_ranks(
    proj: pl.DataFrame, positions: pl.DataFrame, rules: LeagueRules, within: dict[str, float]
) -> pl.DataFrame:
    """WEB-019: the same valuation with every player at HEALTHY_GAMES (rank + $ per variant)."""
    healthy = proj.with_columns(pl.lit(HEALTHY_GAMES).alias("games"))
    pos = positions.select(pl.col("nba_player_id").cast(pl.Int64), "nba_position")
    return valuation.value_all(healthy, pos, rules, within).select(
        "nba_player_id",
        "variant",
        pl.col("overall_rank").alias("healthy_rank"),
        pl.col("dollars").alias("healthy_dollars"),
    )


def build_values(
    wh: Warehouse, rules: LeagueRules, target: str, method: str, *, fill: bool = False
) -> pl.DataFrame:
    positions = wh.read(POSITIONS_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
    proj = project(wh, rules, target, method)
    within: dict[str, float] = {}
    if rules.scoring.uses_categories:
        last = season_of(start_year(target) - 1)
        within = within_week_variance(
            wh.read(WEEKLY_SQL.format(season=last)), rules, rules.pool_size
        )
    values = valuation.value_all(
        proj, positions.select("nba_player_id", "nba_position"), rules, within, fill=fill
    ).join(
        healthy_ranks(proj, positions, rules, within), on=["nba_player_id", "variant"], how="left"
    )
    values = values.join(adjustments(wh), on="nba_player_id", how="left")  # DATA-036
    stamp = f"{method}+repl-fill" if fill else method  # DRAFT-011
    return values.join(
        positions.select("nba_player_id", "player_name"), on="nba_player_id", how="left"
    ).with_columns(pl.lit(target).alias("season"), pl.lit(stamp).alias("method"))
