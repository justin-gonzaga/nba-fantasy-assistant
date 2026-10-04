from datetime import date, timedelta

import numpy as np
import pytest

from fantasy_evaluation import draft_replay as dr


def test_snake_gives_each_seat_its_own_best_available() -> None:
    values = {"a": {1: 3.0, 2: 2.0, 3: 1.0, 4: 0.0}, "b": {1: 0.0, 2: 1.0, 3: 3.0, 4: 2.0}}
    squads = dr.snake(values, ["a", "b"], rounds=2)
    assert squads == [[1, 2], [3, 4]]  # a: 1 then (snake back) b: 3, 4, then a: 2


def test_all_play_is_symmetric_and_rewards_the_stronger_team() -> None:
    wk = np.zeros((3, len(dr.RAW)))
    wk[0] = 10  # best in every category except turnovers (more TO is worse)
    wk[1] = 5
    wk[2] = 5
    share = dr.all_play({date(2025, 11, 3): wk})
    assert share.sum() == pytest.approx(1.5)  # 3 teams: the shares of each pair sum to 1
    assert share[0] > share[1]
    assert share[1] == pytest.approx(share[2])


def test_the_real_values_strategy_beats_a_reversed_one() -> None:
    rng = np.random.default_rng(1)
    players = list(range(300))
    skill = {p: float(rng.uniform(0.2, 2.0)) for p in players}
    elig = {p: ("G", "F", "C")[p % 3 : p % 3 + 1] for p in players}
    days = {}
    start = date(2025, 10, 20)
    for i in range(0, 42, 2):
        lines = {p: [10 * skill[p]] * 6 + [1.0] + [4 * skill[p], 8.0, 2.0, 3.0] for p in players}
        days[start + timedelta(days=i)] = lines
    values = {"smart": skill, "reverse": {p: -s for p, s in skill.items()}}
    res = dr.run(values, elig, days, drafts=4, n_boot=200)
    assert res.strategies == ("smart", "reverse")
    assert res.diff > 0
    assert res.a_better_share == 1.0


def test_snake_breaks_value_ties_by_player_id_not_row_order() -> None:
    forward = {"s": {3: 1.0, 1: 1.0, 2: 1.0}}
    backward = {"s": {2: 1.0, 1: 1.0, 3: 1.0}}
    assert dr.snake(forward, ["s"], 3) == dr.snake(backward, ["s"], 3) == [[1, 2, 3]]


# ------------------------------------------------------------------ DRAFT-011: IL replacements
MON = date(2025, 10, 20)
LINE = [1.0] * len(dr.RAW)


def _days(
    weeks: int, absent: dict[int, set[int]], players: range
) -> dict[date, dict[int, list[float]]]:
    """A game every day; `absent[w]` = players without a game in week w (0-based)."""
    return {
        MON + timedelta(days=7 * w + d): {p: LINE for p in players if p not in absent.get(w, set())}
        for w in range(weeks)
        for d in range(7)
    }


def test_il_absent_player_is_replaced_by_the_best_free_agent() -> None:
    values = {"a": {1: 9.0, 2: 8.0, 10: 3.0, 11: 5.0}, "b": {1: 9.0, 2: 8.0, 10: 3.0, 11: 5.0}}
    days = _days(3, {0: {1}}, range(1, 12))
    rosters = dr.weekly_rosters([[1, 2]], ["a"], values, days, il_slots=3)
    assert rosters[MON] == [[1, 2]]  # nothing known before the first week
    assert rosters[MON + timedelta(days=7)] == [[2, 11]]  # 1 missed week 0 → IL, best FA is 11
    assert rosters[MON + timedelta(days=14)] == [[1, 2]]  # 1 played in week 1 → back


def test_il_is_capped_by_slots_and_free_agents_are_not_shared() -> None:
    values = {"a": {p: float(20 - p) for p in range(1, 20)}}
    values["b"] = values["a"]
    days = _days(2, {0: {1, 2, 3, 4, 5}}, range(1, 20))
    rosters = dr.weekly_rosters([[1, 2, 3], [4, 5, 6]], ["a", "b"], values, days, il_slots=2)
    week1 = rosters[MON + timedelta(days=7)]
    assert week1[0] == [3, 7, 8]  # 3 absentees, 2 IL slots: the two best go to IL; 3 stays
    assert week1[1] == [6, 9, 10]  # team b can't take 7 or 8
    assert len(set(week1[0]) & set(week1[1])) == 0


def test_no_il_slots_keeps_the_drafted_squads() -> None:
    values = {"a": {1: 2.0, 2: 1.0, 3: 0.5}}
    days = _days(2, {0: {1}}, range(1, 4))
    rosters = dr.weekly_rosters([[1, 2]], ["a"], values, days, il_slots=0)
    assert all(r == [[1, 2]] for r in rosters.values())
