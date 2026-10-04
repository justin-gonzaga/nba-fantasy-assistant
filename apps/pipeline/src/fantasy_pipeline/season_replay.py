"""SIM-001: one compact file per replay season (G-31 A: published files, the browser simulates).

Each `replay/<season>.json` holds:
- `players`: everyone with a value or a game that season: name, team (first team that season),
  position (from that season's rosters, else the latest earlier one), and the leak-free
  pre-season $ value, rank and 9-category strengths (the DRAFT-009 replay method with the shipped
  projection), so a replay draft only knows what was known before that season;
- `weeks`: Monday-Sunday matchup weeks, week 1 from opening night to the first Sunday;
- `lines`: every player-game, columnar (player id, day index, minutes and the counting stats).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from typing import Any

import polars as pl

from fantasy_pipeline.workspace import Workspace

SEASONS = ("2023-24", "2024-25", "2025-26")  # G-31 Q5 A
STATS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta")
CATEGORY_ORDER = (
    "pts",
    "reb",
    "ast",
    "stl",
    "blk",
    "fg3m",
    "fg_pct",
    "ft_pct",
    "tov",
)  # the web's order
LINES_SQL = (
    "select nba_player_id, game_date, nba_team_id, team_abbreviation, minutes,"
    " pts, reb, ast, stl, blk, fg3m, tov, fgm, fga, ftm, fta"
    " from staging.stg_nba_stats__player_game where season = '{season}'"
)
ROSTER_SQL = "select season, nba_player_id, nba_position from staging.stg_nba_stats__roster"
NAMES_SQL = (
    "select nba_player_id, any_value(player_name) as player_name"
    " from intermediate.int_player_season group by 1"
)


def path(season: str) -> str:
    return f"replay/{season}.json"


def weeks(days: Sequence[date]) -> list[dict[str, Any]]:
    """Matchup weeks over the game days: week 1 ends on the first Sunday; then Monday-Sunday."""
    if not days:
        return []
    first, last = min(days), max(days)
    out = []
    start = first
    n = 1
    while start <= last:
        end = start + timedelta(days=6 - start.weekday())  # the Sunday of this week
        out.append({"week": n, "start": start.isoformat(), "end": min(end, last).isoformat()})
        start, n = end + timedelta(days=1), n + 1
    return out


def compact_lines(lines: pl.DataFrame) -> dict[str, Any]:
    """Columnar lines: `dates` once, then per game the player id, day index, minutes and stats."""
    days = sorted(set(lines["game_date"].to_list()))
    index = {d: i for i, d in enumerate(days)}
    ordered = lines.sort(["game_date", "nba_player_id"])
    out: dict[str, Any] = {
        "dates": [d.isoformat() for d in days],
        "players": ordered["nba_player_id"].cast(pl.Int64).to_list(),
        "day": [index[d] for d in ordered["game_date"].to_list()],
        "team": ordered["nba_team_id"].cast(pl.Int64).to_list(),
        "min": [round(m or 0) for m in ordered["minutes"].to_list()],
    }
    for s in STATS:
        out[s] = [int(v or 0) for v in ordered[s].to_list()]
    return out


def _positions(roster: pl.DataFrame, season: str) -> pl.DataFrame:
    """Each player's position from his rosters up to `season` (the latest wins)."""
    return (
        roster.filter((pl.col("season") <= season) & pl.col("nba_position").is_not_null())
        .sort("season")
        .group_by("nba_player_id")
        .agg(pl.col("nba_position").last().alias("season_position"))
        .with_columns(pl.col("nba_player_id").cast(pl.Int64))
    )


def build(wh: Any, rules: Any, season: str) -> dict[str, Any]:  # pragma: no cover - needs BigQuery
    """The replay document for one season (leak-free values + real lines)."""
    from fantasy_pipeline.draft_replay_run import OURS, _leak_free, _ours_method  # noqa: PLC0415

    values = _leak_free(wh, rules, season, lambda s: [(OURS, _ours_method(wh, s, season), False)])[
        OURS
    ].with_columns(pl.col("nba_player_id").cast(pl.Int64))
    lines = wh.read(LINES_SQL.format(season=season)).with_columns(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("game_date").cast(pl.Date)
    )
    teams = (
        lines.sort("game_date")
        .group_by("nba_player_id")
        .agg(pl.col("team_abbreviation").first().alias("team"))
    )
    names = wh.read(NAMES_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
    positions = _positions(wh.read(ROSTER_SQL), season)
    ids = pl.concat([values.select("nba_player_id"), lines.select("nba_player_id")]).unique()
    table = (
        ids.join(values, on="nba_player_id", how="left")
        .join(teams, on="nba_player_id", how="left")
        .join(names.rename({"player_name": "name"}), on="nba_player_id", how="left")
        .join(positions, on="nba_player_id", how="left")
        .sort(pl.col("overall_rank").fill_null(10_000), "nba_player_id")
    )
    players = [
        {
            "id": r["nba_player_id"],
            "name": r["name"] or r.get("player_name") or str(r["nba_player_id"]),
            "team": r["team"],
            # that season's rosters first; today's profile only as a fallback
            "pos": r["season_position"] or r.get("nba_position"),
            "usd": round(float(r["dollars"] or 0.0), 1),
            "rank": r["overall_rank"],
            "z": [round(float(r.get(f"s_{c}") or 0.0), 2) for c in CATEGORY_ORDER],
        }
        for r in table.iter_rows(named=True)
    ]
    days = sorted(set(lines["game_date"].to_list()))
    return {
        "season": season,
        "method": OURS,
        "players": players,
        "weeks": weeks(days),
        "lines": compact_lines(lines),
    }


def run_job(
    work: Workspace, build_season: Callable[[str], dict[str, Any]], seasons: Sequence[str] = SEASONS
) -> int:
    """Builds and publishes each season whose file is missing; returns how many were written."""
    written = 0
    for season in seasons:
        if work.exists(path(season)):
            continue
        work.write_text(path(season), json.dumps(build_season(season), separators=(",", ":")))
        written += 1
    return written


def available(work: Workspace, seasons: Sequence[str] = SEASONS) -> list[str]:
    return [s for s in seasons if work.exists(path(s))]
