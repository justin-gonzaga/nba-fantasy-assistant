"""Markdown report for DRAFT-007 (minutes model + breakout probability)."""

from __future__ import annotations

from collections.abc import Callable

import polars as pl

from fantasy_evaluation.breakout_backtest import (
    HOLDOUT_FOLDS,
    SELECT_FOLDS,
    BreakoutResult,
    MinutesResult,
)


def render(
    mins: MinutesResult,
    brk: BreakoutResult,
    names: dict[int, str],
    generated_at: str,
    growth: BreakoutResult | None = None,
) -> str:
    def nm(pid: int) -> str:
        return names.get(pid, str(pid))

    out = [
        "# DRAFT-007 backtest: minutes model (M1) and breakout probability (M2)",
        "",
        f"Generated {generated_at} by `python -m fantasy_pipeline draft-breakouts` (BigQuery dev).",
        "Plan: docs/architecture/ml-methodology-plan.md Part 1b (§7, §8, §10a; G-23 / D-54). "
        "All rules below were pre-registered before this run. Every fold uses only earlier seasons "
        "plus the target season's opening roster (U10) [R-50, R-51]; CIs are bootstraps stratified "
        "by fold [R-54].",
        "",
        f"## M1 minutes model: {'SHIPS' if mins.ships else 'does not ship'}",
        "",
        *[f"- {r}" for r in mins.reasons],
        "",
        "| target | last season | ridge | LightGBM | players |",
        "|---|---|---|---|---|",
    ]
    wide = (
        mins.fold_mae.pivot(on="model", index="target", values="mae")
        .join(mins.fold_mae.group_by("target").agg(pl.col("n").max()), on="target")
        .sort("target")
    )
    for r in wide.iter_rows(named=True):
        tag = " (selection)" if r["target"] in SELECT_FOLDS else " (holdout)"
        out.append(
            f"| {r['target']}{tag} | {r['last']:.3f} | {r['ridge']:.3f} | "
            f"{r['gbm']:.3f} | {r['n']} |"
        )
    out += _m2_section(brk, nm, "M2a bounce-back chance (all players; D-55: shown as bounce-back)")
    if growth is not None:
        out += _m2_section(
            growth,
            nm,
            "M2b growth breakout chance (played >= 60 % of games last season; pre-registered D-55)",
        )
    return "\n".join(out) + "\n"


def _m2_section(brk: BreakoutResult, nm: Callable[[int], str], title: str) -> list[str]:
    out: list[str] = [
        "",
        f"## {title}: {'SHIPS' if brk.ships else 'does not ship'}",
        "",
        "Breakout = season-total 9-cat value rank improves by >= 50 places "
        "and finishes inside the top 150.",
        "",
        *[f"- {r}" for r in brk.reasons],
        "",
        "| target | players | base rate | precision@20 | precision@50 | Brier "
        "| Brier (base rate) | nDCG@20 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in brk.folds.iter_rows(named=True):
        out.append(
            f"| {r['target']} | {r['n']} | {r['base_rate']:.1%} | {r['p_at_20']:.0%} | "
            f"{r['p_at_50']:.0%} | "
            f"{r['brier']:.4f} | {r['brier_base']:.4f} | {r['ndcg20']:.2f} |"
        )
    out += [
        "",
        "Reliability (all folds pooled; predicted vs observed breakout rate):",
        "",
        "| predicted bin | mean predicted | observed | players |",
        "|---|---|---|---|",
    ]
    for r in brk.reliability.iter_rows(named=True):
        out.append(
            f"| {r['bin'] / 10:.1f}-{(r['bin'] + 1) / 10:.1f} | {r['mean_p']:.1%} | "
            f"{r['observed']:.1%} | {r['n']} |"
        )
    out += [
        "",
        f"Sensitivity (holdout folds {HOLDOUT_FOLDS[0]}..{HOLDOUT_FOLDS[-1]}; U9):",
        "",
        "| jump | base rate | precision@20 |",
        "|---|---|---|",
    ]
    for r in brk.sensitivity.iter_rows(named=True):
        out.append(f"| >= {r['jump']} ranks | {r['base_rate']:.1%} | {r['p_at_20']:.0%} |")
    out += [
        "",
        f"## Hindsight {HOLDOUT_FOLDS[-1]}: what the model flagged "
        f"using data up to {HOLDOUT_FOLDS[-2]} only",
        "",
        "Top 20 flags, plus every actual breakout (hit = broke out). "
        "Ranks are season-total 9-cat value.",
        "",
        "| model rank | player | P(breakout) | value rank last season "
        "| value rank this season | broke out |",
        "|---|---|---|---|---|---|",
    ]
    for r in brk.hindsight.iter_rows(named=True):
        out.append(
            f"| {r['model_rank']} | {nm(r['nba_player_id'])} | {r['p_breakout']:.0%} | "
            f"{r['rank_last']} | {r['rank']} | "
            f"{'yes' if r['breakout'] else 'no'} |"
        )
    return out
