import json
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

from dikit.errors import ContractViolation
from fantasy_pipeline import daily_brief as db
from fantasy_pipeline.workspace import Workspace

STATS = ["pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta"]
N = 40


def _week() -> pl.DataFrame:
    rows = []
    for i in range(N):
        scale = (N - i) / N
        row = {
            "nba_player_id": 100 + i,
            "player_name": f"Player {chr(65 + i % 26)}{chr(65 + i // 26)}",
            "team": "AAA",
            "games_left": 3,
            "exp_games": 3.0,
            "plays_today": i % 3 != 0,
            "status_today": "Questionable" if i == 4 else None,
        }
        row |= dict.fromkeys(STATS, 10 * scale)
        row["fga"], row["fta"] = 20 * scale, 10 * scale
        rows.append(row)
    return pl.DataFrame(rows)


def _values() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nba_player_id": [100 + i for i in range(N)],
            "value": [float(N - i) for i in range(N)],
            "nba_position": ["G", "F", "C", "G-F"] * (N // 4),
            "variant": ["all"] * N,
        }
    )


SLOTS = {"G": 3, "F": 3, "C": 1, "Util": 3, "BN": 4, "IL": 3}


def test_sample_league_is_a_snake_draft() -> None:
    lg = db.sample_league(_values(), teams=4, rounds=3)
    assert lg["my_team"] == [100, 107, 108]
    assert len(lg["rostered"]) == 12


def test_brief_from_a_sample_league_file(tmp_path: Path) -> None:
    path = tmp_path / "league.json"
    path.write_text(
        json.dumps(db.sample_league(_values(), teams=4, rounds=5, opp=2)), encoding="utf-8"
    )
    league = db.load_league(path, _week())
    md = db.run(_week(), _values(), league, SLOTS, date(2026, 10, 20))
    assert md.startswith("*Tue 20 Oct* · vs Team 3 (sample)")
    assert "*Pickups*" in md
    assert "cat. wins" in md


def test_league_names_resolve_and_unknown_names_fail(tmp_path: Path) -> None:
    week = _week()
    path = tmp_path / "league.json"
    path.write_text(json.dumps({"my_team": ["Player AA", 101], "opponent": []}), encoding="utf-8")
    assert db.load_league(path, week).my_team == [100, 101]
    path.write_text(json.dumps({"my_team": ["Nobody Here"]}), encoding="utf-8")
    with pytest.raises(ContractViolation, match="Nobody Here"):
        db.load_league(path, week)


def test_brief_refuses_a_week_table_from_another_day(tmp_path: Path) -> None:
    path = tmp_path / "league.json"
    path.write_text(json.dumps(db.sample_league(_values(), teams=4, rounds=5)), encoding="utf-8")
    week = _week().with_columns(pl.lit(date(2026, 9, 27)).alias("as_of_day"))
    with pytest.raises(ContractViolation, match="week-projection"):
        db.run(week, _values(), db.load_league(path, week), SLOTS, date(2026, 10, 20))


def test_compose_gives_the_markdown_and_a_json_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "league.json"
    path.write_text(
        json.dumps(db.sample_league(_values(), teams=4, rounds=5, opp=2)), encoding="utf-8"
    )
    league = db.load_league(path, _week())
    out = db.compose(_week(), _values(), league, SLOTS, date(2026, 10, 20))
    assert out.markdown == db.run(_week(), _values(), league, SLOTS, date(2026, 10, 20))
    snap = json.loads(json.dumps(out.snapshot))  # JSON-serialisable
    assert snap["schema"] == db.SNAPSHOT_SCHEMA
    assert snap["day"] == "2026-10-20"
    assert snap["week"] == {"start": "2026-10-19", "end": "2026-10-25"}
    assert snap["opponent_name"] == "Team 3 (sample)"
    assert set(snap["outlook"]) == {
        "pts",
        "reb",
        "ast",
        "stl",
        "blk",
        "fg3m",
        "tov",
        "fg_pct",
        "ft_pct",
    }
    assert set(snap["totals"]) == {"mine", "theirs"}
    assert {s["slot"] for s in snap["lineup"]} <= set(SLOTS)
    assert snap["pickups"]
    assert {"add_id", "add_name", "drop_id", "drop_name", "games_left", "gain", "helps"} <= set(
        snap["pickups"][0]
    )
    assert snap["sources"] == [{"name": "week projection", "as_of": None}]


def test_publish_writes_markdown_and_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "league.json"
    path.write_text(json.dumps(db.sample_league(_values(), teams=4, rounds=5)), encoding="utf-8")
    out = db.compose(_week(), _values(), db.load_league(path, _week()), SLOTS, date(2026, 10, 20))
    w = Workspace(str(tmp_path))
    db.publish(out, date(2026, 10, 20), datetime(2026, 10, 20, 20, 30, tzinfo=UTC), w)
    assert (tmp_path / "briefs" / "2026-10-20.md").read_text(encoding="utf-8") == out.markdown
    snap = json.loads((tmp_path / "briefs" / "2026-10-20.json").read_text(encoding="utf-8"))
    assert snap["generated_at"] == "2026-10-20T20:30:00+00:00"


def test_two_week_pickups_when_next_weeks_opponent_and_table_exist(tmp_path: Path) -> None:
    lg = db.sample_league(_values(), teams=4, rounds=5, opp=2)
    lg["opponent_next"] = lg["opponent"]
    path = tmp_path / "league.json"
    path.write_text(json.dumps(lg), encoding="utf-8")
    league = db.load_league(path, _week())
    out = db.compose(_week(), _values(), league, SLOTS, date(2026, 10, 20), next_week=_week())
    assert out.snapshot["horizon"] == db.TWO_WEEK
    # the sample free agents are all weaker: the two-week method stands pat (no pickups section)
    assert out.snapshot["pickups"] == [] or f"gain {db.TWO_WEEK}" in out.markdown
    without = db.compose(_week(), _values(), league, SLOTS, date(2026, 10, 20))
    assert without.snapshot["horizon"] == "this week"


def test_a_stale_week_table_is_flagged_first_in_the_brief_and_the_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "league.json"
    path.write_text(json.dumps(db.sample_league(_values(), teams=4, rounds=5)), encoding="utf-8")
    stale = _week().with_columns(pl.lit(date(2026, 10, 18), dtype=pl.Date).alias("stale_since"))
    out = db.compose(stale, _values(), db.load_league(path, stale), SLOTS, date(2026, 10, 20))
    assert out.markdown.startswith("⚠️ Stats are missing games since Sun 18 Oct")
    assert out.snapshot["stale_since"] == "2026-10-18"
    fresh = db.compose(_week(), _values(), db.load_league(path, _week()), SLOTS, date(2026, 10, 20))
    assert not fresh.markdown.startswith("⚠️")
    assert fresh.snapshot["stale_since"] is None
