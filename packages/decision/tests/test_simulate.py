import numpy as np
import pytest

from fantasy_decision import simulate as sim


def _team(scale: float, players: int = 10, tov: float = 2.0) -> sim.Team:
    games = np.full(players, 3)
    per_game = {"pts": 15.0, "reb": 6.0, "ast": 4.0, "stl": 1.0, "blk": 0.8, "fg3m": 1.5}
    return sim.Team(
        counts={c: np.full(players, v * scale) * games for c, v in per_game.items()}
        | {"tov": np.full(players, tov) * games},
        attempts={
            "fga": np.full(players, 12.0 * scale) * games,
            "fta": np.full(players, 4.0) * games,
        },
        pct={"fg_pct": np.full(players, 0.47), "ft_pct": np.full(players, 0.78)},
        units=games,
    )


def test_identical_teams_split_every_category_evenly() -> None:
    m = sim.matchup(_team(1.0), _team(1.0), draws=4000, seed=1)
    for p in m.probs.values():
        assert p == pytest.approx(0.5, abs=0.05)
    assert m.expected_categories == pytest.approx(4.5, abs=0.3)


def test_a_much_stronger_team_wins_the_counting_categories() -> None:
    m = sim.matchup(_team(2.0), _team(0.5), draws=2000, seed=1)
    for c in ("pts", "reb", "ast", "fg3m"):
        assert m.probs[c] > 0.99


def test_fewer_turnovers_win_the_turnover_category() -> None:
    m = sim.matchup(_team(1.0, tov=1.0), _team(1.0, tov=3.0), draws=2000, seed=1)
    assert m.probs["tov"] > 0.95


def test_the_same_seed_gives_the_same_answer() -> None:
    a = sim.matchup(_team(1.1), _team(1.0), draws=1000, seed=42)
    b = sim.matchup(_team(1.1), _team(1.0), draws=1000, seed=42)
    assert a.probs == b.probs


def test_standard_error_is_reported_and_small_at_2000_draws() -> None:
    m = sim.matchup(_team(1.1), _team(1.0), draws=2000, seed=3)
    assert 0 < m.se_expected_categories < 0.05


def test_week_win_probability_counts_categories() -> None:
    m = sim.matchup(_team(2.0), _team(0.5), draws=2000, seed=1)
    assert m.p_win > 0.95
