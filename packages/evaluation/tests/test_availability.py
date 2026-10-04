from datetime import date

import polars as pl
import pytest

from fantasy_evaluation import availability as av

REPORT = pl.DataFrame(
    {
        "game_date": [date(2025, 1, 10)] * 4 + [date(2025, 1, 11)],
        "team": ["Boston Celtics", "Boston Celtics", "LA Clippers", "LA Clippers", "LA Clippers"],
        "player": [
            "Tatum, Jayson",
            "Holiday, Jrue",
            "Harden, James",
            "Nobody, Some",
            "Harden, James",
        ],
        "status": ["Questionable", "Out", "Probable", "Out", "Questionable"],
    }
)
LOGS = pl.DataFrame(
    {
        "PLAYER_ID": [1, 2, 3],
        "PLAYER_NAME": ["Jayson Tatum", "Jrue Holiday", "James Harden"],
        "TEAM_NAME": ["Boston Celtics", "Boston Celtics", "LA Clippers"],
        "GAME_DATE": ["2025-01-10", "2025-01-09", "2025-01-10"],
    }
)


def test_outcomes_join_report_rows_to_whether_the_player_played_that_day() -> None:
    res = av.outcomes(REPORT, LOGS)
    got = {(r["player"], r["game_date"]): r["played"] for r in res.rows.iter_rows(named=True)}
    assert got == {
        ("Tatum, Jayson", date(2025, 1, 10)): True,
        ("Holiday, Jrue", date(2025, 1, 10)): False,  # he appears in the season logs, not that day
        ("Harden, James", date(2025, 1, 10)): True,
        ("Harden, James", date(2025, 1, 11)): False,
    }
    assert res.unmatched == 1  # never appears in the season's logs, so it can't be scored


def test_rates_give_a_proportion_and_a_bootstrap_interval_per_status() -> None:
    rows = pl.DataFrame(
        {
            "status": ["Out"] * 50 + ["Questionable"] * 100,
            "played": [False] * 50 + [(i // 20) % 2 == 0 for i in range(50, 150)],
            "game_date": [date(2025, 1, 1 + i % 20) for i in range(150)],
        }
    )
    r = {x["status"]: x for x in av.rates(rows, n_boot=300, seed=1).iter_rows(named=True)}
    assert r["Out"]["rate"] == 0.0
    assert r["Out"]["n"] == 50
    q = r["Questionable"]
    assert q["rate"] == pytest.approx(0.5)
    assert q["lo"] < 0.5 < q["hi"]
    assert q["hi"] - q["lo"] < 0.3


def test_statuses_are_ordered_from_most_to_least_available() -> None:
    rows = pl.DataFrame(
        {
            "status": ["Out", "Available", "Doubtful"],
            "played": [False, True, False],
            "game_date": [date(2025, 1, 1)] * 3,
        }
    )
    assert av.rates(rows, n_boot=10, seed=0)["status"].to_list() == ["Available", "Doubtful", "Out"]
