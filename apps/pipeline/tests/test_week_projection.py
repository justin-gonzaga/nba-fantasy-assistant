import json
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

from dikit.errors import ContractViolation
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import injury_report, nba_cdn, nba_stats
from fantasy_pipeline import week_projection as wp

FIX = Path(__file__).parents[3] / "packages" / "ingest" / "tests" / "fixtures"
BOS = 1610612738
# 20 Oct 2026, 14:00 UTC = 10:00 ET: the morning of opening night (BOS@DET that evening).
NOW = datetime(2026, 10, 20, 14, tzinfo=UTC)


def _store() -> SnapshotStore:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    sched = (FIX / "nba_cdn" / "cdn_schedule_league_v2_sample.json").read_bytes()
    store.write(nba_cdn.SOURCE, "schedule", "season=2026-27", sched, NOW)
    req = nba_stats.common_team_roster(BOS, "2026-27")
    roster = (FIX / "nba_stats" / "team_roster_BOS_2026_27.json").read_bytes()
    store.write(nba_stats.SOURCE, req.endpoint, req.key, roster, NOW)
    return store


PROJ = pl.DataFrame(
    {
        "nba_player_id": [1641759, 1641759, 1641759],
        "stat": ["pts", "reb", "games"],
        "mean": [10.0, 5.0, 82.0],
    }
)


def test_week_is_monday_to_sunday() -> None:
    wk = wp.default_week(date(2026, 10, 21))  # a Wednesday
    assert (wk.start, wk.end) == (date(2026, 10, 19), date(2026, 10, 25))


def test_run_projects_rostered_players_from_the_stored_snapshots() -> None:
    res = wp.run(_store(), FrozenClock(NOW), PROJ)
    assert res.today == date(2026, 10, 20)
    assert res.injury_report is None
    t = res.table
    assert t["as_of_day"].unique().to_list() == [date(2026, 10, 20)]
    assert t.height == 21  # the BOS roster
    mitchell = t.filter(pl.col("nba_player_id") == 1641759).row(0, named=True)
    assert mitchell["team"] == "BOS"
    assert mitchell["plays_today"]
    assert mitchell["games_left"] == 1  # the sample schedule holds one BOS game
    assert mitchell["pts"] == pytest.approx(10.0)


def test_run_applies_the_latest_injury_report() -> None:
    store = _store()
    rows = {
        "extractor_version": injury_report.EXTRACTOR_VERSION,
        "valid_at": "2026-10-20T13:30:00+00:00",
        "rows": [
            {
                "game_date": "2026-10-20",
                "game_time": "07:00 (ET)",
                "matchup": "BOS@DET",
                "team": "Boston Celtics",
                "player": "Mitchell, Dillon",
                "status": "Out",
                "reason": "Injury/Illness - Left Ankle; Sprain",
            }
        ],
    }
    key = "report=2026-10-20_09_30AM"
    store.write(injury_report.SOURCE, "report_rows", key, json.dumps(rows).encode(), NOW)
    res = wp.run(store, FrozenClock(NOW), PROJ)
    assert res.injury_report == key
    assert res.unmatched == []
    mitchell = res.table.filter(pl.col("nba_player_id") == 1641759).row(0, named=True)
    assert mitchell["status_today"] == "Out"
    assert mitchell["exp_games"] == pytest.approx(0.0, abs=0.01)


def test_run_needs_a_schedule() -> None:
    empty = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    with pytest.raises(ContractViolation, match="nba-daily"):
        wp.run(empty, FrozenClock(NOW), PROJ)


def test_an_old_backfilled_report_is_not_used_for_today() -> None:
    store = _store()
    old = {"extractor_version": "1.0.0", "valid_at": "2025-04-09T21:30:00+00:00", "rows": []}
    store.write(
        injury_report.SOURCE, "report_rows", "report=2025-04-09_05PM", json.dumps(old).encode(), NOW
    )
    assert wp.run(store, FrozenClock(NOW), PROJ).injury_report is None


def test_the_season_so_far_updates_the_projection() -> None:
    store = _store()
    headers = ["PLAYER_ID", *wp.SEASON_COLS]
    rows = [[1641759, 30, 0, 0, 0, 0, 0, 0, 10, 20, 0, 0]] * 4  # 4 games of 30 points
    payload = json.dumps(
        {"resultSets": [{"name": "LeagueGameLog", "headers": headers, "rowSet": rows}]}
    )
    req = nba_stats.league_game_log("2026-27", "P")
    store.write(nba_stats.SOURCE, req.endpoint, req.key, payload.encode(), NOW)
    res = wp.run(store, FrozenClock(NOW), PROJ)
    mitchell = res.table.filter(pl.col("nba_player_id") == 1641759).row(0, named=True)
    assert mitchell["pts"] > 10.0  # the 10-point projection moved toward 30 a game


def test_run_next_projects_next_week_from_the_schedule_without_todays_report() -> None:
    res = wp.run_next(_store(), FrozenClock(NOW), PROJ)
    assert (res.week.start, res.week.end) == (date(2026, 10, 26), date(2026, 11, 1))
    assert res.injury_report is None  # today's report doesn't describe next week
    t = res.table
    assert t["as_of_day"].unique().to_list() == [date(2026, 10, 20)]
    assert t.height == 21
    assert t["games_left"].sum() == 0  # the sample schedule has no games next week


def test_newest_game_comes_from_the_stored_game_logs() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    assert wp.newest_game(store, "2026-27") is None  # pre-season: no logs yet
    req = nba_stats.league_game_log("2026-27", "P")
    payload = {
        "resultSets": [
            {
                "name": "LeagueGameLog",
                "headers": ["PLAYER_ID", "GAME_DATE"],
                "rowSet": [[1, "2026-10-20"], [2, "2026-10-22"]],
            }
        ]
    }
    store.write(nba_stats.SOURCE, req.endpoint, req.key, json.dumps(payload).encode(), NOW)
    assert wp.newest_game(store, "2026-27") == date(2026, 10, 22)


def test_stale_since_is_the_first_scheduled_game_missing_from_the_logs() -> None:
    schedule = pl.DataFrame(
        {"game_date": [date(2026, 10, 21), date(2026, 10, 23), date(2026, 10, 26)]}
    )
    today = date(2026, 10, 25)
    assert wp.stale_since(date(2026, 10, 21), schedule, today) == date(2026, 10, 23)
    assert wp.stale_since(date(2026, 10, 23), schedule, today) is None  # no game since: fresh
    assert wp.stale_since(None, schedule, today) is None  # pre-season
