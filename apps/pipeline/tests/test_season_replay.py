"""SIM-001: season replay files (weeks, compact lines, build-once job)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import polars as pl

from fantasy_pipeline import season_replay as sr
from fantasy_pipeline.workspace import Workspace


def test_weeks_run_monday_to_sunday_with_a_partial_first_week() -> None:
    # 2024-25 opened on Tuesday 22 Oct 2024
    days = [date(2024, 10, 22), date(2024, 10, 27), date(2024, 10, 28), date(2024, 11, 10)]
    weeks = sr.weeks(days)
    assert weeks[0] == {"week": 1, "start": "2024-10-22", "end": "2024-10-27"}
    assert weeks[1] == {"week": 2, "start": "2024-10-28", "end": "2024-11-03"}
    assert weeks[-1] == {"week": 3, "start": "2024-11-04", "end": "2024-11-10"}
    assert len(weeks) == 3


def _lines() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nba_player_id": [1, 1, 2],
            "game_date": [date(2024, 10, 22), date(2024, 10, 24), date(2024, 10, 22)],
            "nba_team_id": [10, 10, 20],
            "minutes": [33.6, 30.2, 12.0],
            **{c: [10, 12, 2] for c in sr.STATS},
        }
    )


def test_compact_lines_are_columnar_and_round_trip() -> None:
    packed = sr.compact_lines(_lines())
    assert packed["dates"] == ["2024-10-22", "2024-10-24"]
    # sorted by date, then player
    assert packed["players"] == [1, 2, 1]
    assert packed["day"] == [0, 0, 1]
    assert packed["min"] == [34, 12, 30]
    assert packed["pts"] == [10, 2, 12]
    assert set(sr.STATS) <= set(packed)


def test_job_builds_only_missing_seasons(tmp_path: Path) -> None:
    w = Workspace(str(tmp_path))
    built: list[str] = []

    def fake_build(season: str) -> dict[str, object]:
        built.append(season)
        return {"season": season}

    assert sr.run_job(w, fake_build, seasons=("2023-24", "2024-25")) == 2
    assert json.loads(w.read_text(sr.path("2023-24"))) == {"season": "2023-24"}
    assert sr.run_job(w, fake_build, seasons=("2023-24", "2024-25")) == 0  # already published
    assert built == ["2023-24", "2024-25"]


def test_available_lists_published_seasons(tmp_path: Path) -> None:
    w = Workspace(str(tmp_path))
    sr.run_job(w, lambda s: {"season": s}, seasons=("2024-25",))
    assert sr.available(w) == ["2024-25"]


def test_positions_come_from_that_seasons_rosters() -> None:
    roster = pl.DataFrame(
        {
            "season": ["2023-24", "2024-25", "2025-26", "2023-24"],
            "nba_player_id": [1, 1, 1, 2],
            "nba_position": ["G", "G-F", "F", "C"],
        }
    )
    pos = {
        r["nba_player_id"]: r["season_position"]
        for r in sr._positions(roster, "2024-25").iter_rows(named=True)
    }
    assert pos == {1: "G-F", 2: "C"}  # the latest up to the season; nothing from 2025-26
