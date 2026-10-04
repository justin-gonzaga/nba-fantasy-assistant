from datetime import UTC, datetime

import polars as pl
import pytest

from fantasy_evaluation import draft_replay as dr
from fantasy_pipeline import draft_replay_run as r

run = r


def test_baselines_are_selectable_and_have_their_own_reports() -> None:
    assert set(r.BASELINES) == {"B0", "B1"}
    assert r.REPORTS["B0"] != r.REPORTS["B1"]
    assert "Marcel" in r.BASELINES["B1"]


def _res(diff: float, ci: tuple[float, float], a: str, b: str) -> dr.Result:
    return dr.Result([{a: 0.5, b: 0.5}], diff, ci, 0.0, (a, b))


def _vals() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nba_player_id": [203507],
            "player_name": ["Giannis Antetokounmpo"],
            "variant": ["all"],
            "overall_rank": [1],
            "dollars": [10.0],
        }
    )


def test_fill_report_keeps_current_values_when_the_candidate_loses() -> None:
    r = _res(-0.04, (-0.045, -0.033), run.FILL, run.CURRENT)
    text = run.fill_report(r, r, _vals(), _vals(), 3, datetime(2026, 10, 2, tzinfo=UTC))
    assert "KEEP the current values" in text
    assert "SHIP A" not in text


def test_fill_report_refuses_a_swapped_comparison() -> None:
    r = _res(0.04, (0.03, 0.05), run.CURRENT, run.FILL)
    with pytest.raises(ValueError, match="candidate must be strategy A"):
        run.fill_report(r, r, _vals(), _vals(), 3, datetime(2026, 10, 2, tzinfo=UTC))


def test_robust_report_uses_non_inferiority() -> None:
    near = _res(-0.002, (-0.004, 0.0), run.ROBUST, run.ROBUST_CMP.current)
    text = run.fill_report(
        near, near, _vals(), _vals(), 3, datetime(2026, 10, 2, tzinfo=UTC), run.ROBUST_CMP
    )
    assert "SHIP A" in text  # slightly worse but within the -0.005 margin
    worse = _res(-0.01, (-0.012, -0.008), run.ROBUST, run.ROBUST_CMP.current)
    text = run.fill_report(
        worse, worse, _vals(), _vals(), 3, datetime(2026, 10, 2, tzinfo=UTC), run.ROBUST_CMP
    )
    assert "KEEP the current values" in text


def test_reports_state_the_single_season_caveat() -> None:
    r = _res(-0.04, (-0.045, -0.033), run.FILL, run.CURRENT)
    text = run.fill_report(r, r, _vals(), _vals(), 3, datetime(2026, 10, 2, tzinfo=UTC))
    assert "not season-to-season variation" in text
