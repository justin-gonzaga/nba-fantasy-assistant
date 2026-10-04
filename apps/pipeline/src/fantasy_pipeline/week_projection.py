"""Rest-of-week projections from stored snapshots (MVP-001).

Reads the latest schedule (cdn.nba.com), team rosters (stats.nba.com), the latest injury report
and the draft per-game projections; writes one row per NBA player for the fantasy week.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import polars as pl

from dikit.errors import ContractViolation
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_core.gamedate import game_date
from fantasy_ingest import injury_report, nba_cdn, nba_stats
from fantasy_models import inseason, weekly

SEASON = "2026-27"
# Relative to the workspace root (INFRA-006).
PROJECTIONS = "predictions/preseason_projection.parquet"
OUT = "predictions/week_projection.parquet"
NEXT_OUT = "predictions/next_week_projection.parquet"  # DEC-010


@dataclass(frozen=True)
class Result:
    table: pl.DataFrame
    week: weekly.Week
    today: date
    injury_report: str | None
    unmatched: list[str]


def default_week(today: date) -> weekly.Week:
    """Monday to Sunday around `today` (Yahoo's usual weekly matchup)."""
    start = today - timedelta(days=today.weekday())
    return weekly.Week(start, start + timedelta(days=6))


def _schedule(store: SnapshotStore, season: str) -> bytes:
    raw = store.latest(nba_cdn.SOURCE, "schedule", f"season={season}")
    if raw is None:
        msg = "no schedule snapshot: run `nba-daily` first"
        raise ContractViolation(msg)
    return raw


def roster(store: SnapshotStore, season: str, teams: list[nba_cdn.Team]) -> pl.DataFrame:
    rows = []
    for t in teams:
        req = nba_stats.common_team_roster(t.team_id, season)
        payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
        for r in nba_stats.result_set(payload) if payload else []:
            rows.append(
                {
                    "nba_player_id": int(str(r["PLAYER_ID"])),
                    "player_name": str(r["PLAYER"]),
                    "team": t.tricode,
                }
            )
    schema = {"nba_player_id": pl.Int64, "player_name": pl.String, "team": pl.String}
    return pl.DataFrame(rows, schema=schema)


def latest_injuries(store: SnapshotStore, today: date) -> tuple[pl.DataFrame | None, str | None]:
    """Today's newest report (not simply the newest fetch: backfills add old reports)."""
    found = injury_report.stored_report(store, today)
    if found is None:
        return None, None
    key, rows = found
    df = pl.DataFrame(rows).with_columns(pl.col("game_date").str.to_date())
    return df.filter(pl.col("game_date") >= today), key


SEASON_COLS = {
    "PTS": "pts",
    "REB": "reb",
    "AST": "ast",
    "STL": "stl",
    "BLK": "blk",
    "FG3M": "fg3m",
    "TOV": "tov",
    "FGM": "fgm",
    "FGA": "fga",
    "FTM": "ftm",
    "FTA": "fta",
}


def newest_game(store: SnapshotStore, season: str) -> date | None:
    """The latest game date in the stored game logs (None before the season's first game)."""
    req = nba_stats.league_game_log(season, "P")
    payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
    rows = nba_stats.result_set(payload) if payload else []
    days = [date.fromisoformat(str(r["GAME_DATE"])[:10]) for r in rows if r.get("GAME_DATE")]
    return max(days) if days else None


def stale_since(newest: date | None, schedule: pl.DataFrame, today: date) -> date | None:
    """The first scheduled game after `newest` and before today, i.e. missing from the data
    (INFRA-007: the PC's fetch didn't run). None when the data is current, or pre-season."""
    if newest is None:
        return None
    missing = schedule.filter((pl.col("game_date") > newest) & (pl.col("game_date") < today))
    return missing["game_date"].min() if missing.height else None  # type: ignore[return-value]


def season_so_far(store: SnapshotStore, season: str) -> pl.DataFrame | None:
    """Per player: games and totals this season from the latest stored game logs (None if none)."""
    req = nba_stats.league_game_log(season, "P")
    payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
    rows = nba_stats.result_set(payload) if payload else []
    if not rows:
        return None
    logs = pl.DataFrame(rows)
    return logs.group_by(pl.col("PLAYER_ID").cast(pl.Int64).alias("nba_player_id")).agg(
        pl.len().alias("games"),
        *[pl.col(c).sum().cast(pl.Float64).alias(s) for c, s in SEASON_COLS.items()],
    )


def schedule_frame(raw: bytes) -> pl.DataFrame:
    """Regular-season games with both teams known: game_id, game_date, away, home."""
    games = [g for g in nba_cdn.parse_schedule(raw) if g.regular_season and g.home and g.away]
    return pl.DataFrame(
        {
            "game_id": [g.game_id for g in games],
            "game_date": [g.game_date for g in games],
            "away": [g.away for g in games],
            "home": [g.home for g in games],
        },
        schema={"game_id": pl.String, "game_date": pl.Date, "away": pl.String, "home": pl.String},
    )


def run(
    store: SnapshotStore,
    clock: Clock,
    projections: pl.DataFrame,
    *,
    season: str = SEASON,
    week: weekly.Week | None = None,
) -> Result:
    today = game_date(clock.now())
    wk = week or default_week(today)
    raw = _schedule(store, season)
    teams = nba_cdn.teams(raw)
    schedule = schedule_frame(raw)
    players = roster(store, season, teams)
    injuries, report_key = latest_injuries(store, today)
    names = {t.full_name: t.tricode for t in teams}
    unmatched = (
        weekly.match_injuries(injuries, players, names).unmatched if injuries is not None else []
    )
    per_game = projections.select("nba_player_id", "stat", "mean")
    so_far = season_so_far(store, season)
    if so_far is not None:  # ANL-005 shipped: blend the draft projection with the season so far
        per_game = inseason.update_long(per_game, so_far)
    table = weekly.project(
        per_game,
        players,
        schedule,
        week=wk,
        today=today,
        injuries=injuries,
        teams=names,
    )
    stale = stale_since(newest_game(store, season), schedule, today)
    table = table.with_columns(
        pl.lit(today).alias("as_of_day"), pl.lit(stale, dtype=pl.Date).alias("stale_since")
    )
    return Result(table, wk, today, report_key, unmatched)


def run_next(
    store: SnapshotStore, clock: Clock, projections: pl.DataFrame, *, season: str = SEASON
) -> Result:
    """Next week's table (DEC-010: the add/drop horizon): every game of next week, from the same
    projections, without today's injury report (it describes today, not next week)."""
    today = game_date(clock.now())
    nxt = default_week(today + timedelta(days=7))
    raw = _schedule(store, season)
    teams = nba_cdn.teams(raw)
    schedule = schedule_frame(raw)
    per_game = projections.select("nba_player_id", "stat", "mean")
    so_far = season_so_far(store, season)
    if so_far is not None:
        per_game = inseason.update_long(per_game, so_far)
    table = weekly.project(
        per_game,
        roster(store, season, teams),
        schedule,
        week=nxt,
        today=nxt.start,
        injuries=None,
        teams={t.full_name: t.tricode for t in teams},
    )
    return Result(table.with_columns(pl.lit(today).alias("as_of_day")), nxt, today, None, [])
