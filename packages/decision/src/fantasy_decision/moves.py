"""Add/drop recommendations (DEC-008; methodology §20, D-61).

Candidate pairs (the top free agents by a fast screen x the lowest-value rostered players) are
scored with the DEC-003 simulator on expected categories won against this week's opponent,
plus a discounted next week (U13). Every candidate is scored on the same random numbers as the
current roster (common random numbers [R-61]), so small differences aren't simulation noise.

The screen ranks free agents by the normal-approximation gain in expected categories (the brief's
estimate) from replacing the lowest-value player, over the same horizon. Ranking by draft value x
games is wrong for free agents: their values are below replacement (negative), which put players
with no games first (found in the first DEC-008 run).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import polars as pl

from fantasy_decision import brief, simulate

COUNTS = simulate.COUNTS
N_ADDS = 10
N_DROPS = 3
DISCOUNT = 0.5  # U13: next week counts half


@dataclass(frozen=True)
class PlayerWeek:
    """Per-game projections (pts ... tov, fgm, fga, ftm, fta) and expected games for one week."""

    per_game: Mapping[str, float]
    games: float


@dataclass(frozen=True)
class Move:
    add: int
    drop: int
    gain: float  # expected categories won: this week + discount x next week, vs keeping the roster
    this_week: float
    next_week: float


def team(ids: Sequence[int], week: Mapping[int, PlayerWeek]) -> simulate.Team:
    rows = [week[i] for i in ids]
    games = np.array([max(r.games, 0.0) for r in rows])
    arr = {s: np.array([r.per_game[s] for r in rows]) * games for s in (*COUNTS, "fga", "fta")}
    with np.errstate(divide="ignore", invalid="ignore"):
        fg = np.nan_to_num(
            np.array([r.per_game["fgm"] / r.per_game["fga"] for r in rows]), nan=0.45
        )
        ft = np.nan_to_num(
            np.array([r.per_game["ftm"] / r.per_game["fta"] for r in rows]), nan=0.75
        )
    return simulate.Team(
        {c: arr[c] for c in COUNTS},
        {"fga": arr["fga"], "fta": arr["fta"]},
        {"fg_pct": fg, "ft_pct": ft},
        np.maximum(np.rint(games), 1).astype(np.int64),
    )


def _cats(
    mine: Sequence[int], opp: Sequence[int], week: Mapping[int, PlayerWeek], draws: int, seed: int
) -> float:
    return simulate.matchup(
        team(mine, week), team(opp, week), draws=draws, seed=seed
    ).expected_categories


def _frame(week: Mapping[int, PlayerWeek], ids: Sequence[int]) -> pl.DataFrame:
    stats = (*COUNTS, "fgm", "fga", "ftm", "fta")
    return pl.DataFrame(
        {
            "nba_player_id": list(ids),
            "exp_games": [week[p].games for p in ids],
            **{s: [week[p].per_game[s] * week[p].games for p in ids] for s in stats},
        }
    )


def _normal_cats(mine: Sequence[int], opp: Sequence[int], week: Mapping[int, PlayerWeek]) -> float:
    frame = _frame(week, [*mine, *opp])
    probs = brief.win_probs(brief.team_totals(frame, mine), brief.team_totals(frame, opp))
    return sum(probs.values())


def screen(  # noqa: PLR0913, PLR0917 - the screen's inputs
    roster: Sequence[int],
    drop: int,
    opponent: Sequence[int],
    opponent_next: Sequence[int],
    free_agents: Sequence[int],
    this_week: Mapping[int, PlayerWeek],
    next_week: Mapping[int, PlayerWeek],
    discount: float,
) -> dict[int, float]:
    """Normal-approximation gain of each free agent replacing `drop`, now + discount x next."""
    out = {}
    base = _normal_cats(roster, opponent, this_week)
    base_next = _normal_cats(roster, opponent_next, next_week) if discount else 0.0
    for a in free_agents:
        if a not in this_week or a not in next_week:
            continue
        new = [a if p == drop else p for p in roster]
        gain = _normal_cats(new, opponent, this_week) - base
        if discount:
            gain += discount * (_normal_cats(new, opponent_next, next_week) - base_next)
        out[a] = gain
    return out


def best_moves(  # noqa: PLR0913, PLR0917 - the decision's inputs
    roster: Sequence[int],
    opponent: Sequence[int],
    opponent_next: Sequence[int],
    free_agents: Sequence[int],
    this_week: Mapping[int, PlayerWeek],
    next_week: Mapping[int, PlayerWeek],
    *,
    value: Mapping[int, float],
    discount: float = DISCOUNT,
    n_adds: int = N_ADDS,
    n_drops: int = N_DROPS,
    draws: int = 1000,
    seed: int = 0,
) -> list[Move]:
    """Moves that beat keeping the roster, best first (empty: stand pat)."""

    drops = sorted(roster, key=lambda p: value.get(p, 0.0))[:n_drops]
    fast = screen(
        roster, drops[0], opponent, opponent_next, free_agents, this_week, next_week, discount
    )
    adds = sorted(fast, key=lambda p: -fast[p])[:n_adds]
    base_now = _cats(roster, opponent, this_week, draws, seed)
    base_next = _cats(roster, opponent_next, next_week, draws, seed + 1) if discount else 0.0
    out = []
    for a in adds:
        for d in drops:
            new = [a if p == d else p for p in roster]
            now = _cats(new, opponent, this_week, draws, seed) - base_now
            nxt = (
                (_cats(new, opponent_next, next_week, draws, seed + 1) - base_next)
                if discount
                else 0.0
            )
            gain = now + discount * nxt
            if gain > 0:
                out.append(Move(a, d, gain, now, nxt))
    return sorted(out, key=lambda m: -m.gain)


STATS = (*COUNTS, "fgm", "fga", "ftm", "fta")


def players_from(table: pl.DataFrame) -> dict[int, PlayerWeek]:
    """Brief-style week table (weekly totals + exp_games) -> per-game projections and games."""
    out = {}
    for r in table.iter_rows(named=True):
        games = float(r["exp_games"] or 0.0)
        per_game = {s: float(r[s]) / games if games > 0 else 0.0 for s in STATS}
        out[int(r["nba_player_id"])] = PlayerWeek(per_game, games)
    return out


def pickups(  # noqa: PLR0913 - the brief's inputs plus next week
    week: pl.DataFrame,
    next_week: pl.DataFrame,
    mine: Sequence[int],
    opponent: Sequence[int],
    opponent_next: Sequence[int],
    *,
    rostered: set[int],
    value: Mapping[int, float],
    n: int = 5,
    draws: int = 1000,
    seed: int = 0,
) -> list[brief.Pickup]:
    """DEC-010: the brief's pickups by DEC-008's method (this week + half of next week).

    `gain` is the simulated change in expected categories over that horizon; `helps` names the
    categories whose win chance this week rises most (the normal approximation, for the text)."""
    now, nxt = players_from(week), players_from(next_week)
    idle = PlayerWeek(dict.fromkeys(STATS, 0.0), 0.0)
    nxt |= {p: idle for p in now if p not in nxt}
    fas = [p for p in now if p not in rostered]
    best = best_moves(
        mine, opponent, opponent_next, fas, now, nxt, value=value, draws=draws, seed=seed
    )[:n]
    ids = week["nba_player_id"].to_list()
    names = dict(zip(ids, week["player_name"].to_list(), strict=True))
    left = dict(zip(ids, week["games_left"].to_list(), strict=True))
    theirs = brief.team_totals(week, opponent)
    before = brief.win_probs(brief.team_totals(week, mine), theirs)
    out = []
    for m in best:
        new = [m.add if p == m.drop else p for p in mine]
        after = brief.win_probs(brief.team_totals(week, new), theirs)
        ranked = sorted(after, key=lambda c: after[c] - before[c], reverse=True)
        helps = [c for c in ranked if after[c] - before[c] > brief.HELP_THRESHOLD][:3]
        out.append(
            brief.Pickup(
                m.add, names[m.add], m.drop, names[m.drop], int(left[m.add]), m.gain, helps
            )
        )
    return out
