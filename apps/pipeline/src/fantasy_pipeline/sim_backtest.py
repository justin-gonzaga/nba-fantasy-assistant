"""DEC-003: run the pre-registered simulation test and write the report."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fantasy_evaluation import simulation_backtest as sb

REPORT = Path("docs/evaluation/reports/DEC-003-simulation.md")


def report(res: sb.Result, generated: datetime) -> str:
    cats = "\n".join(
        f"| {r['category']} | {r['b_normal']:.4f} | {r['b_sim']:.4f} | {r['diff']:+.4f} |"
        for r in res.table.iter_rows(named=True)
    )
    rel = "\n".join(
        f"| {int(r['bin']) / 10:.1f}-{(int(r['bin']) + 1) / 10:.1f} | {r['predicted']:.3f} | "
        f"{r['observed']:.3f} | {r['n']:,} |"
        for r in res.reliability.iter_rows(named=True)
    )
    verdict = (
        "**SHIPS**: the brief's category win chances come from the simulation"
        if res.ships
        else "**Does not ship**: the brief keeps the normal approximation"
    )
    return f"""# DEC-003: Monte Carlo simulation vs the normal approximation

Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline sim-backtest`.
The test was pre-registered in the task file (commit 8684b8a) before any result.

**Setup**: 2025-26 holdout weeks (from 19 Jan 2026), {sb.MATCHUPS_PER_WEEK} random matchups per
week of two {sb.TEAM}-player teams from the top {sb.POOL} by season-to-date points per game:
**{res.matchups:,} matchups**, {res.matchups * len(sb.CATS):,} category outcomes. Both methods
share the means (season-to-date averages x games played); the outcome is who actually won each
category. Brier score [R-40]; 95 % CI from a bootstrap over whole weeks (2,000 resamples) [R-55].

## Verdict

{verdict}. Pooled Brier difference (simulation - normal) **{res.pooled_diff:+.4f}**
(95 % CI {res.ci[0]:+.4f} to {res.ci[1]:+.4f}); rule: CI entirely below 0.

## Brier by category (lower is better; a coin flip scores 0.25)

| category | normal approx. | simulation | difference |
|---|---|---|---|
{cats}

## Reliability of the simulation's probabilities

| predicted bin | mean predicted | observed win rate | outcomes |
|---|---|---|---|
{rel}

## Monte Carlo precision (U14)

Mean standard error of expected categories won at {sb.DRAWS:,} draws: **{res.mc_se:.4f}**
(target < 0.02 at 10,000 draws; at 2,000 draws the target scales to < 0.045).
"""
