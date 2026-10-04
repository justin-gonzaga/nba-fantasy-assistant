import polars as pl
import pytest

from fantasy_api import indicators as ind
from fantasy_api.schemas import Indicator


def _proj(
    pid: int, games: float, games_sd: float, mpg: float, mpg_sd: float
) -> list[dict[str, object]]:
    stats = {
        "pts": (25.0, 3.0),
        "reb": (10.0, 1.5),
        "ast": (5.0, 1.0),
        "games": (games, games_sd),
        "mpg": (mpg, mpg_sd),
    }
    return [
        {"season": "2026-27", "nba_player_id": pid, "stat": s, "mean": m, "sd": sd}
        for s, (m, sd) in stats.items()
    ]


def _inputs(variant: str = "all") -> ind.IndicatorInputs:
    proj = pl.DataFrame(_proj(1, 70, 5, 34, 2) + _proj(2, 60, 15, 30, 6) + _proj(3, 65, 9, 32, 4))
    history = pl.DataFrame(
        {
            "nba_player_id": [1, 2, 3],
            "season": ["2025-26"] * 3,
            "games_played": [70, 40, 60],
            "season_team_games": [82, 82, 82],
            "minutes": [70 * 30.0, 40 * 26.0, 60 * 32.0],
            "age": [30.0, 22.0, 26.0],
        }
    )
    consistency = pl.DataFrame(
        {
            "nba_player_id": [1, 2, 3],
            "season": ["2025-26"] * 3,
            "weeks": [20, 20, 20],
            "weekly_sd": [0.8, 2.1, 1.2],
            "weekly_mean": [4.0, 3.0, 4.0],
            "rel_sd": [0.2, 0.7, 0.3],
            "pct": [0.0, 1.0, 0.5],
        }
    )
    values = pl.DataFrame(
        {
            "nba_player_id": [1, 2, 3, 1, 2, 3],
            "variant": ["all"] * 3 + ["punt_ast"] * 3,
            "overall_rank": [5, 64, 30, 9, 31, 28],
            "drafted": [True, True, True, True, True, True],
        }
    )
    return ind.load_inputs(values, variant, proj, history, consistency)


def _by_code(pid: int, inputs: ind.IndicatorInputs) -> dict[str, Indicator]:
    return {i.code: i for i in ind.indicators_for(pid, inputs)}


def test_thresholds_are_pinned() -> None:
    assert (ind.ROLE_MPG, ind.PUNT_GAIN, ind.Z80) == (3.0, 20, 1.2816)
    assert (ind.STEADY_PCT, ind.VOLATILE_PCT) == (1 / 3, 2 / 3)


def test_range_uses_the_calibrated_80_percent_interval() -> None:
    r = _by_code(1, _inputs())["range"]
    assert r.why == f"80 % range: 21{ind.EN_DASH}29 pts, 64{ind.EN_DASH}76 games"  # 25 ± 1.28*3


def test_certainty_terciles_by_games_and_minutes_spread() -> None:
    i = _inputs()
    assert _by_code(1, i)["certainty"].label == "High certainty"
    assert _by_code(2, i)["certainty"].label == "Low certainty"
    assert _by_code(3, i)["certainty"].label == "Medium certainty"


def test_role_change_needs_three_minutes() -> None:
    i = _inputs()
    big = _by_code(2, i)["role"]  # 30 projected vs 26 last season
    assert (big.label, big.tone, big.signal, big.value) == (
        "Bigger role +4.0 min",
        "win",
        True,
        4.0,
    )
    assert big.why == "Projected 30.0 min vs 26.0 last season"
    assert "role" not in _by_code(3, i)  # 32 vs 32


def test_punt_fit_only_under_a_punt_and_with_a_big_gain() -> None:
    assert "punt_fit" not in _by_code(2, _inputs("all"))
    fit = _by_code(2, _inputs("punt_ast"))["punt_fit"]
    assert (fit.label, fit.why) == ("Fits punt AST", "#64 overall, #31 when punting AST")
    assert "punt_fit" not in _by_code(1, _inputs("punt_ast"))  # #5 → #9


