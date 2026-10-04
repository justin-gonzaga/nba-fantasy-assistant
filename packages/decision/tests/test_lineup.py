from hypothesis import given, settings
from hypothesis import strategies as st

from fantasy_decision import lineup as lu

POSITIONS = [("G",), ("F",), ("C",), ("G", "F"), ("F", "C")]


def test_the_optimiser_fixes_a_case_greedy_gets_wrong() -> None:
    cands = [
        lu.Candidate(1, 10.0, ("F", "C"), plays=True),  # greedy puts him at F ...
        lu.Candidate(2, 9.0, ("F",), plays=True),  # ... so this forward has nowhere to go
    ]
    slots = {"F": 1, "C": 1}
    assert lu.score(lu.greedy(cands, slots), cands) == (1, 10.0)
    best = lu.optimise(cands, slots)
    assert best == {1: "C", 2: "F"}
    assert lu.score(best, cands) == (2, 19.0)


def test_players_without_a_game_are_never_active() -> None:
    cands = [lu.Candidate(1, 10.0, ("G",), plays=False), lu.Candidate(2, 1.0, ("G",), plays=True)]
    assert lu.optimise(cands, {"G": 1}) == {2: "G"}


def test_util_takes_anyone() -> None:
    cands = [lu.Candidate(1, 3.0, ("C",), plays=True), lu.Candidate(2, 2.0, ("C",), plays=True)]
    assert lu.score(lu.optimise(cands, {"C": 1, "Util": 1}), cands) == (2, 5.0)


roster = st.lists(
    st.tuples(
        st.floats(-5, 10, allow_nan=False),
        st.sampled_from(POSITIONS),
        st.booleans(),
    ),
    min_size=1,
    max_size=14,
)


@settings(max_examples=150, deadline=None)
@given(roster)
def test_optimised_lineups_are_legal_and_never_worse_than_greedy(
    players: list[tuple[float, tuple[str, ...], bool]],
) -> None:
    cands = [lu.Candidate(i, v, e, p) for i, (v, e, p) in enumerate(players)]
    slots = {"G": 3, "F": 3, "C": 1, "Util": 3}
    best, greedy = lu.optimise(cands, slots), lu.greedy(cands, slots)
    assert lu.legal(best, cands, slots)
    assert lu.legal(greedy, cands, slots)
    b, g = lu.score(best, cands), lu.score(greedy, cands)
    assert b[0] >= g[0]
    if b[0] == g[0]:
        assert b[1] >= g[1] - 1e-6  # below solver tolerance; real values differ by far more
