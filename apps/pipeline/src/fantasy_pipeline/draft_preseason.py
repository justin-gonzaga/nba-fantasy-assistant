"""DRAFT-008 job: does the pre-season role signal pass its pre-registered tests (G-24 / D-57)?"""

from __future__ import annotations

import polars as pl

from dikit.time.clock import Clock, SystemClock
from fantasy_evaluation import breakout_backtest as bb
from fantasy_evaluation.breakout_report import _m2_section
from fantasy_pipeline.draft_breakouts import breakout_predictions, player_names
from fantasy_pipeline.draft_projection import _inputs
from fantasy_pipeline.warehouse import PRESEASON_SQL, Warehouse


def load_preseason(wh: Warehouse) -> pl.DataFrame:
    return wh.read(PRESEASON_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))


def run(
    wh: Warehouse, n_boot: int = 2000, clock: Clock | None = None, target: str = "2026-27"
) -> tuple[str, bool, bool, pl.DataFrame | None]:
    seasons, draft = _inputs(wh)
    pre = load_preseason(wh)
    mins = bb.preseason_minutes_backtest(seasons, draft, pre, n_boot=n_boot)
    growth = bb.breakout_backtest(seasons, n_boot=n_boot, min_gp=bb.GROWTH_MIN_GP, pre=pre)
    names = player_names(wh)
    stamp = (clock or SystemClock()).now().strftime("%Y-%m-%d %H:%M UTC")
    wide = mins.fold_mae.pivot(on="model", index="target", values="mae").sort("target")
    out = [
        "# DRAFT-008 backtest: pre-season role signal",
        "",
        f"Generated {stamp} by `python -m fantasy_pipeline draft-preseason` (BigQuery dev).",
        "Rules pre-registered in docs/architecture/ml-methodology-plan.md §12 "
        "(G-24 / D-57, PR #23) "
        "before this data existed in the warehouse. Pre-season features use only exhibition "
        "games up to "
        "2 days before each opening night; starts are missing before 2017-18 (source quality) and "
        "flagged explicitly. Holdout folds only; bootstrap stratified by fold [R-54].",
        "",
        f"## Minutes model with pre-season role: {'SHIPS' if mins.ships else 'does not ship'}",
        "",
        *[f"- {r}" for r in mins.reasons],
        "",
        "| target | M1 (current) | M1 + pre-season |",
        "|---|---|---|",
        *[
            f"| {r['target']} | {r['M1']:.3f} | {r['M1pre']:.3f} |"
            for r in wide.iter_rows(named=True)
        ],
    ]
    hindsight_fix = (
        f"using data up to {bb.HOLDOUT_FOLDS[-2]} only",
        f"using data up to {bb.HOLDOUT_FOLDS[-2]} plus that season's pre-season games "
        "before the draft cutoff",
    )
    section = _m2_section(
        growth,
        lambda pid: names.get(pid, str(pid)),
        "Growth breakout chance with pre-season role (played >= 60 % of games; D-55 rule)",
    )
    out += [line.replace(*hindsight_fix) for line in section]
    probs = None
    if growth.ships and growth.model and pre.filter(pl.col("season") == target).height:
        probs = breakout_predictions(
            wh, growth.model, target, "growth", bb.GROWTH_MIN_GP, clock, pre=pre
        )
    return "\n".join(out) + "\n", mins.ships, growth.ships, probs
