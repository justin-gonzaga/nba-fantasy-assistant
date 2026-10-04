"""DEC-007: the pre-registered lineup replay report, with sample-roster standings."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import polars as pl

from fantasy_evaluation import lineup_replay as lr

REPORT = Path("docs/evaluation/reports/DEC-007-lineup.md")


def report(res: lr.Result, values: pl.DataFrame, generated: datetime) -> str:
    verdict = (
        "**SHIPS**: the brief's lineup comes from the optimiser"
        if res.ships
        else "**Does not ship**: the brief keeps the greedy lineup"
    )
    names = dict(
        zip(values["nba_player_id"].to_list(), values["player_name"].to_list(), strict=True)
    )
    squads = lr.rosters(values)
    table = ""
    if res.standings is not None:
        rows = [
            "| rank | roster (first 3 picks) | starts | PTS | REB | AST | STL | BLK | 3PM | TO "
            "| FG% | FT% | roto pts |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        for rank, r in enumerate(res.standings.iter_rows(named=True), 1):
            picks = ", ".join(names.get(p, str(p)) for p in squads[int(r["roster"]) - 1][:3])
            rows.append(
                f"| {rank} | #{r['roster']}: {picks} | {int(r['starts']):,} | {int(r['PTS']):,} | "
                f"{int(r['REB']):,} | {int(r['AST']):,} | {int(r['STL']):,} | {int(r['BLK']):,} | "
                f"{int(r['FG3M']):,} | {int(r['TOV']):,} | {r['FG%']:.3f} | {r['FT%']:.3f} | "
                f"{r['roto_points']:.1f} |"
            )
        table = "\n".join(rows)
    return f"""# DEC-007: lineup optimiser vs greedy (replay of 2025-26)

Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline lineup-replay`.
Pre-registered in the task file (commits 0aad42e, amended before any result in 738a953).

**Setup**: every 2025-26 regular-season game day x {lr.TEAMS} sample rosters (a snake draft of the
top {lr.TEAMS * lr.ROUNDS} by this season's draft values), slots Gx3, Fx3, Cx1, Utilx3. A player
plays that day if he has a game-log row. Both methods maximise the number of active players, then
their total value.

## Verdict

{verdict}. Across **{res.lineups:,} lineups**:
- the optimiser started **more players** than greedy in **{res.better_count:,}** lineups
  (+{res.mean_extra_active:.2f} players on average when it did), and the same number with **more
  value** in **{res.better_value:,}**;
- it was worse in **{res.worse}** and illegal in **{res.illegal}** (rule: both 0);
- the slowest solve took **{res.max_seconds * 1000:.0f} ms** (rule: < 1 s).

## Sample-roster standings (a thought experiment)

What each sample roster's optimised lineups actually produced over 2025-26, ranked like a
rotisserie table (16 points for the best in a category). These rosters are a snake draft by the
**2026-27** draft values replayed on last season's games, so they show how draft value turned into
production, not a real league.

{table}
"""
