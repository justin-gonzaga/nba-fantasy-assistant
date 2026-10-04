"""DRAFT-009: leak-free values for a past season, then the pre-registered draft replay and report.

Leak guards (the task's pre-registration):
- projections use seasons before the target only (project_pool asserts it) plus the target's
  pre-season games, which a draft that year could see;
- the minutes model's team context uses each player's opening team of the target season (known at
  tip-off), not the current rosters;
- the pool is players with a season just before the target plus that summer's draft class;
- no injury overrides (those are 2026 news).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import polars as pl

from dikit.methods import regression as rg
from fantasy_core.league import LeagueRules
from fantasy_evaluation import draft_replay as dr
from fantasy_evaluation.preseason_backtest import Method
from fantasy_models import valuation
from fantasy_models.preseason import breakouts as b
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.project import project_pool
from fantasy_models.preseason.schema import season_of, start_year
from fantasy_pipeline.draft_projection import FIRST_M1_TRAIN, METHODS, _inputs
from fantasy_pipeline.draft_values import POSITIONS_SQL, WEEKLY_SQL, within_week_variance
from fantasy_pipeline.warehouse import PRESEASON_SQL, Warehouse

TARGET = "2025-26"
REPORT = Path("docs/evaluation/reports/DRAFT-009-draft-replay.md")
OURS = "ours (H1+aging+M1pre)"
BASELINES = {"B0": "last season (B0)", "B1": "Marcel (B1)"}
BASE = BASELINES["B0"]
REPORTS = {
    "B0": REPORT,
    "B1": Path("docs/evaluation/reports/DRAFT-010-draft-replay-vs-marcel.md"),
}


def _ours_method(
    wh: Warehouse,
    seasons: pl.DataFrame,
    target: str,
    *,
    robust: bool = False,
    returners: bool = False,
) -> Method:
    pre = wh.read(PRESEASON_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
    opening = seasons.filter(pl.col("season") == target).select(
        pl.col("nba_player_id").cast(pl.Int64),
        pl.col("first_nba_team_id").cast(pl.Int64).alias("team"),
    )
    targets = [season_of(y) for y in range(start_year(FIRST_M1_TRAIN), start_year(target))]
    feats = b.features(
        seasons.filter(pl.col("season") < target), opening, target, injury_robust=robust
    )
    feats = b.add_preseason(feats, pre.filter(pl.col("season") == target))
    train = b.training_rows(seasons, targets, preseason=pre, injury_robust=robust)
    override = b.predict_mpg(rg.Ridge(), train, feats, b.M1_PRE_FEATURES)

    def with_m1(history: pl.DataFrame, t: str) -> pl.DataFrame:
        return m.hybrid(
            history,
            t,
            aging=True,
            mpg_override=override,
            three_season_games=robust,
            returners=returners,
        )

    return with_m1


FILL_REPORT = Path("docs/evaluation/reports/DRAFT-011-replacement-fill.md")
CURRENT = "current (missed games = 0)"
FILL = "A (missed games at replacement)"


def leak_free_values(
    wh: Warehouse, rules: LeagueRules, target: str = TARGET, baseline: str = "B0"
) -> dict[str, pl.DataFrame]:
    return _leak_free(
        wh,
        rules,
        target,
        lambda s: [
            (OURS, _ours_method(wh, s, target), False),
            (BASELINES[baseline], METHODS[baseline], False),
        ],
    )


def fill_values(wh: Warehouse, rules: LeagueRules, target: str = TARGET) -> dict[str, pl.DataFrame]:
    """DRAFT-011: our projection valued two ways, missed games at zero vs at replacement level."""
    return _leak_free(
        wh,
        rules,
        target,
        lambda s: [  # A (the candidate) first: the replay reports A - B
            (FILL, _ours_method(wh, s, target), True),
            (CURRENT, _ours_method(wh, s, target), False),
        ],
    )


def _leak_free(
    wh: Warehouse,
    rules: LeagueRules,
    target: str,
    strategies: Callable[[pl.DataFrame], list[tuple[str, Method, bool]]],
) -> dict[str, pl.DataFrame]:
    seasons, draft = _inputs(wh)
    last = season_of(start_year(target) - 1)
    pool = (
        pl.concat(
            [
                seasons.filter(pl.col("season") == last).select(
                    pl.col("nba_player_id").cast(pl.Int64)
                ),
                draft.filter(pl.col("draft_year") == start_year(target)).select("nba_player_id"),
            ]
        )
        .unique()
        .with_columns(pl.lit(None, pl.Int64).alias("overall_pick"))
    )
    positions = wh.read(POSITIONS_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
    within = within_week_variance(wh.read(WEEKLY_SQL.format(season=last)), rules, rules.pool_size)
    out = {}
    for name, fn, fill in strategies(seasons):
        proj = project_pool(seasons, draft, pool, target, fn).drop(
            "source", "mpg_band", strict=False
        )
        vals = valuation.value_all(
            proj, positions.select("nba_player_id", "nba_position"), rules, within, fill=fill
        )
        out[name] = vals.filter(pl.col("variant") == "all").join(
            positions.select("nba_player_id", "player_name"), on="nba_player_id", how="left"
        )
    return out


def days_from_logs(logs: pl.DataFrame) -> dict[date, dict[int, list[float]]]:
    days: dict[date, dict[int, list[float]]] = {}
    for row in logs.select("GAME_DATE", "PLAYER_ID", *dr.RAW).iter_rows():
        days.setdefault(date.fromisoformat(str(row[0])), {})[int(row[1])] = [
            float(x) for x in row[2:]
        ]
    return days


def report(res: dr.Result, values: dict[str, pl.DataFrame], generated: datetime) -> str:
    a, bname = res.strategies
    top = {}
    for strat in (a, bname):
        names = values[strat].sort("value", descending=True)["player_name"].head(5)
        top[strat] = ", ".join(names.fill_null("?").to_list())
    per = [r[a] - r[bname] for r in res.per_draft]
    mean = {s_: sum(r[s_] for r in res.per_draft) / len(res.per_draft) for s_ in (a, bname)}
    lines = [
        f"# Draft replay: our draft values vs {bname} (2025-26, leak-free)",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline draft-replay`.",
        "Pre-registered before any result: DRAFT-009 (commit 3a2535d, baseline B0) and DRAFT-010",
        "(commit b94f839, baseline B1).",
        "",
        "**Leak guards**: both strategies' values use seasons up to 2024-25 only (plus the 2025-26",
        "pre-season for ours), opening-night teams for the minutes model, a pool of 2024-25",
        "players + the 2025 draft class, and no injury overrides. The season is replayed on the",
        "real 2025-26 games.",
        "",
        f"**Setup**: {len(res.per_draft)} random seat orders; 16-team snake, 14 rounds;",
        "seats alternate the two strategies; daily lineups by the DEC-007 optimiser;",
        "score = weekly all-play H2H share of the 9 categories.",
        "",
        "## Result",
        "",
        "| strategy | mean all-play category share | top 5 by its values |",
        "|---|---|---|",
        f"| {a} | {mean[a]:.3f} | {top[a]} |",
        f"| {bname} | {mean[bname]:.3f} | {top[bname]} |",
        "",
        f"**Difference (ours - {bname}): {res.diff:+.3f}** (95 % CI {res.ci[0]:+.3f} to "
        f"{res.ci[1]:+.3f}, bootstrap over drafts [R-54]).",
        f"Ours averaged higher in **{res.a_better_share:.0%}** of the drafts",
        f"(per-draft differences {min(per):+.3f} to {max(per):+.3f}).",
        "",
        "0.500 is an average team. +0.01 is about one extra category won per opponent",
        "every 11 weeks.",
    ]
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class Comparison:
    """A pre-registered candidate-vs-current replay: names, ship margin, report location."""

    candidate: str
    current: str
    title: str
    task_file: str
    command: str
    margin: float  # ship if the CI lower bound of candidate - current exceeds this
    rule: str


FILL_CMP = Comparison(
    FILL,
    CURRENT,
    "Missed games at replacement level (DRAFT-011, G-26 A)",
    "docs/project/tasks/DRAFT-011-replacement-fill-missed-games.md",
    "repl-fill-replay",
    0.0,
    "ship only if the difference with IL replacements is > 0 and its CI lower bound > 0",
)
ROBUST = "B (injury-robust minutes + 3-season games)"
ROBUST_CMP = Comparison(
    ROBUST,
    "current (H1+aging+M1pre)",
    "Injury-robust minutes and games (DRAFT-012, G-26 B)",
    "docs/project/tasks/DRAFT-012-injury-robust-minutes-and-games.md",
    "robust-replay",
    -0.005,
    "non-inferiority: ship if the CI lower bound with IL replacements is > -0.005",
)
ROBUST_REPORT = Path("docs/evaluation/reports/DRAFT-012-injury-robust.md")


def robust_values(
    wh: Warehouse, rules: LeagueRules, target: str = TARGET
) -> dict[str, pl.DataFrame]:
    """DRAFT-012: our projection with and without the injury-robust inputs (candidate first)."""
    return _leak_free(
        wh,
        rules,
        target,
        lambda s: [
            (ROBUST, _ours_method(wh, s, target, robust=True), False),
            (ROBUST_CMP.current, _ours_method(wh, s, target), False),
        ],
    )


RETURN_CAND = "R (games floor for returners)"
RETURN_CMP = Comparison(
    RETURN_CAND,
    "current (H1+aging+M1pre)",
    "Replay and 2026-27 values: returners games floor (DRAFT-022, G-32)",
    "docs/project/tasks/DRAFT-022-return-from-lost-season-games.md",
    "returners-eval",
    -0.005,
    "non-inferiority: check 3 passes if the CI lower bound with IL replacements is > -0.005",
)


def returners_values(
    wh: Warehouse, rules: LeagueRules, target: str = TARGET
) -> dict[str, pl.DataFrame]:
    """DRAFT-022: our projection with and without the returners games floor (candidate first)."""
    return _leak_free(
        wh,
        rules,
        target,
        lambda s: [
            (RETURN_CAND, _ours_method(wh, s, target, returners=True), False),
            (RETURN_CMP.current, _ours_method(wh, s, target), False),
        ],
    )


def fill_report(  # noqa: PLR0913, PLR0917 - the pre-registered report's parts
    with_il: dr.Result,
    without_il: dr.Result,
    before: pl.DataFrame,
    after: pl.DataFrame,
    il_slots: int,
    generated: datetime,
    cmp: Comparison = FILL_CMP,
) -> str:
    """Report: both replays, the ship decision by the pre-registered rule, top 25 before/after."""
    a, b_ = with_il.strategies
    if a != cmp.candidate:
        msg = f"the candidate must be strategy A, got {a!r}"
        raise ValueError(msg)
    ship = (
        with_il.diff > 0 and with_il.ci[0] > cmp.margin
        if cmp.margin >= 0
        else (with_il.ci[0] > cmp.margin)
    )

    def row(name: str, r: dr.Result) -> str:
        return (
            f"| {name} | {r.diff:+.4f} | {r.ci[0]:+.4f} to {r.ci[1]:+.4f} | "
            f"{r.a_better_share:.0%} of {len(r.per_draft)} |"
        )

    def ranks(df: pl.DataFrame) -> dict[int, tuple[int, float]]:
        all_ = df.filter(pl.col("variant") == "all")
        return {
            int(r["nba_player_id"]): (int(r["overall_rank"]), float(r["dollars"] or 0.0))
            for r in all_.iter_rows(named=True)
        }

    rb, ra = ranks(before), ranks(after)
    names = dict(
        zip(
            after["nba_player_id"].to_list(),
            after["player_name"].fill_null("?").to_list(),
            strict=True,
        )
    )
    top = sorted(ra, key=lambda p: ra[p][0])[:25]
    lines = [
        f"# {cmp.title}",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline {cmp.command}`.",
        f"Pre-registered in `{cmp.task_file}` before any run.",
        "",
        "## Replay (2025-26, leak-free, 40 drafts, 16 teams, all-play share)",
        f"Strategy A = {a}; B = {b_}. Difference = A - B.",
        "",
        "| Replay | Difference | 95 % CI | A ahead |",
        "|---|---|---|---|",
        row(f"**with IL replacements ({il_slots} slots), decides**", with_il),
        row("without replacements (reported only)", without_il),
        "",
        f"**Decision by the rule**: {'SHIP A' if ship else 'KEEP the current values'} "
        f"({cmp.rule}).",
        "",
        "Caveat: one season (2025-26). The 95 % CI is over draft-seat randomness within this "
        "single season's replay, not season-to-season variation; a different season could differ.",
        "",
        "## 2026-27 values: top 25 with the candidate (A)",
        "| Rank (A) | Player | $ (A) | Rank before | $ before |",
        "|---|---|---|---|---|",
        *[
            f"| {ra[p][0]} | {names.get(p, '?')} | {ra[p][1]:.0f} | {rb.get(p, (0, 0.0))[0]} | "
            f"{rb.get(p, (0, 0.0))[1]:.0f} |"
            for p in top
        ],
        "",
    ]
    giannis = 203507
    if giannis in ra:
        lines.append(
            f"Giannis Antetokounmpo (the trigger): rank {rb.get(giannis, (0, 0.0))[0]} → "
            f"{ra[giannis][0]}, ${rb.get(giannis, (0, 0.0))[1]:.0f} → ${ra[giannis][1]:.0f}."
        )
    return "\n".join(lines) + "\n"
