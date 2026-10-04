"""Markdown report for the preseason projection backtest (DRAFT-002 AC2, G-21b / D-51)."""

from __future__ import annotations

import polars as pl

from fantasy_evaluation.preseason_backtest import GATE_STATS, FoldResult, GateDecision, pooled_table

MAE_COMPARISONS = ("H1 vs B0", "C1 vs B0", "H1 vs C1")


def _ci(df: pl.DataFrame, comparison: str, stat: str | None = None) -> str:
    cond = pl.col("comparison") == comparison
    if stat is not None:
        cond &= pl.col("stat") == stat
    rows = df.filter(cond)
    if rows.height == 0:
        return "n/a"
    r = rows.row(0, named=True)
    return f"{r['diff']:+.3f} ({r['lo']:+.3f}, {r['hi']:+.3f})"


def _mae_table(fold: FoldResult) -> list[str]:
    methods = fold.mae.get_column("method").unique(maintain_order=True).to_list()
    head = (
        " | ".join(methods)
        + " | "
        + " | ".join(f"{c.replace(' vs ', ' - ')} (95 % CI)" for c in MAE_COMPARISONS)
    )
    lines = [f"| stat | {head} |", "|---" * (len(methods) + len(MAE_COMPARISONS) + 1) + "|"]
    for s in [*GATE_STATS, "fg3a", "mpg", "games"]:
        vals = [
            fold.mae.filter((pl.col("method") == k) & (pl.col("stat") == s)).get_column("mae")[0]
            for k in methods
        ]
        best = min(vals)
        cells = [f"**{v:.3f}**" if v == best else f"{v:.3f}" for v in vals]
        cis = [_ci(fold.mae_diff, c, s) for c in MAE_COMPARISONS]
        lines.append(f"| {s} | " + " | ".join(cells) + " | " + " | ".join(cis) + " |")
    return lines


def _fold_table(folds: list[FoldResult], attr: str, with_ci: bool) -> list[str]:
    methods = getattr(folds[-1], attr).get_column("method").to_list()
    extra = " | H1 - B0 (95 % CI) |" if with_ci else " |"
    lines = [
        "| target | players | " + " | ".join(methods) + extra,
        "|---" * (len(methods) + (3 if with_ci else 2)) + "|",
    ]
    for f in folds:
        tab = getattr(f, attr)
        cells = [f"{v:.3f}" for v in tab.get_column("spearman").to_list()]
        n = f.n_rank if attr == "rank" else f.n_players
        tail = f" | {_ci(f.rank_diff, 'H1 vs B0')} |" if with_ci else " |"
        lines.append(f"| {f.target} | {n} | " + " | ".join(cells) + tail)
    return lines


def render_report(
    folds: list[FoldResult], primary: FoldResult, decision: GateDecision, generated_at: str
) -> str:
    out = [
        "# DRAFT-002 backtest: preseason projections",
        "",
        f"Generated {generated_at} by `python -m fantasy_pipeline draft-backtest` "
        "from `intermediate.int_player_season` (BigQuery dev).",
        "Design: docs/architecture/ml-methodology-plan.md §4 (G-21), amended by G-21b / D-51. "
        "Every fold builds projections only from seasons before its target "
        "(rolling origin [R-50, R-51]).",
        "",
        "Methods:",
        "- **B0**: last season per game (naive baseline [R-52]).",
        "- **B1**: Marcel [R-13] (practitioner). 5/4/3 recency weights, regression of "
        "1,000 minutes to the league rate, Marcel age factor, Marcel games.",
        "- **C1**: empirical Bayes [R-11, R-12]. Gamma-Poisson per per-minute stat and "
        "Beta-Binomial per shooting %, prior strengths estimated from the 5 prior seasons; "
        "3-year weighted minutes; Marcel games.",
        "- **C1+aging**: C1 with a per-stat age curve estimated from our data "
        "(delta method, U6 ablation).",
        "- **H1**: C1 per-minute rates x last season's minutes per game x Marcel games "
        "(G-21b / D-51).",
        "",
        "**Primary metric (G-21b)**: Spearman rank correlation between projected and realised "
        "**season-total** 9-cat value (per game x games; z-sum, FG%/FT% as volume-weighted "
        "impact, TO negative), over every player who played the target season and has a "
        "projection from every method. Per-game MAE uses players with >= 20 games. "
        "CIs: paired bootstrap over players, 2,000 resamples [R-54].",
        "",
        f"## Decision (primary fold {primary.target}): ship **{decision.method}**",
        "",
        *[f"- {r}" for r in decision.reasons],
        "",
        "## Pooled over all folds: season-total value rank difference (every comparison)",
        "",
        "Bootstrap stratified by fold (players resampled within each fold, fold means averaged) "
        "[R-54]. Positive = the first method ranks realised value better.",
        "",
        "| comparison | mean diff | 95 % CI | folds positive |",
        "|---|---|---|---|",
        *[
            f"| {r['comparison']} | {r['diff']:+.3f} | {r['lo']:+.3f} to {r['hi']:+.3f} | "
            f"{int(r['folds_positive'])}/{int(r['folds'])} |"
            for r in pooled_table(folds).iter_rows(named=True)
        ],
        "",
        "## All folds: season-total value rank correlation (primary)",
        "",
        *_fold_table(folds, "rank", with_ci=True),
        "",
        "## All folds: per-game value rank correlation (secondary)",
        "",
        *_fold_table(folds, "rank_per_game", with_ci=False),
        "",
        "## Diagnostic: per-minute rates x the realised minutes (rate quality alone)",
        "",
        "This isolates the per-minute rate model from the minutes projection: with the true "
        "minutes, the shrunk rates rank far better than last season's, so minutes are the "
        "weak component (why H1 takes last season's minutes).",
        "",
        *_fold_table(folds, "rank_oracle_minutes", with_ci=False),
        "",
        f"## Primary fold {primary.target}: per-stat MAE (per game; lower is better, best in bold)",
        "",
        *_mae_table(primary),
        "",
        "Top-224 overlap on season-total value (share of the realised top 224 that each method "
        f"also ranks top 224), {primary.target}: "
        + ", ".join(
            f"{r['method']} {r['top_overlap']:.2f}" for r in primary.rank.iter_rows(named=True)
        ),
        "",
        "## Players with no NBA history "
        "(U4: rookie prior by draft bucket vs one league-average rookie line)",
        "",
    ]
    if primary.rookies.height:
        piv = primary.rookies.pivot(on="method", index="stat", values="mae")
        out.append(f"{primary.rookies.get_column('n')[0]} players, {primary.target}.")
        out.append("")
        out.append("| stat | rookie_prior | league_avg_rookie |")
        out.append("|---|---|---|")
        for r in piv.iter_rows(named=True):
            out.append(f"| {r['stat']} | {r['rookie_prior']:.3f} | {r['league_avg_rookie']:.3f} |")
    if primary.coverage80:
        out += [
            "",
            "## Calibration: 80 % interval coverage "
            "(sds from the previous fold's residuals; target 75-85 %)",
            "",
            ", ".join(f"{k} {v:.0%}" for k, v in sorted(primary.coverage80.items())),
        ]
    return "\n".join(out) + "\n"
