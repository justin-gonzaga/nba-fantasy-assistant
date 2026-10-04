"""Count distributions for weekly category totals (DEC-002; methodology §17, D-61).

- Counting stats: negative binomial per game, parameterised by mean and size r (var = m + m^2/r;
  r -> infinity is Poisson) [R-30, R-31]. A week of n games sums n iid draws: size n*r, mean n*m.
- Makes given attempts: beta-binomial with intra-class correlation rho (rho = 0 is binomial).
- Dispersions by the method of moments on (observation, predicted mean) pairs.
- Scores (CRPS, randomized PIT) live in `dikit.evaluate.scoring` [R-41, R-43, R-44].
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]

# Fitted on 20,783 selection player-weeks; shipped by the pre-registered DEC-002 test
# (docs/evaluation/reports/DEC-002-distributions.md): per-game NB size r by category, and the
# beta-binomial correlation of makes given attempts.
NB_SIZE: dict[str, float] = {
    "pts": 3.872,
    "reb": 4.663,
    "ast": 4.225,
    "stl": 2.666,
    "blk": 2.266,
    "fg3m": 3.103,
    "tov": 5.343,
    "fga": 6.865,
    "fta": 2.057,
}
MAKES_RHO: dict[str, float] = {"fg_pct": 0.004, "ft_pct": 0.035}
