"""DATA-035: the daily job rebuilds the draft values and the badge inputs and publishes them to the
workspace (the serve bucket in the cloud), so the website's data never needs a manual upload.

A guard compares the rebuild with the live file and refuses to overwrite it when the rebuild looks
broken (a strategy missing, ranks not 1..n, the row count moving > 20 %, or the top 10 reshuffled).
"""

from __future__ import annotations

from collections.abc import Callable

import polars as pl

from fantasy_core.league import LeagueRules
from fantasy_models.preseason import breakouts
from fantasy_models.preseason.breakouts import _zsum
from fantasy_models.preseason.schema import season_of, start_year
from fantasy_pipeline import draft_projection, draft_values
from fantasy_pipeline.warehouse import DRAFT_SQL, SEASONS_SQL, Warehouse
from fantasy_pipeline.workspace import Workspace

__all__ = ["DRAFT_SQL", "SEASONS_SQL"]

VALUES = "predictions/auction_values.parquet"
HISTORY = "predictions/player_history.parquet"
BREAKOUTS = "predictions/breakout_probability.parquet"
CONSISTENCY = "predictions/player_consistency.parquet"  # WEB-020: week-to-week swings
MIN_CONSISTENCY_WEEKS = 15
ROLE = "predictions/role_context.parquet"  # WEB-020: the minutes model's role drivers
TARGET = "2026-27"  # the season being drafted
SHIPPED_METHOD = (
    "H1+aging+M1"  # the method on the live values file (changing it is a reviewed change)
)
BREAKOUT_SQL = (
    "select nba_player_id, kind, p_breakout, season from predictions.breakout_probability "
    "where season = '{season}'"
)
MAX_ROW_CHANGE = 0.2
MIN_TOP10_KEPT = 5

Builder = Callable[..., dict[str, pl.DataFrame]]


class PublishRefusedError(RuntimeError):
    """The rebuild failed a guard; the live files were left as they were."""


PublishRefused = PublishRefusedError


def build(wh: Warehouse, rules: LeagueRules, target: str, method: str) -> dict[str, pl.DataFrame]:
    """The tables to publish (the breakout file only when the warehouse has rows for `target`)."""
    out = {VALUES: draft_values.build_values(wh, rules, target, method)}
    t = start_year(target)
    seasons = [season_of(t - k) for k in (3, 2, 1)]
    hist = wh.read(SEASONS_SQL).filter(pl.col("season").is_in(seasons))
    draft = wh.read(DRAFT_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64),
        pl.col("draft_year").cast(pl.Int64),
        pl.col("overall_pick").cast(pl.Int64),
    )
    seasons_rows = hist.select(
        pl.col("nba_player_id").cast(pl.Int64),
        "season",
        pl.col("games_played").cast(pl.Int64),
        pl.col("season_team_games").cast(pl.Int64),
        pl.col("minutes").cast(pl.Float64),  # season total
        pl.col("age").cast(pl.Float64),  # WEB-020
    ).join(draft.unique("nba_player_id"), on="nba_player_id", how="left")
    # Rookies have no seasons: one row with only the draft facts (WEB-018's contract).
    rookies = (
        draft.filter(pl.col("draft_year") == t)
        .unique("nba_player_id")
        .join(seasons_rows.select("nba_player_id"), on="nba_player_id", how="anti")
        .select(
            "nba_player_id",
            pl.lit(None, pl.String).alias("season"),
            pl.lit(None, pl.Int64).alias("games_played"),
            pl.lit(None, pl.Int64).alias("season_team_games"),
            pl.lit(None, pl.Float64).alias("minutes"),
            pl.lit(None, pl.Float64).alias("age"),
            "draft_year",
            "overall_pick",
        )
    )
    out[HISTORY] = pl.concat([seasons_rows, rookies]).sort(
        "nba_player_id", "season", nulls_last=True
    )
    out[ROLE] = role_context(wh, target)
    last = season_of(t - 1)
    out[CONSISTENCY] = consistency(wh.read(draft_values.WEEKLY_SQL.format(season=last)), last)
    brk = wh.read(BREAKOUT_SQL.format(season=target))
    if brk.height:
        out[BREAKOUTS] = brk.select(
            pl.col("nba_player_id").cast(pl.Int64), "kind", "p_breakout", "season"
        )
    return out


