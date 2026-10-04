import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dikit.errors import SourceUnavailable
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import nba_stats
from fantasy_pipeline import availability_study as st

FIX = Path(__file__).parents[3] / "packages" / "ingest" / "tests" / "fixtures"
PDF = FIX / "injury_reports" / "Injury-Report_2026-01-20_05_00PM.pdf"


def _logs() -> bytes:
    headers = ["PLAYER_ID", "PLAYER_NAME", "TEAM_NAME", "GAME_DATE"]
    rows = [
        [1, "Jordan Goodwin", "Phoenix Suns", "2026-01-20"],  # Available -> played
        [2, "Mark Williams", "Phoenix Suns", "2026-01-18"],  # Questionable -> didn't play that day
        [3, "Joel Embiid", "Philadelphia 76ers", "2026-01-19"],  # Out -> didn't play
    ]
    return json.dumps(
        {"resultSets": [{"name": "LeagueGameLog", "headers": headers, "rowSet": rows}]}
    ).encode()


class Reports:
    def __init__(self) -> None:
        self.calls = 0

    def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
        self.calls += 1
        return PDF.read_bytes() if url.endswith("2026-01-20_05_00PM.pdf") else None


def _store() -> SnapshotStore:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    req = nba_stats.league_game_log("2025-26", "P")
    store.write(nba_stats.SOURCE, req.endpoint, req.key, _logs(), datetime(2026, 9, 28, tzinfo=UTC))
    return store


def test_study_scores_report_rows_against_game_logs_and_reuses_stored_reports() -> None:
    store = _store()
    clock = FrozenClock(datetime(2026, 9, 28, 4, tzinfo=UTC))
    first = Reports()
    s = st.run(store, first, clock, ["2025-26"], n_boot=50)
    assert s.days == 3
    assert s.reports == 1  # only 20 Jan has a report in the fake
    assert s.missing == 2
    got = {r["player"]: r["played"] for r in s.rows.iter_rows(named=True)}
    assert got["Goodwin, Jordan"] is True
    assert got["Williams, Mark"] is False
    assert got["Embiid, Joel"] is False
    assert s.unmatched > 0  # rows for players absent from the tiny log fixture

    again = Reports()
    st.run(store, again, clock, ["2025-26"], n_boot=50)
    assert again.calls < first.calls  # 20 Jan is read from bronze; only missing days are retried

    md = st.report(s, datetime(2026, 9, 28, tzinfo=UTC))
    assert "| Available |" in md
    assert json.loads(st.rates_json(s))["rates"]["Out"] == 0.0


def test_study_needs_game_logs() -> None:
    empty = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    with pytest.raises(SourceUnavailable):
        st.run(empty, Reports(), FrozenClock(datetime(2026, 9, 28, tzinfo=UTC)), ["2025-26"])
