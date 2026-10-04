import copy
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from dikit.errors import ContractViolation
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import nba_cdn

FIX = Path(__file__).parent / "fixtures" / "nba_cdn"
SCHEDULE = json.loads((FIX / "cdn_schedule_league_v2_sample.json").read_text(encoding="utf-8"))
BOX = (FIX / "cdn_boxscore_sample.json").read_bytes()


def _schedule(statuses: list[int], day: str = "10/20/2026 00:00:00") -> bytes:
    """The fixture's first date with its games set to the given statuses (3 = final)."""
    s = copy.deepcopy(SCHEDULE)
    games = s["leagueSchedule"]["gameDates"][0]["games"]
    s["leagueSchedule"]["gameDates"][0]["gameDate"] = day
    for g, st in zip(games, statuses, strict=True):
        g["gameStatus"] = st
    return json.dumps(s).encode()


class Fake:
    def __init__(self, schedule: bytes) -> None:
        self.schedule = schedule
        self.calls: list[str] = []

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        self.calls.append(url)
        return self.schedule if url == nba_cdn.SCHEDULE_URL else BOX


def test_parse_schedule_gives_one_row_per_game_with_teams_and_times() -> None:
    games = nba_cdn.parse_schedule(_schedule([1, 1, 1]))
    assert len(games) == 3
    g = games[0]
    assert g.game_id == "0022600001"
    assert g.game_date == date(2026, 10, 20)  # the US/Eastern game date
    assert g.tipoff_utc == datetime(2026, 10, 20, 19, 0, tzinfo=UTC)
    assert (g.away, g.home) == ("BOS", "DET")
    assert g.regular_season
    assert not g.final


def test_parse_schedule_rejects_an_unexpected_shape() -> None:
    with pytest.raises(ContractViolation):
        nba_cdn.parse_schedule(b'{"leagueSchedule": {}}')


def test_final_games_are_only_finished_games_on_that_date() -> None:
    games = nba_cdn.parse_schedule(_schedule([3, 2, 3]))
    finals = nba_cdn.final_game_ids(games, date(2026, 10, 20))
    assert finals == ["0022600001", "0022600003"]
    assert nba_cdn.final_game_ids(games, date(2026, 10, 21)) == []


def test_box_score_player_count() -> None:
    assert nba_cdn.box_score_players(BOX) > 0


def test_daily_stores_schedule_and_final_box_scores_and_is_idempotent() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    clock = FrozenClock(datetime(2026, 10, 21, 12, tzinfo=UTC))
    fake = Fake(_schedule([3, 2, 3]))
    rep = nba_cdn.daily(store, fake, clock, date(2026, 10, 20))
    assert (rep.schedule_games, rep.box_scores_fetched, rep.box_scores_skipped) == (3, 2, 0)
    assert store.has(nba_cdn.SOURCE, "schedule", "season=2026-27")
    assert store.has(nba_cdn.SOURCE, "boxscore", "game_id=0022600001")
    assert not store.has(nba_cdn.SOURCE, "boxscore", "game_id=0022600002")  # still live

    # A re-run for the same date adds a new schedule snapshot but never re-fetches box scores.
    later = FrozenClock(datetime(2026, 10, 21, 13, tzinfo=UTC))
    again = Fake(_schedule([3, 3, 3]))
    rep2 = nba_cdn.daily(store, again, later, date(2026, 10, 20))
    assert (rep2.box_scores_fetched, rep2.box_scores_skipped) == (1, 2)
    assert sum(url != nba_cdn.SCHEDULE_URL for url in again.calls) == 1


def test_teams_give_ids_tricodes_and_injury_report_names() -> None:
    ts = nba_cdn.teams(_schedule([1, 1, 1]))
    det = next(t for t in ts if t.tricode == "DET")
    assert (det.team_id, det.full_name) == (1610612765, "Detroit Pistons")
    assert len(ts) == 6  # 3 games in the sample
