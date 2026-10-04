"""DRAFT-009: draft two strategies against each other, play the season, score all-play H2H
(pre-registered in the task file).

- Draft: snake; each seat's strategy picks the best available player by its own values.
- Season: every day, the DEC-007 optimiser sets each team's lineup from its own values; started
  players with a game that day add their actual stats.
- Score: per week, each team against every other team in all 9 categories (ties 0.5); a team's
  score is its share of category wins.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from dikit.evaluate import bootstrap as bs
from fantasy_decision import lineup as lu

TEAMS = 16
ROUNDS = 14
SLOTS = {"G": 3, "F": 3, "C": 1, "Util": 3}
COUNTS = ("PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV")
RAW = (*COUNTS, "FGM", "FGA", "FTM", "FTA")


@dataclass(frozen=True)
class Result:
    per_draft: list[dict[str, float]]  # per draft: mean all-play share by strategy
    diff: float  # strategy A minus B, mean over drafts
    ci: tuple[float, float]
    a_better_share: float  # share of drafts where A's teams averaged higher
    strategies: tuple[str, str]


def snake(
    values: Mapping[str, Mapping[int, float]], seats: Sequence[str], rounds: int
) -> list[list[int]]:
    """Each seat picks the best remaining player by its own strategy's values (ties: lowest id)."""
    ranked = {s: sorted(v, key=lambda p: (-v[p], p)) for s, v in values.items()}
    taken: set[int] = set()
    squads: list[list[int]] = [[] for _ in seats]
    for rnd in range(rounds):
        order = range(len(seats)) if rnd % 2 == 0 else range(len(seats) - 1, -1, -1)
        for seat in order:
            pick = next(p for p in ranked[seats[seat]] if p not in taken)
            taken.add(pick)
            squads[seat].append(pick)
    return squads


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def weekly_rosters(
    squads: Sequence[Sequence[int]],
    seats: Sequence[str],
    values: Mapping[str, Mapping[int, float]],
    days: Mapping[date, Mapping[int, Sequence[float]]],
    il_slots: int = 0,
) -> dict[date, list[list[int]]]:
    """Each team's roster per week (DRAFT-011, pre-registered).

    At each week start, a drafted player with no game in the previous 7 days goes to IL (the team's
    most valuable absentees first, up to `il_slots`); for each, the team adds the best player by its
    own values that nobody owns. IL players return as soon as they play again (the next week)."""
    played: dict[date, set[int]] = defaultdict(set)
    for day, lines in days.items():
        played[day].update(lines)
    first = min(days) if days else None
    out: dict[date, list[list[int]]] = {}
    for wk in sorted({monday(d) for d in days}):
        if il_slots == 0 or first is None or wk - timedelta(days=7) < first:
            out[wk] = [list(s) for s in squads]
            continue
        recent: set[int] = set()
        for k in range(1, 8):
            recent |= played.get(wk - timedelta(days=k), set())
        owned = {p for s in squads for p in s}
        rosters = []
        for t, squad in enumerate(squads):
            v = values[seats[t]]
            absent = sorted(
                (p for p in squad if p not in recent), key=lambda p: (-v.get(p, 0.0), p)
            )
            il = set(absent[:il_slots])
            free = sorted((p for p in v if p not in owned), key=lambda p: (-v[p], p))
            adds = free[: len(il)]
            owned.update(adds)
            rosters.append([p for p in squad if p not in il] + adds)
        out[wk] = rosters
    return out


def season(  # noqa: PLR0913, PLR0917 - the replay's inputs
    squads: Sequence[Sequence[int]],
    seats: Sequence[str],
    values: Mapping[str, Mapping[int, float]],
    elig: Mapping[int, tuple[str, ...]],
    days: Mapping[date, Mapping[int, Sequence[float]]],
    il_slots: int = 0,
) -> dict[date, np.ndarray]:
    """Weekly totals: {week: array (teams, len(RAW))} of started players' actual stats."""
    weeks: dict[date, np.ndarray] = defaultdict(lambda: np.zeros((len(squads), len(RAW))))
    rosters = weekly_rosters(squads, seats, values, days, il_slots)
    for day, lines in days.items():
        wk = weeks[monday(day)]
        for t, squad in enumerate(rosters[monday(day)]):
            v = values[seats[t]]
            cands = [lu.Candidate(p, v.get(p, 0.0), elig.get(p, ()), p in lines) for p in squad]
            for pid in lu.optimise(cands, SLOTS):
                wk[t] += np.asarray(lines[pid], dtype=float)
    return dict(weeks)


def all_play(weeks: Mapping[date, np.ndarray]) -> np.ndarray:
    """Each team's share of category wins against every other team, pooled over weeks."""
    first = next(iter(weeks.values()))
    teams = first.shape[0]
    wins = np.zeros(teams)
    games = 0
    idx = {c: i for i, c in enumerate(RAW)}
    for tot in weeks.values():
        cats = [tot[:, idx[c]] for c in COUNTS]
        with np.errstate(divide="ignore", invalid="ignore"):
            cats.append(np.nan_to_num(tot[:, idx["FGM"]] / tot[:, idx["FGA"]]))
            cats.append(np.nan_to_num(tot[:, idx["FTM"]] / tot[:, idx["FTA"]]))
        for k, x in enumerate(cats):
            better = -x if k == COUNTS.index("TOV") else x
            diff = better[:, None] - better[None, :]
            wins += (diff > 0).sum(axis=1) + 0.5 * ((diff == 0).sum(axis=1) - 1)
        games += 9 * (teams - 1)
    return wins / games


def run(  # noqa: PLR0913 - the replay's inputs and knobs
    values: Mapping[str, Mapping[int, float]],
    elig: Mapping[int, tuple[str, ...]],
    days: Mapping[date, Mapping[int, Sequence[float]]],
    *,
    drafts: int = 40,
    n_boot: int = 2000,
    seed: int = 0,
    il_slots: int = 0,
) -> Result:
    a, b = list(values)
    rng = np.random.default_rng(seed)
    per_draft = []
    for _ in range(drafts):
        seats = [a, b] * (TEAMS // 2)
        rng.shuffle(seats)
        squads = snake(values, seats, ROUNDS)
        share = all_play(season(squads, seats, values, elig, days, il_slots))
        per_draft.append(
            {s: float(np.mean([share[i] for i, x in enumerate(seats) if x == s])) for s in (a, b)}
        )
    d = np.array([r[a] - r[b] for r in per_draft])
    return Result(
        per_draft,
        float(d.mean()),
        bs.mean_ci(d, n_boot, rng),
        float((d > 0).mean()),
        (a, b),
    )
