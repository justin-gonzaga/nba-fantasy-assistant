"""DEC-002: run the pre-registered distribution test on stored game logs and write the report."""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path

import polars as pl

from dikit.errors import SourceUnavailable
from dikit.store.snapshot import SnapshotStore
from fantasy_evaluation import distribution_backtest as db
from fantasy_ingest import nba_stats

SEASONS = ["2023-24", "2024-25", "2025-26"]
REPORT = Path("docs/evaluation/reports/DEC-002-distributions.md")
COLS = ["PLAYER_ID", "GAME_DATE", *db.COUNTS.values(), "FGM", "FGA", "FTM", "FTA"]


def load_logs(store: SnapshotStore, seasons: list[str]) -> pl.DataFrame:
    frames = []
    for s in seasons:
        req = nba_stats.league_game_log(s, "P")
        payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
        if payload is None:
            msg = f"no {s} game logs stored"
            raise SourceUnavailable(nba_stats.SOURCE, msg)
        df = pl.DataFrame(nba_stats.result_set(payload)).select(COLS)
        frames.append(df.with_columns(pl.lit(s).alias("SEASON")))
    return pl.concat(frames)


def _fmt(x: float) -> str:
    return "∞ (Poisson)" if math.isinf(x) else f"{x:.3f}"


def report(res: db.Result, generated: datetime) -> str:
    lines = [
        "| category | holdout player-weeks | CRPS Poisson | CRPS NB | NB - Poisson (95 % CI) "
        "| PIT dev. Poisson | PIT dev. NB |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in res.table.iter_rows(named=True):
        better = " ✅" if r["ci_hi"] < 0 else ""
        lines.append(
            f"| {r['category']} | {r['n']:,} | {r['crps_poisson']:.4f} | {r['crps_nb']:.4f} | "
            f"{r['diff']:+.4f} ({r['ci_lo']:+.4f} to {r['ci_hi']:+.4f}){better} | "
            f"{r['pit_poisson']:.4f} | {r['pit_nb']:.4f} |"
        )
    disp = "\n".join(f"| {k} | {_fmt(v)} |" for k, v in res.dispersion.items())
    wins = res.table.filter(pl.col("ci_hi") < 0).height
    pit_b = float(res.table["pit_poisson"].mean())  # type: ignore[arg-type]
    pit_n = float(res.table["pit_nb"].mean())  # type: ignore[arg-type]
    verdict = (
        "**SHIPS**: the simulation uses negative-binomial totals"
        if res.ships
        else "**Does not ship**: the simulation keeps Poisson/binomial totals"
    )
    return f"""# DEC-002: negative-binomial vs Poisson weekly totals

Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline dist-backtest`.
The test was pre-registered in the task file (commit ac54390) before any result: see DEC-002,
"Pre-registered test".

**Setup**: player-weeks (Mon-Sun) of {", ".join(SEASONS)} with >= 5 earlier games that season.
Both models share the mean (season-to-date per-game average x games played that week), so only
the distribution shape differs. Dispersions come from **{res.rows["selection"]:,} selection
player-weeks** (before 19 Jan 2026); scores are on **{res.rows["holdout"]:,} holdout player-weeks**
(from 19 Jan 2026). CRPS [R-41]; randomized PIT [R-43, R-44]; 95 % CIs from a bootstrap over
whole weeks (2,000 resamples) [R-55]. ✅ = CI entirely below 0.

## Verdict

{verdict}. NB is better (CI below 0) on **{wins} of 9** categories (rule: >= 6); mean PIT deviation
Poisson {pit_b:.4f} vs NB {pit_n:.4f} (rule: NB no worse).

## Holdout scores (lower is better)

{chr(10).join(lines)}

## Dispersions (selection weeks)

Per-game negative-binomial size r (variance = m + m²/r; ∞ = Poisson), and the
beta-binomial correlation for makes given attempts.

| parameter | estimate |
|---|---|
{disp}
"""
