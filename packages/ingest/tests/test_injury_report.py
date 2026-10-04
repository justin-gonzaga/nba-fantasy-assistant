import json
import uuid
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import injury_report as ir

FIX = Path(__file__).parent / "fixtures" / "injury_reports"
NEW = FIX / "Injury-Report_2026-01-20_05_00PM.pdf"
LEGACY = FIX / "Injury-Report_2025-03-10_05PM.pdf"
OLD = FIX / "Injury-Report_2022-01-10_05PM.pdf"


def test_new_layout_matches_the_hand_checked_first_rows() -> None:
    rep = ir.parse(NEW.read_bytes())
    expected = json.loads((FIX / f"{NEW.stem}.expected_first12.json").read_text(encoding="utf-8"))
    got = [
        {
            "GameDate": r.game_date.strftime("%m/%d/%Y"),
            "GameTime": r.game_time,
            "Matchup": r.matchup,
            "Team": r.team,
            "PlayerName": r.player,
            "CurrentStatus": r.status,
            "Reason": r.reason,
        }
        for r in rep.rows[:12]
    ]
    assert got == expected
    assert rep.valid_at == datetime(2026, 1, 20, 22, 0, tzinfo=UTC)  # 5:00 PM ET


def test_every_row_is_complete_and_uses_a_known_status() -> None:
    for pdf in (NEW, LEGACY):
        rep = ir.parse(pdf.read_bytes())
        assert len(rep.rows) > 15
        for r in rep.rows:
            assert r.status in ir.STATUSES
            assert r.player
            assert r.team
            assert r.matchup
            assert r.reason


def test_legacy_filename_report_time_comes_from_the_header() -> None:
    rep = ir.parse(LEGACY.read_bytes())
    assert rep.valid_at.date() == date(2025, 3, 10)


def test_old_2021_22_layout_parses_the_same_way() -> None:
    # DISC-005 found 0 rows with the spike parser; header-derived columns handle it (DATA-007 AC4).
    rep = ir.parse(OLD.read_bytes())
    assert rep.valid_at == datetime(2022, 1, 10, 22, 30, tzinfo=UTC)  # the "05PM" file is 5:30 PM
    assert len(rep.rows) == 99
    first = rep.rows[0]
    assert (first.matchup, first.team, first.player, first.status) == (
        "MIL@CHA",
        "Charlotte Hornets",
        "Carey Jr., Vernon",
        "Out",
    )
    holiday = next(r for r in rep.rows if r.player == "Holiday, Jrue")
    assert (holiday.team, holiday.reason) == (
        "Milwaukee Bucks",
        "Injury/Illness - Left Ankle; Soreness",
    )


def test_a_page_without_a_column_header_is_an_unknown_layout() -> None:
    words = [
        {"text": t, "x0": 10.0 * i, "top": 50.0} for i, t in enumerate(["Some", "other", "PDF"])
    ]
    with pytest.raises(ir.UnknownLayout):
        ir._header(ir._lines(words))


def test_candidate_urls_cover_both_filename_formats_newest_first() -> None:
    urls = ir.candidate_urls(date(2026, 1, 20), latest=datetime(2026, 1, 20, 22, 20, tzinfo=UTC))
    assert urls[0].endswith("Injury-Report_2026-01-20_05_15PM.pdf")  # 5:20 PM ET -> 5:15 first
    assert urls[1].endswith("Injury-Report_2026-01-20_05_00PM.pdf")
    assert any(u.endswith("Injury-Report_2026-01-20_04PM.pdf") for u in urls)  # the 4:30 report


class Fake:
    """Serves the fixture PDF at one URL and 'not published' (None) everywhere else."""

    def __init__(self, url: str) -> None:
        self.url = url
        self.calls: list[str] = []

    def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
        self.calls.append(url)
        return NEW.read_bytes() if url == self.url else None


def test_fetch_latest_stores_the_pdf_and_versioned_rows_once() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    clock = FrozenClock(datetime(2026, 1, 20, 22, 20, tzinfo=UTC))
    url = ir.URL.format(day="2026-01-20", slot="05_00PM")
    fake = Fake(url)
    rep = ir.fetch_latest(store, fake, clock, date(2026, 1, 20))
    assert rep is not None
    assert rep.rows
    assert fake.calls[:2] == [url.replace("05_00PM", "05_15PM"), url]
    key = "report=2026-01-20_05_00PM"
    assert store.has(ir.SOURCE, "report_pdf", key)
    rows = json.loads(store.latest(ir.SOURCE, "report_rows", key) or b"{}")
    assert rows["extractor_version"] == ir.EXTRACTOR_VERSION
    assert rows["valid_at"] == "2026-01-20T22:00:00+00:00"
    # A second run finds the same report already stored and doesn't store it again.
    again = Fake(url)
    assert ir.fetch_latest(store, again, clock, date(2026, 1, 20)) is None


def test_fetch_latest_returns_none_when_nothing_is_published() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    clock = FrozenClock(datetime(2026, 10, 20, 14, tzinfo=UTC))
    assert ir.fetch_latest(store, Fake("nowhere"), clock, date(2026, 10, 20)) is None


def test_backfill_picks_the_slot_by_latest_but_stamps_the_real_fetch_time() -> None:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    fetched_at = datetime(2026, 9, 28, 3, tzinfo=UTC)
    url = ir.URL.format(day="2026-01-20", slot="05_00PM")
    rep = ir.fetch_latest(
        store,
        Fake(url),
        FrozenClock(fetched_at),
        date(2026, 1, 20),
        latest=datetime(2026, 1, 20, 22, 20, tzinfo=UTC),
    )
    assert rep is not None
    meta = next(m for m in store.manifest(ir.SOURCE) if m["endpoint"] == "report_rows")
    assert meta["observed_at"] == fetched_at.isoformat()
    rows = ir.stored_rows(store, date(2026, 1, 20))
    assert len(rows) == len(rep.rows)
    assert ir.stored_rows(store, date(2026, 1, 21)) == []
