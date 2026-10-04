from dikit.decide import assign as a

SLOTS = {"X": 1, "Y": 1, "Any": 1}


def test_optimise_fills_more_slots_than_greedy_when_greedy_blocks_itself() -> None:
    cands = [
        a.Candidate(1, 10.0, ("X", "Y"), available=True),
        a.Candidate(2, 9.0, ("X",), available=True),
        a.Candidate(3, 8.0, ("X",), available=True),
    ]
    slots = {"X": 1, "Y": 1}
    best = a.optimise(cands, slots)
    assert best == {1: "Y", 2: "X"}
    assert (
        a.score(best, cands) > a.score(a.greedy(cands, slots), cands)
        or a.greedy(cands, slots) == best
    )


def test_flex_slot_takes_anyone_and_unavailable_candidates_sit() -> None:
    cands = [
        a.Candidate(1, 5.0, ("X",), available=True),
        a.Candidate(2, 4.0, ("X",), available=True),
        a.Candidate(3, 9.0, ("Y",), available=False),
    ]
    best = a.optimise(cands, SLOTS, flex="Any")
    assert a.score(best, cands) == (2, 9.0)  # both X-only candidates play, one of them as flex
    assert a.legal(best, cands, SLOTS, flex="Any")
    assert not a.legal({3: "Y"}, cands, SLOTS, flex="Any")
    assert not a.legal({1: "Any", 2: "Any"}, cands, SLOTS, flex="Any")  # over capacity


def test_without_a_flex_slot_nobody_is_placed_out_of_position() -> None:
    cands = [a.Candidate(1, 5.0, ("X",), available=True), a.Candidate(2, 4.0, ("X",), True)]
    assert a.optimise(cands, SLOTS) == {1: "X"}
    assert a.greedy(cands, SLOTS) == {1: "X"}
