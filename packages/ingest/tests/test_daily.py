import copy
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import daily, nba_cdn, nba_stats

FIX = Path(__file__).parent / "fixtures" / "nba_cdn"
BOX = (FIX / "cdn_boxscore_sample.json").read_bytes()


def _schedule(statuses: list[int]) -> bytes:
    s = json.loads((FIX / "cdn_schedule_league_v2_sample.json").read_text(encoding="utf-8"))
    s = copy.deepcopy(s)
    for g, st in zip(s["leagueSchedule"]["gameDates"][0]["games"], statuses, strict=True):
        g["gameStatus"] = st
    return json.dumps(s).encode()


class Cdn:
    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        return _schedule([3, 3, 3]) if url == nba_cdn.SCHEDULE_URL else BOX


class Stats:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        self.keys.append(f"{(params or {}).get('Season')}/{(params or {}).get('PlayerOrTeam')}")
        rs = {"name": "LeagueGameLog", "headers": ["GAME_ID"], "rowSet": [["0022600001"]]}
        return json.dumps({"resultSets": [rs]}).encode()


def test_default_day_is_yesterday_in_us_eastern() -> None:
    # 01:00 UTC on 21 Oct is still 20 Oct in New York, so "yesterday" there is 19 Oct.
    assert daily.default_day(datetime(2026, 10, 21, 1, tzinfo=UTC)) == date(2026, 10, 19)
    assert daily.default_day(datetime(2026, 10, 21, 20, tzinfo=UTC)) == date(2026, 10, 20)


def test_refresh_stores_cdn_and_a_new_game_log_snapshot_each_run() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    stats = Stats()
    clock = FrozenClock(datetime(2026, 10, 21, 20, tzinfo=UTC))
    rep = daily.refresh(store, Cdn(), stats, clock, season="2026-27")
    assert rep.day == date(2026, 10, 20)
    assert rep.cdn.box_scores_fetched == 3
    assert rep.game_logs_fetched == 2
    assert sorted(stats.keys) == ["2026-27/P", "2026-27/T"]

    # The next day's run fetches the (changed) game logs again, as new snapshots.
    later = FrozenClock(datetime(2026, 10, 22, 20, tzinfo=UTC))
    rep2 = daily.refresh(store, Cdn(), Stats(), later, season="2026-27")
    assert rep2.game_logs_fetched == 2
    req = nba_stats.league_game_log("2026-27", "P")
    assert len([m for m in store.manifest(nba_stats.SOURCE) if m["key"] == req.key]) == 2


class Injuries:
    def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
        name = "Injury-Report_2026-01-20_05_00PM.pdf"
        return (FIX.parent / "injury_reports" / name).read_bytes() if url.endswith(name) else None


def test_refresh_also_stores_todays_latest_injury_report() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    clock = FrozenClock(datetime(2026, 1, 20, 22, 20, tzinfo=UTC))  # 5:20 PM ET
    rep = daily.refresh(store, Cdn(), Stats(), clock, season="2025-26", injuries=Injuries())
    assert rep.injury_rows is not None
    assert rep.injury_rows > 15
    later = FrozenClock(datetime(2026, 1, 20, 22, 21, tzinfo=UTC))
    again = daily.refresh(store, Cdn(), Stats(), later, season="2025-26", injuries=Injuries())
    assert again.injury_rows is None  # nothing new
