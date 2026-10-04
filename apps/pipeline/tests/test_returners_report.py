from datetime import UTC, datetime

import polars as pl
import pytest

from fantasy_pipeline import returners_report as rr

TEAM_GAMES = 80


def _hist() -> pl.DataFrame:
    """40 rotation players a season; half skip the next year and return the year after."""
    rows = []
    pid = 0
    for y in range(2015, 2026):
        s = f"{y}-{(y + 1) % 100:02d}"
        for i in range(40):
            pid += 1
            rows.append((pid, s, 70, 30.0, 26.0))
            if i < 20 and y + 2 <= 2025:
                # lost season: no row next year; return the year after with 50 games
                nxt = f"{y + 2}-{(y + 3) % 100:02d}"
                rows.append((pid, nxt, 50, 28.0, 28.0))
    df = pl.DataFrame(
        rows,
        schema=["nba_player_id", "season", "games_played", "mpg", "age"],
        orient="row",
    )
    return df.with_columns(
        pl.lit(TEAM_GAMES).alias("season_team_games"),
        (pl.col("games_played") * pl.col("mpg")).alias("minutes"),
    ).drop("mpg")


def test_fold_rows_use_only_earlier_cohorts_and_r_never_lowers() -> None:
    rows = rr.fold_rows(_hist(), "2025-26")
    assert rows.height > 0
    assert (rows["r"] >= rows["current"]).all()
    assert str(rows["season"].min()) >= "2021-22"


def test_accuracy_reports_a_positive_gap_when_r_is_closer() -> None:
    rows = pl.DataFrame(
        {
            "realised": [0.6] * 40,
            "current": [0.3] * 40,
            "r": [0.6] * 40,
            "season": ["2021-22"] * 40,
            "nba_player_id": list(range(40)),
            "age": [30.0] * 40,
        }
    )
    acc = rr.accuracy(rows, n_boot=200)
    assert acc.ci[0] > 0
    assert acc.mae_r == pytest.approx(0.0)
    assert rr.calibration_gap(rows) == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("acc_low", "gap", "replay_low", "ship"),
    [
        (0.05, 0.02, -0.001, True),
        (-0.01, 0.02, -0.001, False),  # accuracy CI includes 0
        (0.05, 0.09, -0.001, False),  # miscalibrated
        (0.05, 0.02, -0.006, False),  # replay lower bound at or below the margin
        (0.05, 0.08, -0.004, True),  # boundary: gap exactly at the limit passes
    ],
)
def test_one_failed_check_keeps_the_current_method(
    acc_low: float, gap: float, replay_low: float, ship: bool
) -> None:
    acc = rr.Accuracy(0.2, 0.1, (acc_low, acc_low + 0.1), 30)
    assert rr.decide(acc, gap, replay_low).ship is ship


def test_render_states_the_decision_and_the_checks() -> None:
    rows = rr.fold_rows(_hist(), "2025-26")
    acc = rr.accuracy(rows, n_boot=100)
    d = rr.decide(acc, rr.calibration_gap(rows), -0.1)
    text = rr.render(
        rows, acc, 0.0, -0.1, d, "replay text", "rank 221 → 80", datetime(2026, 10, 5, tzinfo=UTC)
    )
    assert "KEEP the current method" in text
    assert "SHIP variant R" not in text
    assert "replay text" in text
