import numpy as np
import pytest

from dikit.decide import simulate as sim

CATS = sim.Categories(
    counts={"a": 5.0, "b": 5.0, "c": 5.0},
    ratios={"r": sim.Ratio("att", 10.0, 0.01)},
    lower_is_better=frozenset({"c"}),
)


def _side(scale: float, members: int = 8) -> sim.Side:
    units = np.full(members, 3)
    return sim.Side(
        counts={k: np.full(members, 4.0 * scale) * units for k in ("a", "b", "c")},
        attempts={"att": np.full(members, 10.0) * units},
        pct={"r": np.full(members, 0.45)},
        units=units,
    )


def test_equal_sides_split_evenly_and_a_stronger_side_wins() -> None:
    even = sim.matchup(_side(1.0), _side(1.0), CATS, draws=4000, seed=1)
    assert even.expected_categories == pytest.approx(2.0, abs=0.1)
    strong = sim.matchup(_side(2.0), _side(1.0), CATS, draws=4000, seed=1)
    assert strong.probs["a"] > 0.95
    assert strong.probs["c"] < 0.05  # lower is better: more is worse
    assert strong.p_win > 0.5


def test_same_seed_same_answer() -> None:
    m1 = sim.matchup(_side(1.2), _side(1.0), CATS, draws=500, seed=7)
    m2 = sim.matchup(_side(1.2), _side(1.0), CATS, draws=500, seed=7)
    assert m1 == m2
    assert CATS.names == ("a", "b", "c", "r")
