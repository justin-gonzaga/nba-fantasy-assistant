"""ANL-005: leak-free pre-season priors for past seasons, the test and its report."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl

from fantasy_evaluation import inseason_backtest as ib
from fantasy_models.preseason.project import project_pool
from fantasy_models.preseason.schema import season_of, start_year
from fantasy_pipeline.draft_projection import _inputs
from fantasy_pipeline.draft_replay_run import _ours_method
from fantasy_pipeline.warehouse import Warehouse

SEASONS = ["2023-24", "2024-25", "2025-26"]
REPORT = Path("docs/evaluation/reports/ANL-005-inseason-update.md")
STATS = ["pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta"]


def leak_free_priors(wh: Warehouse, targets: list[str]) -> pl.DataFrame:
    """Per-game pre-season projections for each target season, each from earlier data only."""
    seasons, draft = _inputs(wh)
    frames = []
    for target in targets:
        last = season_of(start_year(target) - 1)
        pool = (
            pl.concat(
                [
                    seasons.filter(pl.col("season") == last).select(
                        pl.col("nba_player_id").cast(pl.Int64)
                    ),
                    draft.filter(pl.col("draft_year") == start_year(target)).select(
                        "nba_player_id"
                    ),
                ]
            )
            .unique()
            .with_columns(pl.lit(None, pl.Int64).alias("overall_pick"))
        )
        proj = project_pool(seasons, draft, pool, target, _ours_method(wh, seasons, target))
        frames.append(
            proj.select(
                pl.lit(target).alias("SEASON"),
                pl.col("nba_player_id").cast(pl.Int64).alias("PLAYER_ID"),
                *[pl.col(s).cast(pl.Float64) for s in STATS],
            )
        )
    return pl.concat(frames)


def report(res: ib.Result, generated: datetime) -> str:
    rows = [
        "| category | k (games of prior) | MAE frozen prior | MAE season-to-date | MAE blend | "
        "blend - prior (95 % CI) |",
        "|---|---|---|---|---|---|",
    ]
    for r in res.table.iter_rows(named=True):
        mark = " ✅" if r["ci_hi"] < 0 else ""
        rows.append(
            f"| {r['category']} | {r['k']} | {r['mae_prior']:.4f} | {r['mae_std']:.4f} | "
            f"{r['mae_blend']:.4f} | {r['diff']:+.4f} "
            f"({r['ci_lo']:+.4f} to {r['ci_hi']:+.4f}){mark} |"
        )
    wins = res.table.filter(pl.col("ci_hi") < 0).height
    verdict = (
        "**SHIPS**: the week projection blends the prior with the season so far"
        if res.ships
        else "**Does not ship**: the week projection keeps the frozen prior"
    )
    lines = [
        "# ANL-005: updating pre-season projections with the season so far",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC by",
        "`python -m fantasy_pipeline inseason-backtest`.",
        "Pre-registered in the task file (commit f6e1775) before any result.",
        "",
        "**Setup**: leak-free pre-season priors (H1+aging+M1pre) for 2023-24, 2024-25 and 2025-26;",
        "player-weeks with a prior and >= 1 earlier game.",
        f"{res.rows['selection']:,} selection weeks pick k per stat;",
        f"{res.rows['holdout']:,} holdout player-weeks (from 19 Jan 2026) score.",
        "Weekly MAE given the games played;",
        "week-block bootstrap CIs [R-55]; ✅ = CI below 0.",
        "",
        "## Verdict",
        "",
        f"{verdict}. The blend beats the frozen prior on **{wins} of 9** categories",
        "(rule: >= 6, with no category more than 2 % worse).",
        "",
        "## Holdout MAE (lower is better)",
        "",
        *rows,
        "",
    ]
    return "\n".join(lines)
