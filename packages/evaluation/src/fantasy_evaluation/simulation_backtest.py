"""DEC-003: does the Monte Carlo simulation give better-calibrated category win chances than the
live normal approximation? (Pre-registered in the task file.)

Each holdout week: random matchups of two 10-player teams from that week's pool (top 224 by
season-to-date points per game, >= 5 earlier games, >= 1 game that week). Both methods get the same
means (season-to-date averages x games played); the outcome is who actually won each category.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from fantasy_decision import brief, simulate
from fantasy_evaluation.distribution_backtest import HOLDOUT_START, player_weeks

POOL = 224
TEAM = 10
MATCHUPS_PER_WEEK = 100
DRAWS = 2000
CATS = [*simulate.COUNTS, *simulate.PCTS]
RAW = {
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "fg3m": "FG3M",
    "tov": "TOV",
}


@dataclass(frozen=True)
class Result:
    table: pl.DataFrame  # per category: brier_normal, brier_sim, diff
    pooled_diff: float
    ci: tuple[float, float]
    reliability: pl.DataFrame
    matchups: int
    mc_se: float  # mean MC standard error of expected categories won (U14)
    ships: bool


def _per_game(df: pl.DataFrame, col: str) -> np.ndarray:
    return (df[f"prior_{col}"] / df["prior_n"]).to_numpy()


def _team_inputs(df: pl.DataFrame) -> tuple[simulate.Team, pl.DataFrame]:
    n = df["n"].to_numpy()
    counts = {c: _per_game(df, raw) * n for c, raw in RAW.items()}
    att = {"fga": _per_game(df, "FGA") * n, "fta": _per_game(df, "FTA") * n}
    with np.errstate(divide="ignore", invalid="ignore"):
        fg = np.nan_to_num(df["prior_FGM"].to_numpy() / df["prior_FGA"].to_numpy(), nan=0.45)
        ft = np.nan_to_num(df["prior_FTM"].to_numpy() / df["prior_FTA"].to_numpy(), nan=0.75)
    team = simulate.Team(counts, att, {"fg_pct": fg, "ft_pct": ft}, n)
    week = pl.DataFrame(
        {
            **counts,
            "fgm": att["fga"] * fg,
            "fga": att["fga"],
            "ftm": att["fta"] * ft,
            "fta": att["fta"],
            "exp_games": n.astype(float),
            "nba_player_id": np.arange(len(n)),
        }
    )
    return team, week


def _actual(df: pl.DataFrame) -> dict[str, float]:
    out = {c: float(df[raw].sum()) for c, raw in RAW.items()}
    for cat, (m, a) in {"fg_pct": ("FGM", "FGA"), "ft_pct": ("FTM", "FTA")}.items():
        att = float(df[a].sum())
        out[cat] = float(df[m].sum()) / att if att else 0.0
    return out


def _outcome(a: dict[str, float], b: dict[str, float], cat: str) -> float:
    x, y = (b[cat], a[cat]) if cat in simulate.LOWER_IS_BETTER else (a[cat], b[cat])
    return 1.0 if x > y else 0.5 if x == y else 0.0


def run(
    logs: pl.DataFrame, *, n_boot: int = 2000, seed: int = 0, matchups: int = MATCHUPS_PER_WEEK
) -> Result:
    rng = np.random.default_rng(seed)
    pw = player_weeks(logs).filter(pl.col("week") >= HOLDOUT_START)
    rows: list[dict[str, object]] = []
    ses = []
    for w in sorted(pw["week"].unique().to_list()):
        pool = (
            pw.filter(pl.col("week") == w)
            .with_columns((pl.col("prior_PTS") / pl.col("prior_n")).alias("ppg"))
            .sort("ppg", descending=True)
            .head(POOL)
        )
        if pool.height < 2 * TEAM:
            continue
        for k in range(matchups):
            idx = rng.choice(pool.height, 2 * TEAM, replace=False)
            da, dbb = pool[idx[:TEAM].tolist()], pool[idx[TEAM:].tolist()]
            (sa, wa), (sb, wb) = _team_inputs(da), _team_inputs(dbb)
            normal = brief.win_probs(
                brief.team_totals(wa, list(range(TEAM))), brief.team_totals(wb, list(range(TEAM)))
            )
            m = simulate.matchup(sa, sb, draws=DRAWS, seed=seed * 1_000_003 + len(rows) + k)
            ses.append(m.se_expected_categories)
            act_a, act_b = _actual(da), _actual(dbb)
            for c in CATS:
                y = _outcome(act_a, act_b, c)
                rows.append(
                    {"week": w, "category": c, "y": y, "p_normal": normal[c], "p_sim": m.probs[c]}
                )
    df = pl.DataFrame(rows).with_columns(
        ((pl.col("p_normal") - pl.col("y")) ** 2).alias("b_normal"),
        ((pl.col("p_sim") - pl.col("y")) ** 2).alias("b_sim"),
    )
    table = (
        df.group_by("category")
        .agg(pl.col("b_normal").mean(), pl.col("b_sim").mean())
        .with_columns((pl.col("b_sim") - pl.col("b_normal")).alias("diff"))
        .sort("category")
    )
    by_week = (
        df.group_by("week")
        .agg((pl.col("b_sim") - pl.col("b_normal")).sum().alias("s"), pl.len().alias("n"))
        .sort("week")  # group_by order is arbitrary: unsorted, the bootstrap CI changed per run
    )
    s, n = by_week["s"].to_numpy(), by_week["n"].to_numpy()
    lo, hi = bs.ratio_ci(s, n, n_boot, rng)
    pooled = float((df["b_sim"] - df["b_normal"]).mean())  # type: ignore[arg-type]
    reliability = (
        df.with_columns((pl.col("p_sim") * 10).floor().clip(0, 9).alias("bin"))
        .group_by("bin")
        .agg(
            pl.col("p_sim").mean().alias("predicted"),
            pl.col("y").mean().alias("observed"),
            pl.len().alias("n"),
        )
        .sort("bin")
    )
    return Result(
        table, pooled, (lo, hi), reliability, df.height // len(CATS), float(np.mean(ses)), hi < 0
    )
