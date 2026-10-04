"""League-aware player valuation for the draft (DRAFT-003; ml-methodology-plan §2).

Formats are handled through LeagueRules, never by name (ADR-0018):
- Category formats: G-score per category [R-01]. Each player's expected weekly edge is scaled by
  sqrt(between-player variance + week-to-week variance). The weekly term matters only when
  matchups are decided weekly; Rotisserie sets it to 0 (a plain z-score).
  Ratio categories are volume-weighted: makes - league% x attempts. Negative categories are flipped.
- Points formats: expected fantasy points per week from the league's stat modifiers.
Then:
- replacement level by pool size: the drafted pool is teams x drafted slots, filled greedily by
  position; replacement = the best undrafted player eligible at a position [R-83].
- missed games (DRAFT-011, D-65): with `fill`, a projected missed game counts at the replacement
  line (the mean per-game line of the 16 players just outside the drafted pool [R-83]) instead of
  zero, since a real team covers it from waivers or an IL slot.
- value over replacement (VOR) -> auction $: every drafted player gets $1; the rest of the league
  budget is shared in proportion to positive VOR (practitioner method, flagged U1).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import polars as pl

from fantasy_core.league import Category, LeagueRules

SEASON_WEEKS = 25.0  # NBA regular season ~ 20 Oct -> 11 Apr
SEASON_GAMES = 82
REPLACEMENT_N = 16  # players just outside the pool whose mean line fills missed games (DRAFT-011)
POSITIONS = ("G", "F", "C")
ELIGIBILITY = {  # NBA listing -> Yahoo G/F/C (D-47 Q1: derived; a Yahoo list paste can override)
    "G": ("G",),
    "F": ("F",),
    "C": ("C",),
    "G-F": ("G", "F"),
    "F-G": ("G", "F"),
    "F-C": ("F", "C"),
    "C-F": ("F", "C"),
}
POOL_ITERATIONS = 3


def eligibility(nba_position: str | None) -> tuple[str, ...]:
    return ELIGIBILITY.get(nba_position or "", ())


def weekly(
    proj: pl.DataFrame, stats: Iterable[str], repl: dict[str, float] | None = None
) -> pl.DataFrame:
    """Expected weekly totals: per game x expected games / season weeks. Missed games count as zero,
    or, given a replacement line `repl`, at that line (DRAFT-011)."""
    missed = (SEASON_GAMES - pl.col("games")).clip(lower_bound=0)

    def total(s: str) -> pl.Expr:
        own = pl.col(s) * pl.col("games")
        return own + missed * repl[s] if repl else own

    return proj.with_columns([(total(s) / SEASON_WEEKS).alias(f"w_{s}") for s in stats])


def replacement_line(
    proj: pl.DataFrame,
    order: list[int],
    stats: Iterable[str],
    pool_size: int,
    n: int = REPLACEMENT_N,
) -> dict[str, float]:
    """Mean per-game line of the `n` players just outside the pool (`order` is best first)."""
    ids = order[pool_size : pool_size + n]
    rows = proj.filter(pl.col("nba_player_id").is_in(ids))
    return {s: float(rows.get_column(s).mean() or 0.0) for s in stats}  # type: ignore[arg-type]


def _category_x(df: pl.DataFrame, cat: Category, ref: pl.DataFrame) -> np.ndarray:
    if cat.attempts is not None:
        p = float(ref.get_column(f"w_{cat.stat}").sum()) / float(
            ref.get_column(f"w_{cat.attempts}").sum()
        )
        x = (
            df.get_column(f"w_{cat.stat}").to_numpy()
            - p * df.get_column(f"w_{cat.attempts}").to_numpy()
        )
    else:
        x = df.get_column(f"w_{cat.stat}").to_numpy()
    return -x if cat.negative else x


def _stats(rules: LeagueRules) -> list[str]:
    return sorted(
        {c.stat for c in rules.categories} | {c.attempts for c in rules.categories if c.attempts}
    )


def category_scores(
    proj: pl.DataFrame,
    rules: LeagueRules,
    within_var: dict[str, float],
    ref_ids: np.ndarray,
    repl: dict[str, float] | None = None,
) -> pl.DataFrame:
    """One column `s_<code>` per category, standardised on the reference pool `ref_ids`."""
    df = weekly(proj, _stats(rules), repl)
    ref = df.filter(pl.col("nba_player_id").is_in(ref_ids))
    kappa = 1.0 if rules.scoring.weekly_matchups else 0.0
    cols = {}
    for cat in rules.categories:
        x, xr = _category_x(df, cat, ref), _category_x(ref, cat, ref)
        denom = np.sqrt(xr.var() + kappa * within_var.get(cat.code, 0.0)) or 1.0
        cols[f"s_{cat.code}"] = (x - xr.mean()) / denom
    return df.select("nba_player_id").with_columns([pl.Series(k, v) for k, v in cols.items()])


def points_scores(proj: pl.DataFrame, rules: LeagueRules) -> pl.DataFrame:
    df = weekly(proj, rules.modifiers)
    fpts = sum((pl.col(f"w_{s}") * w for s, w in rules.modifiers.items()), start=pl.lit(0.0))
    return df.select("nba_player_id", fpts.alias("s_fpts"))


def score(
    proj: pl.DataFrame,
    rules: LeagueRules,
    within_var: dict[str, float] | None = None,
    *,
    fill: bool = False,
) -> pl.DataFrame:
    """Per-category scores on a reference pool that converges to the drafted pool. With `fill`,
    the replacement line is recomputed each iteration from the players just outside that pool."""
    if not rules.scoring.uses_categories:
        return points_scores(proj, rules)
    ids = (
        proj.sort("pts", descending=True)
        .head(rules.pool_size)
        .get_column("nba_player_id")
        .to_numpy()
    )
    scores = pl.DataFrame()
    repl: dict[str, float] | None = None
    for _ in range(POOL_ITERATIONS + (1 if fill else 0)):
        scores = category_scores(proj, rules, within_var or {}, ids, repl)
        order = (
            scores.select(
                pl.sum_horizontal(pl.exclude("nba_player_id")).alias("t"), "nba_player_id"
            )
            .sort(["t", "nba_player_id"], descending=[True, False])
            .get_column("nba_player_id")
            .to_list()
        )
        ids = np.asarray(order[: rules.pool_size])
        if fill:
            repl = replacement_line(proj, order, _stats(rules), rules.pool_size)
    return scores


@dataclass(frozen=True)
class Variant:
    name: str
    punted: tuple[str, ...] = ()


def variants(rules: LeagueRules) -> list[Variant]:
    """The full-category build plus one punt per category (category formats only)."""
    out = [Variant("all")]
    if rules.scoring.uses_categories:
        out += [Variant(f"punt_{c.code}", (c.code,)) for c in rules.categories]
    return out


def _fill(order: list[int], elig: dict[int, tuple[str, ...]], rules: LeagueRules) -> set[int]:
    """Greedy draft: each player (best first) takes a free eligible starting slot, then Util,
    then bench, until the pool is full."""
    free = {p: rules.roster_slots.get(p, 0) * rules.teams for p in POSITIONS}
    flex = (
        rules.roster_slots.get("Util", 0) * rules.teams
        + rules.roster_slots.get("BN", 0) * rules.teams
    )
    drafted: set[int] = set()
    for pid in order:
        slot = next((p for p in elig.get(pid, ()) if free[p] > 0), None)
        if slot is not None:
            free[slot] -= 1
        elif flex > 0:
            flex -= 1
        else:
            continue
        drafted.add(pid)
        if len(drafted) >= rules.pool_size:
            break
    return drafted


def value_variant(
    scores: pl.DataFrame, positions: pl.DataFrame, rules: LeagueRules, variant: Variant
) -> pl.DataFrame:
    """Total value, draft pool, replacement level, VOR, $ and tiers for one variant."""
    keep = [
        c
        for c in scores.columns
        if c.startswith("s_") and c.removeprefix("s_") not in variant.punted
    ]
    df = scores.with_columns(pl.sum_horizontal(keep).alias("value")).join(
        positions, on="nba_player_id", how="left"
    )
    df = df.sort("value", descending=True)
    elig = {r["nba_player_id"]: eligibility(r["nba_position"]) for r in df.iter_rows(named=True)}
    drafted = _fill(df.get_column("nba_player_id").to_list(), elig, rules)
    undrafted = df.filter(~pl.col("nba_player_id").is_in(list(drafted)))
    best_left = float(undrafted.get_column("value").max() or 0.0)  # type: ignore[arg-type]
    repl = {
        p: max(
            (
                float(r["value"])
                for r in undrafted.iter_rows(named=True)
                if p in elig[r["nba_player_id"]]
            ),
            default=best_left,
        )
        for p in POSITIONS
    }

    def vor(pid: int, value: float) -> float:
        levels = [repl[p] for p in elig[pid]] or [best_left]
        return value - min(levels)

    df = df.with_columns(
        pl.col("nba_player_id").is_in(list(drafted)).alias("drafted"),
        pl.struct("nba_player_id", "value")
        .map_elements(lambda r: vor(r["nba_player_id"], r["value"]), return_dtype=pl.Float64)
        .alias("vor"),
    )
    if rules.auction_budget:
        spend = rules.teams * rules.auction_budget - rules.pool_size
        pos = df.filter(pl.col("drafted")).get_column("vor").clip(lower_bound=0).sum()
        dollars = (
            pl.when(pl.col("drafted"))
            .then(1 + pl.col("vor").clip(lower_bound=0) / pos * spend)
            .otherwise(0.0)
        )
        df = df.with_columns(dollars.alias("dollars"))
    else:
        df = df.with_columns(pl.lit(None, pl.Float64).alias("dollars"))
    df = df.with_columns(
        pl.col("value").rank(method="ordinal", descending=True).cast(pl.Int64).alias("overall_rank")
    )
    return df.with_columns(
        tiers(df.get_column("value").to_numpy(), max_size=rules.teams).alias("tier"),
        pl.lit(variant.name).alias("variant"),
        pl.lit(rules.teams).alias("league_teams"),  # WEB-022: first-round value = rank <= teams
    )


def tiers(values: np.ndarray, gap_sd: float = 0.25, max_size: int | None = None) -> pl.Series:
    """Natural breaks: a new tier starts where the drop to the next player (sorted by value)
    exceeds `gap_sd` standard deviations of the top-pool values, or (WEB-022) when the tier
    already holds `max_size` players (a draft round), since dense values have no big gaps."""
    order = np.argsort(-values)
    v = values[order]
    thresh = gap_sd * float(np.std(v[: max(1, min(len(v), 224))]))
    tier = np.ones(len(v), dtype=np.int64)
    size = 1
    for i in range(1, len(v)):
        full = max_size is not None and size >= max_size
        new = v[i - 1] - v[i] > thresh or full
        tier[i] = tier[i - 1] + (1 if new else 0)
        size = 1 if new else size + 1
    out = np.empty_like(tier)
    out[order] = tier
    return pl.Series("tier", out)


def value_all(
    proj: pl.DataFrame,
    positions: pl.DataFrame,
    rules: LeagueRules,
    within_var: dict[str, float] | None = None,
    *,
    fill: bool = False,
) -> pl.DataFrame:
    """Every variant, long format: one row per variant x player (DRAFT-004 reads this)."""
    scores = score(proj, rules, within_var, fill=fill)
    return pl.concat(
        [value_variant(scores, positions, rules, v) for v in variants(rules)], how="diagonal"
    )