def test_consistency_extremes_only() -> None:
    i = _inputs()
    assert _by_code(1, i)["consistency"].label == "Steady"
    vol = _by_code(2, i)["consistency"]
    assert (vol.label, vol.signal) == ("Volatile", True)
    assert vol.why == "Weekly value swung ±70% of his level last season (draft-pool median ±30%)"
    assert "consistency" not in _by_code(3, i)


def test_age_next_season() -> None:
    assert _by_code(1, _inputs())["age"].label == "Age 31"


@pytest.mark.parametrize("missing", ["proj", "history", "consistency"])
def test_missing_inputs_drop_their_indicators(missing: str) -> None:
    i = _inputs()
    stripped = ind.load_inputs(
        pl.DataFrame({"nba_player_id": [1], "variant": ["all"], "overall_rank": [1]}),
        "all",
        None if missing == "proj" else pl.DataFrame(_proj(1, 70, 5, 34, 2)),
        None
        if missing == "history"
        else pl.DataFrame(
            {
                "nba_player_id": [1],
                "season": ["2025-26"],
                "games_played": [70],
                "season_team_games": [82],
                "minutes": [2100.0],
                "age": [30.0],
            }
        ),
        None
        if missing == "consistency"
        else pl.DataFrame(
            {
                "nba_player_id": [1],
                "season": ["2025-26"],
                "weeks": [20],
                "weekly_sd": [0.5],
                "pct": [0.0],
            }
        ),
    )
    codes = set(_by_code(1, stripped))
    gone = {
        "proj": {"range", "certainty", "role"},
        "history": {"role", "age"},
        "consistency": {"consistency"},
    }[missing]
    assert not codes & gone
    del i


def test_signal_priority() -> None:
    i = _inputs("punt_ast")
    top = ind.signal(ind.indicators_for(2, i))
    assert top is not None
    assert top.code == "role"  # role > punt fit > volatile


def test_certainty_cut_points_come_from_the_draft_pool() -> None:
    """A fringe player with a huge spread can't make every pool player look certain."""
    rows = []
    for pid, spread in ((1, 0.1), (2, 0.2), (3, 0.3), (99, 5.0)):
        rows += _proj(pid, 60, 60 * spread / 2, 30, 30 * spread / 2)
    values = pl.DataFrame(
        {
            "nba_player_id": [1, 2, 3, 99],
            "variant": ["all"] * 4,
            "overall_rank": [1, 2, 3, 400],
            "drafted": [True, True, True, False],
        }
    )
    i = ind.load_inputs(values, "all", pl.DataFrame(rows), None, None)
    assert [i.certainty[p] for p in (1, 2, 3)] == ["high", "medium", "low"]
    assert i.certainty[99] == "low"


def test_role_why_names_the_drivers_when_published() -> None:
    i = _inputs()
    ind.add_role_context(
        i,
        pl.DataFrame({"nba_player_id": [2], "changed_team": [True], "vacated_min": [1240.0]}),
    )
    why = _by_code(2, i)["role"].why
    assert why == "Projected 30.0 min vs 26.0 last season; new team; 1,240 team minutes freed up"


def test_role_why_without_drivers_is_just_the_minutes() -> None:
    assert _by_code(2, _inputs())["role"].why == "Projected 30.0 min vs 26.0 last season"


def test_role_without_age_column() -> None:
    """WEB-022: an older history file without `age` still gives role change; age is skipped."""
    hist = pl.DataFrame(
        {
            "nba_player_id": [2],
            "season": ["2025-26"],
            "games_played": [40],
            "season_team_games": [82],
            "minutes": [40 * 26.0],
        }
    )
    values = pl.DataFrame({"nba_player_id": [2], "variant": ["all"], "overall_rank": [1]})
    i = ind.load_inputs(values, "all", pl.DataFrame(_proj(2, 60, 15, 30, 6)), hist, None)
    codes = {x.code for x in ind.indicators_for(2, i)}
    assert "role" in codes
    assert "age" not in codes
    assert any("Age" in n for n in i.notes)
    assert any("Steady" in n for n in i.notes)  # no consistency file either
