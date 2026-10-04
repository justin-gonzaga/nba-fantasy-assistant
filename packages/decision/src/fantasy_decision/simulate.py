"""Monte Carlo matchup simulation (DEC-003; methodology §18, D-61): the NBA 9-category binding of
`dikit.decide.simulate`.

Counting categories use the DEC-002 negative-binomial sizes per game; FG%/FT% use NB attempts with
beta-binomial makes. One seed drives both teams, so two lineups compared with the same seed share
their random numbers (common random numbers [R-61]).
"""

from __future__ import annotations

import numpy as np

from dikit.decide import simulate as sim
from fantasy_models.distributions import MAKES_RHO, NB_SIZE

COUNTS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov")
PCTS = {"fg_pct": "fga", "ft_pct": "fta"}
LOWER_IS_BETTER = frozenset({"tov"})
CATEGORIES = sim.Categories(
    counts={c: NB_SIZE[c] for c in COUNTS},
    ratios={cat: sim.Ratio(att, NB_SIZE[att], MAKES_RHO[cat]) for cat, att in PCTS.items()},
    lower_is_better=LOWER_IS_BETTER,
)

Team = sim.Side  # per-player weekly expectations; `units` = games that week
Matchup = sim.Result


def totals(team: Team, draws: int, rng: np.random.Generator) -> dict[str, sim.Array]:
    """Simulated weekly team totals per category (percentages as team makes / attempts)."""
    return sim.totals(team, CATEGORIES, draws, rng)


def matchup(team_a: Team, team_b: Team, *, draws: int = 2000, seed: int = 0) -> Matchup:
    return sim.matchup(team_a, team_b, CATEGORIES, draws=draws, seed=seed)
