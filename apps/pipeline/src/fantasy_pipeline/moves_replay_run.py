"""DEC-008: the add/drop replay on 2025-26 from leak-free inputs, and its report."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl

from dikit.errors import SourceUnavailable
from dikit.store.snapshot import SnapshotStore
from fantasy_core.league import LeagueRules
from fantasy_evaluation import draft_replay as dr
from fantasy_evaluation import moves_replay as mr
from fantasy_ingest import nba_stats
from fantasy_pipeline.draft_replay_run import OURS, TARGET, leak_free_values
from fantasy_pipeline.inseason_run import leak_free_priors
from fantasy_pipeline.warehouse import Warehouse

REPORT = Path("docs/evaluation/reports/DEC-008-moves.md")
NAMES = {
    "A": "A: live pickups rule (normal approx., this week)",
    "B0.5": "B: simulation, this week + 0.5 x next (decides)",
    "B0.3": "B at 0.3 (sensitivity)",
    "B0.7": "B at 0.7 (sensitivity)",
}


def load_logs(store: SnapshotStore, season: str = TARGET) -> pl.DataFrame:
    req = nba_stats.league_game_log(season, "P")
    payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
    if payload is None:
        msg = f"no {season} game logs stored"
        raise SourceUnavailable(nba_stats.SOURCE, msg)
    return pl.DataFrame(nba_stats.result_set(payload)).select(
        pl.col("PLAYER_ID").cast(pl.Int64),
        pl.col("TEAM_ID").cast(pl.Int64),
        "GAME_DATE",
        *mr.RAW,
    )


def inputs(
    wh: Warehouse, store: SnapshotStore, rules: LeagueRules
) -> tuple[list[list[int]], dict[date, mr.Week], dict[int, float]]:
    vals = leak_free_values(wh, rules)[OURS]
    value = dict(zip(vals["nba_player_id"].to_list(), vals["value"].to_list(), strict=True))
    squads = dr.snake({"ours": value}, ["ours"] * dr.TEAMS, dr.ROUNDS)
    priors = leak_free_priors(wh, [TARGET]).drop("SEASON")
    logs = load_logs(store)
    mondays = mr.weeks_of(logs)
    wanted = sorted({*mondays, *(m + timedelta(days=7) for m in mondays)})
    return squads, {m: mr.week_inputs(logs, priors, m) for m in wanted}, value


def report(res: mr.Result, weeks: int, generated: datetime) -> str:
    rows = [
        "| method | mean realised gain (categories) | 95 % CI | team-weeks with a move |",
        "|---|---|---|---|",
    ]
    for r in res.summary.iter_rows(named=True):
        rows.append(
            f"| {NAMES[r['method']]} | {r['mean_gain']:+.4f} | "
            f"{r['ci_lo']:+.4f} to {r['ci_hi']:+.4f} | {r['move_share']:.0%} |"
        )
    diff, lo, hi = res.b_minus_a
    verdict = (
        "**B SHIPS**: method B becomes the brief's pickup rule (wired in DEC-010)"
        if res.ships
        else "**B does not ship**: the brief keeps the live pickups rule (A)"
    )
    lines = [
        "# DEC-008: which add/drop rule gains more categories?",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline moves-replay`.",
        "Pre-registered in the task file (commit 6f41bc4) before any result.",
        "",
        f"**Setup**: 16 rosters of 14 drafted by the leak-free 2025-26 values; {weeks} holdout "
        f"weeks (from 19 Jan 2026) x 16 teams = {res.rows.height} team-weeks. Each team-week, each",
        "method proposes at most one Monday move from what was known then; the move is scored on",
        "actual stats: categories won vs that week's opponent, minus without the move, plus 0.5 x",
        "next week. Week-block bootstrap CIs [R-55]. A moves only if its own gain is > 0.",
        "",
        "## Verdict",
        "",
        f"{verdict}. B minus A: **{diff:+.4f}** categories per team-week "
        f"(95 % CI {lo:+.4f} to {hi:+.4f}; rule: CI entirely above 0).",
        "",
        "## Realised gain per team-week vs making no move",
        "",
        *rows,
        "",
        "A gain of +0.10 means one extra category every ten weeks for that team.",
        "",
        "## Limitations (reviewer findings)",
        "",
        "- Common random numbers are partial: numpy's negative-binomial and beta draws use a",
        "  variable number of stream values, so swapping one player can shift the later draws. The",
        "  estimate stays unbiased but noise cancels less than [R-61] promises.",
        "- 1,000 draws per scored pair; Monte Carlo SE not measured here (U14; DEC-003 found",
        "  SE 0.027 at 2,000). The ship margin (CI low +0.055) is measured on realised outcomes,",
        "  so simulation noise can only make B's choices worse, not inflate its score.",
        "- Players with no games yet this season get 0 expected games (e.g. a debuting rookie).",
        "- Yahoo's weekly add limit and waiver order are not modelled; B moved every team-week.",
        "",
        "## Disclosure: two bugs found before this run",
        "",
        "1. The first run gave B exactly +0.0000 while moving in 15 % of team-weeks. Cause: B",
        "   ranked free agents by draft value x games, but free agents' values are below",
        "   replacement (negative), so players with **no games** ranked first and B only ever",
        "   considered idle players. That was an implementation bug, not the pre-registered",
        "   method ('the top free agents by projected weekly value'). Fix: the screen ranks free",
        "   agents by the normal-approximation gain over the same horizon (regression test in",
        "   `test_moves.py`).",
        "2. Method A's gain differed between runs (+0.38, +0.34, +0.32) with no code change.",
        "   Cause: several players share exactly the same value (e.g. rookies from the same draft",
        "   slot) and the snake draft broke ties by row order, which the data load doesn't fix,",
        "   so the league's rosters changed from run to run. Fix: ties go to the lowest player id",
        "   (`test_draft_replay.py`). The spread shows that the gains depend on the league drawn;",
        "   the CIs above cover week-to-week noise only, not other drafts.",
        "",
        "Methods, data, scoring and the ship rule are otherwise as pre-registered. The bug-fix",
        "run with the old tie-breaking gave B - A = +0.2557 (CI +0.1051 to +0.4034).",
        "",
    ]
    return "\n".join(lines)
