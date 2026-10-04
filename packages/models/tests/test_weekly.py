from datetime import date

import polars as pl
import pytest

from fantasy_models import weekly

PER_GAME = pl.DataFrame(
    {
        "nba_player_id": [1, 1, 1, 2, 2, 2],
        "stat": ["pts", "blk", "games", "pts", "blk", "games"],
        "mean": [20.0, 1.0, 82.0, 10.0, 2.0, 41.0],
    }
)
ROSTER = pl.DataFrame(
    {
        "nba_player_id": [1, 2],
        "player_name": ["Luka Dončić", "Jaren Jackson Jr."],
        "team": ["LAL", "MEM"],
    }
)
SCHEDULE = pl.DataFrame(
    {
        "game_id": ["g1", "g2", "g3", "g4"],
        "game_date": [
            date(2026, 10, 19),
            date(2026, 10, 21),
            date(2026, 10, 23),
            date(2026, 10, 22),
        ],
        "away": ["LAL", "LAL", "BOS", "MEM"],
        "home": ["GSW", "DEN", "LAL", "NYK"],
    }
)
WEEK = weekly.Week(start=date(2026, 10, 19), end=date(2026, 10, 25))


def test_name_key_handles_order_accents_and_suffixes() -> None:
    assert weekly.name_key("Dončić, Luka") == weekly.name_key("Luka Doncic") == "luka doncic"
    assert weekly.name_key("Jackson Jr., Jaren") == weekly.name_key("Jaren Jackson Jr.")
    assert weekly.name_key("Butler III, Jimmy") == "jimmy butler"


def test_games_left_counts_only_remaining_games_in_the_week() -> None:
    out = weekly.project(PER_GAME, ROSTER, SCHEDULE, week=WEEK, today=date(2026, 10, 21))
    luka = out.filter(pl.col("nba_player_id") == 1).row(0, named=True)
    assert luka["games_left"] == 2  # g2 (today) and g3; g1 is past
    assert luka["plays_today"]
    jjj = out.filter(pl.col("nba_player_id") == 2).row(0, named=True)
    assert jjj["games_left"] == 1
    assert not jjj["plays_today"]


def test_expected_totals_use_base_availability_without_a_report() -> None:
    out = weekly.project(PER_GAME, ROSTER, SCHEDULE, week=WEEK, today=date(2026, 10, 21))
    luka = out.filter(pl.col("nba_player_id") == 1).row(0, named=True)
    assert luka["exp_games"] == pytest.approx(2.0)  # 82/82 games -> plays every game
    assert luka["pts"] == pytest.approx(40.0)
    jjj = out.filter(pl.col("nba_player_id") == 2).row(0, named=True)
    assert jjj["exp_games"] == pytest.approx(0.5)  # 41/82
    assert jjj["blk"] == pytest.approx(1.0)


def test_injury_status_overrides_availability_on_its_game_date_only() -> None:
    injuries = pl.DataFrame(
        {
            "game_date": [date(2026, 10, 21)],
            "team": ["Los Angeles Lakers"],
            "player": ["Dončić, Luka"],
            "status": ["Out"],
        }
    )
    teams = {"Los Angeles Lakers": "LAL"}
    out = weekly.project(
        PER_GAME,
        ROSTER,
        SCHEDULE,
        week=WEEK,
        today=date(2026, 10, 21),
        injuries=injuries,
        teams=teams,
    )
    luka = out.filter(pl.col("nba_player_id") == 1).row(0, named=True)
    assert luka["exp_games"] == pytest.approx(1.0, abs=0.01)  # out today, normal on 23 Oct
    assert luka["status_today"] == "Out"


def test_unmatched_injury_names_are_reported_not_dropped_silently() -> None:
    injuries = pl.DataFrame(
        {
            "game_date": [date(2026, 10, 21)],
            "team": ["Los Angeles Lakers"],
            "player": ["Nobody, Some"],
            "status": ["Out"],
        }
    )
    res = weekly.match_injuries(injuries, ROSTER, {"Los Angeles Lakers": "LAL"})
    assert res.unmatched == ["Nobody, Some"]
    assert res.matched.height == 0


def test_status_probabilities_are_the_measured_ones() -> None:
    assert weekly.STATUS_PLAY_PROB_SOURCE.startswith("MEASURED")
    p = weekly.STATUS_PLAY_PROB
    assert p["Out"] < p["Doubtful"] < p["Questionable"] < p["Available"] < p["Probable"]
