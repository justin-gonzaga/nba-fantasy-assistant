"""DRAFT-007 job: minutes-model and breakout backtests (report) + 2026-27 outputs if they ship."""

from __future__ import annotations

import polars as pl

from dikit.methods import regression as rg
from dikit.time.clock import Clock, SystemClock
from fantasy_evaluation import breakout_backtest as bb
from fantasy_evaluation.breakout_report import render
from fantasy_models.preseason import breakouts as b
from fantasy_models.preseason.schema import history_before
from fantasy_pipeline.draft_projection import _inputs
from fantasy_pipeline.warehouse import SEASONS_SQL, Warehouse

# Production opening roster = the current roster (latest capture). Backtests use each player's
# first team of the historical season instead (U10); both stand in for the opening-night roster.
ROSTER_SQL = "select nba_player_id, nba_team_id as team from intermediate.int_player_profile"


def player_names(wh: Warehouse) -> dict[int, str]:
    raw = wh.read(SEASONS_SQL).select("nba_player_id", "player_name", "season").sort("season")
    return {int(r["nba_player_id"]): str(r["player_name"]) for r in raw.iter_rows(named=True)}


def breakout_predictions(  # noqa: PLR0913, PLR0917
    wh: Warehouse,
    model: rg.Logistic,
    target: str,
    kind: str,
    min_gp: float = 0.0,
    clock: Clock | None = None,
    pre: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """P(breakout) for every rostered player who played last season (the M2 population)."""
    seasons, _ = _inputs(wh)
    rosters = wh.read(ROSTER_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("team").cast(pl.Int64)
    )
    feats = b.features(history_before(seasons, target), rosters, target).filter(
        pl.col("gp_frac_last") >= min_gp
    )
    cols: tuple[str, ...] = b.M2_FEATURES
    if pre is not None:  # DRAFT-008 growth model uses pre-season role
        feats, cols = (
            b.add_preseason(feats, pre.filter(pl.col("season") == target)),
            b.M2_PRE_FEATURES,
        )
    p = model.predict_proba(b.matrix(feats, cols))
    return feats.select("nba_player_id").with_columns(
        pl.Series("p_breakout", p),
        pl.lit(target).alias("season"),
        pl.lit(kind).alias("kind"),
        pl.lit("M2-logistic-v0").alias("model_version"),
        pl.lit((clock or SystemClock()).now()).alias("created_at"),
    )


def run(
    wh: Warehouse, target: str, n_boot: int = 2000, clock: Clock | None = None
) -> tuple[str, bb.MinutesResult, bb.BreakoutResult, bb.BreakoutResult, pl.DataFrame | None]:
    seasons, draft = _inputs(wh)
    mins = bb.minutes_backtest(seasons, draft, n_boot=n_boot)
    brk = bb.breakout_backtest(seasons, n_boot=n_boot)
    growth = bb.breakout_backtest(seasons, n_boot=n_boot, min_gp=bb.GROWTH_MIN_GP)
    stamp = (clock or SystemClock()).now().strftime("%Y-%m-%d %H:%M UTC")
    md = render(mins, brk, player_names(wh), stamp, growth)
    parts = []
    if brk.ships and brk.model:
        parts.append(breakout_predictions(wh, brk.model, target, "bounce_back", clock=clock))
    if growth.ships and growth.model:
        parts.append(
            breakout_predictions(wh, growth.model, target, "growth", bb.GROWTH_MIN_GP, clock)
        )
    probs = pl.concat(parts) if parts else None
    return md, mins, brk, growth, probs
