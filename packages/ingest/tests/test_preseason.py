import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import nba_stats, preseason


def _logs(ids: list[str]) -> bytes:
    return json.dumps(
        {
            "resultSets": [
                {
                    "name": "LeagueGameLog",
                    "headers": ["GAME_ID", "GAME_DATE"],
                    "rowSet": [[g, "2025-10-05"] for g in ids],
                }
            ]
        }
    ).encode()


def _box() -> bytes:
    side = {"players": [{"personId": 1, "position": "G"}, {"personId": 2, "position": ""}]}
    return json.dumps({"boxScoreTraditional": {"homeTeam": side, "awayTeam": side}}).encode()


class Fake:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        self.calls.append(url)
        if url.endswith("boxscoretraditionalv3"):
            return _box()
        return _logs(["0012500001", "0012500002", "0012500001"])


def test_preseason_keys_do_not_collide_with_regular_season() -> None:
    reg = nba_stats.league_game_log("2025-26", "P")
    pre = nba_stats.league_game_log("2025-26", "P", nba_stats.PRE_SEASON)
    assert reg.key == "season=2025-26/player_or_team=P"
    assert pre.key == "season=2025-26/player_or_team=P/season_type=pre_season"
    assert pre.params["SeasonType"] == "Pre Season"


def test_v3_box_score_row_count() -> None:
    assert nba_stats.row_count(_box()) == 4
    assert nba_stats.box_score_traditional("0012500001").params["GameID"] == "0012500001"


def test_backfill_fetches_logs_then_each_game_once_and_resumes() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    clock = FrozenClock(datetime(2026, 9, 26, tzinfo=UTC))
    fake = Fake()
    logs, boxes = preseason.backfill(store, fake, ["2025-26"], clock)
    assert (logs.fetched, boxes.fetched) == (2, 2)  # P + T logs; 2 unique games
    again = preseason.backfill(store, Fake(), ["2025-26"], clock)
    assert (again[0].fetched, again[1].fetched) == (0, 0)