def role_context(wh: Warehouse, target: str) -> pl.DataFrame:
    """WEB-020: per player, whether he changed team and the team minutes freed up (the M1 features
    `changed_team` and `net_vacated_min`, from data known before the target season)."""
    seasons, _ = draft_projection._inputs(wh)
    rosters = wh.read(draft_projection.ROSTER_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("team").cast(pl.Int64)
    )
    feats = breakouts.features(seasons.filter(pl.col("season") < target), rosters, target)
    return feats.select(
        "nba_player_id",
        (pl.col("changed_team") > 0).alias("changed_team"),
        (pl.col("net_vacated_min") * 1000).alias("vacated_min"),
    ).unique("nba_player_id")


def consistency(weekly: pl.DataFrame, season: str) -> pl.DataFrame:
    """WEB-020: how much each player's weekly 9-cat value (z-sum within each week) swings, relative
    to his own weekly level, over last season.

    `weekly_sd` is the sd of his weekly values and `rel_sd` = weekly_sd / his mean weekly value.
    Only players with >= MIN_CONSISTENCY_WEEKS weeks and a positive mean are kept (relative swings
    of near-zero or negative contributors are meaningless); `pct` ranks `rel_sd` among them
    (0 = the steadiest). Absolute sds grow with value, so stars would always look volatile."""
    frames = []
    for (week,), w in weekly.group_by("week"):
        frames.append(
            w.select("nba_player_id").with_columns(
                pl.lit(week).alias("week"), pl.Series("v", _zsum(w, None))
            )
        )
    v = pl.concat(frames)
    agg = (
        v.group_by("nba_player_id")
        .agg(
            pl.len().alias("weeks"),
            pl.col("v").std().alias("weekly_sd"),
            pl.col("v").mean().alias("weekly_mean"),
        )
        .filter((pl.col("weeks") >= MIN_CONSISTENCY_WEEKS) & (pl.col("weekly_mean") > 0))
        .with_columns((pl.col("weekly_sd") / pl.col("weekly_mean")).alias("rel_sd"))
    )
    n = max(agg.height - 1, 1)
    return agg.with_columns(
        pl.lit(season).alias("season"),
        ((pl.col("rel_sd").rank("ordinal") - 1) / n).alias("pct"),
    ).select(
        "nba_player_id",
        "season",
        pl.col("weeks").cast(pl.Int64),
        "weekly_sd",
        "weekly_mean",
        "rel_sd",
        "pct",
    )


def check(new: pl.DataFrame, old: pl.DataFrame | None) -> list[str]:
    """Reasons the rebuilt values shouldn't replace the live file (empty = fine)."""
    reasons = []
    ranks_ok = (
        new.group_by("variant")
        .agg((pl.col("overall_rank").sort() == pl.int_range(1, pl.len() + 1)).all().alias("ok"))
        .get_column("ok")
        .all()
    )
    if not ranks_ok:
        reasons.append("ranks are not 1..n within each variant")
    if old is None:
        return reasons
    missing = set(old["variant"].unique()) - set(new["variant"].unique())
    if missing:
        reasons.append(f"missing variants: {sorted(missing)}")
    if old.height and abs(new.height - old.height) / old.height > MAX_ROW_CHANGE:
        reasons.append(f"row count {old.height} -> {new.height} (> {MAX_ROW_CHANGE:.0%})")

    def top10(df: pl.DataFrame) -> set[int]:
        top = df.filter(pl.col("variant") == "all").sort("overall_rank").head(10)
        return set(top.get_column("nba_player_id").to_list())

    kept = len(top10(new) & top10(old))
    if kept < MIN_TOP10_KEPT:
        reasons.append(f"only {kept} of the old top 10 are still in the top 10")
    return reasons


def run_job(  # noqa: PLR0913 - the job's inputs
    w: Workspace,
    wh: Warehouse,
    rules: LeagueRules,
    target: str = TARGET,
    method: str = SHIPPED_METHOD,
    *,
    build: Builder = build,
) -> int:
    """Rebuild, check against the live file, then write all tables; returns the values row count."""
    tables = build(wh, rules, target, method)
    old = w.read_parquet(VALUES) if w.exists(VALUES) else None
    reasons = check(tables[VALUES], old)
    if reasons:
        raise PublishRefusedError("; ".join(reasons))
    # The supporting files first, the guarded values file last: if any write fails, the live values
    # (what the site ranks by) are still the old, consistent ones, and the job fails visibly.
    for rel in sorted(tables, key=lambda r: r == VALUES):
        w.write_parquet(rel, tables[rel])
    return tables[VALUES].height
