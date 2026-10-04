"""DRAFT-022: the three pre-registered checks for the returners games floor, and the report.

1. Accuracy: expanding-window folds, paired bootstrap of (current - R) absolute error in the
   games fraction of cohort players; ship needs the 95 % CI entirely above 0 [R-54].
2. Calibration: |mean predicted - mean realised| games fraction for cohort players <= 0.08.
3. Non-inferiority: the DRAFT-011 replay with IL replacements, CI lower bound of R - current
   all-play share > -0.005 (computed by the replay harness and passed in).
All three must hold; otherwise the current method stays. Nothing here is tuned.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from fantasy_models.preseason import methods as m
from fantasy_models.preseason import returners as rt
from fantasy_models.preseason.schema import history_before, season_of, start_year

REPORT = Path("docs/evaluation/reports/DRAFT-022-returners.md")
FIRST_FOLD = (
    2021  # 2021-22: the first season with enough earlier cohort rows (checked, not assumed)
)
CALIBRATION_LIMIT = 0.08
REPLAY_MARGIN = -0.005
OLD = 33.0
LILLARD = 203081


@dataclass(frozen=True)
class Accuracy:
    mae_current: float
    mae_r: float
    ci: tuple[float, float]  # 95 % CI of (current - R) mean absolute error
    n: int


@dataclass(frozen=True)
class Decision:
    accuracy_ok: bool
    calibration_ok: bool
    replay_ok: bool

    @property
    def ship(self) -> bool:
        return self.accuracy_ok and self.calibration_ok and self.replay_ok


def _current_games_frac(past: pl.DataFrame, s: str) -> pl.DataFrame:
    """The shipped games forecast (Marcel-style, as a fraction of the season) for every player."""
    t = start_year(s)

    def lag(k: int) -> pl.DataFrame:
        return past.filter(pl.col("season") == season_of(t - k)).select(
            "nba_player_id",
            (pl.col("games_played") / pl.col("season_team_games")).alias(f"gp_frac_{k}"),
        )

    w = (
        past.filter(pl.col("season") >= season_of(t - 3))
        .select("nba_player_id")
        .unique()
        .join(lag(1), on="nba_player_id", how="left")
        .join(lag(2), on="nba_player_id", how="left")
        .with_columns(pl.col("gp_frac_1", "gp_frac_2").fill_null(0.0))
    )
    return w.select("nba_player_id", m.expected_games(w, 1).alias("pred"))


def fold_rows(history: pl.DataFrame, last_season: str) -> pl.DataFrame:
    """One row per holdout cohort player in each fold season: realised, current, r (games
    fractions), age. Seasons where R has too few earlier cohort rows contribute nothing."""
    seasons = sorted(history.get_column("season").unique().to_list())
    out = []
    for s in seasons:
        if start_year(s) < FIRST_FOLD or s > last_season:
            continue
        past = history_before(history, s)
        base = rt.base_rate(past, s)
        if base is None:
            continue
        real = rt.realised(history, s)
        w = _current_games_frac(past, s)
        age = (
            past.filter(pl.col("season") == season_of(start_year(s) - 2))
            .select("nba_player_id", (pl.col("age") + 2).alias("age"))
            .unique("nba_player_id")
        )
        rows = real.join(w, on="nba_player_id", how="left").join(
            age, on="nba_player_id", how="left"
        )
        out.append(
            rows.with_columns(
                pl.col("games_frac").alias("realised"),
                pl.col("pred").fill_null(0.25).alias("current"),
                pl.lit(s).alias("season"),
                pl.lit(base.rate).alias("base"),
            )
            .with_columns(pl.max_horizontal("current", "base").alias("r"))
            .select("season", "nba_player_id", "realised", "current", "r", "age")
        )
    if not out:
        return pl.DataFrame(
            schema={
                "season": pl.String,
                "nba_player_id": pl.Int64,
                "realised": pl.Float64,
                "current": pl.Float64,
                "r": pl.Float64,
                "age": pl.Float64,
            }
        )
    return pl.concat(out)


def accuracy(rows: pl.DataFrame, n_boot: int = 2000, seed: int = 0) -> Accuracy:
    real = rows["realised"].to_numpy()
    cur = np.abs(rows["current"].to_numpy() - real)
    r = np.abs(rows["r"].to_numpy() - real)
    ci = bs.mean_ci(cur - r, n_boot, np.random.default_rng(seed))
    return Accuracy(float(cur.mean()), float(r.mean()), ci, len(real))


def calibration_gap(rows: pl.DataFrame) -> float:
    return abs(float(rows["r"].mean()) - float(rows["realised"].mean()))  # type: ignore[arg-type]


def decide(acc: Accuracy, gap: float, replay_ci_low: float) -> Decision:
    return Decision(
        accuracy_ok=acc.ci[0] > 0,
        calibration_ok=gap <= CALIBRATION_LIMIT,
        replay_ok=replay_ci_low > REPLAY_MARGIN,
    )


def lillard_line(before: pl.DataFrame, after: pl.DataFrame) -> str:
    def at(df: pl.DataFrame) -> str:
        row = df.filter((pl.col("nba_player_id") == LILLARD) & (pl.col("variant") == "all"))
        if row.height == 0:
            return "not in the pool"
        r = row.row(0, named=True)
        return f"rank {r['overall_rank']}, ${float(r['dollars'] or 0.0):.0f}"

    return f"{at(before)} before, {at(after)} with R."


def _subgroup(rows: pl.DataFrame) -> str:
    old = rows.filter(pl.col("age") >= OLD)
    if old.height == 0:
        return "no cohort player aged 33 or more in the folds"
    m = old.select(pl.col("realised", "current", "r").mean()).row(0)
    return f"n = {old.height}: realised {m[0]:.2f}, current {m[1]:.2f}, R {m[2]:.2f}"


def render(  # noqa: PLR0913, PLR0917 - the pre-registered report's parts
    rows: pl.DataFrame,
    acc: Accuracy,
    gap: float,
    replay_ci_low: float,
    decision: Decision,
    replay_text: str,
    lillard: str,
    generated: datetime,
) -> str:
    def ok(flag: bool) -> str:
        return "pass" if flag else "FAIL"

    per_fold = (
        rows.group_by("season")
        .agg(
            pl.len().alias("n"),
            pl.col("realised").mean().alias("realised"),
            pl.col("current").mean().alias("current"),
            pl.col("r").mean().alias("r"),
        )
        .sort("season")
    )
    fold_lines = [
        f"| {r['season']} | {r['n']} | {r['realised']:.2f} | {r['current']:.2f} | {r['r']:.2f} |"
        for r in per_fold.iter_rows(named=True)
    ]
    verdict = (
        "SHIP variant R" if decision.ship else "KEEP the current method (use cited override rows)"
    )
    lines = [
        "# Returners: games floor after a lost season (DRAFT-022, G-32)",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline returners-eval`.",
        "Pre-registered in `docs/project/tasks/DRAFT-022-return-from-lost-season-games.md` and",
        "`docs/architecture/ml-methodology-plan.md` section 25 (commit 4a4ee78) before any run.",
        "",
        f"## Decision: {verdict}",
        "",
        "| Check | Result | Value | Rule |",
        "|---|---|---|---|",
        f"| 1 Accuracy | {ok(decision.accuracy_ok)} | MAE current {acc.mae_current:.3f}, R "
        f"{acc.mae_r:.3f}; CI of (current - R) {acc.ci[0]:+.3f} to {acc.ci[1]:+.3f} | CI lower "
        "bound > 0 |",
        f"| 2 Calibration | {ok(decision.calibration_ok)} | gap {gap:.3f} | <= "
        f"{CALIBRATION_LIMIT} |",
        f"| 3 Non-inferiority (replay, IL) | {ok(decision.replay_ok)} | CI lower bound "
        f"{replay_ci_low:+.4f} | > {REPLAY_MARGIN} |",
        "",
        f"## Folds ({acc.n} holdout cohort player-seasons, expanding window)",
        "",
        "Games fraction (games played / team games). Bootstrap resamples player-seasons (paired),",
        "2000 draws, seed 0 [R-54]. The folds are not independent of the Lillard observation and",
        "partly reuse data seen when the cohort was counted (disclosed in the pre-registration).",
        "",
        "| Fold season | n | realised | current | R |",
        "|---|---|---|---|---|",
        *fold_lines,
        "",
        "## Reported, not deciding",
        f"- Aged 33 or more: {_subgroup(rows)}.",
        f"- Lillard (a fact, not a target): {lillard}",
        "- Players in two consecutive lost seasons are outside the cohort by definition.",
        "",
        "---",
        "",
        replay_text,
    ]
    return "\n".join(lines) + "\n"
