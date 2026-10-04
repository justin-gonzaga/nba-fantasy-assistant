"""A synthetic league with known true rates, for testing projection methods without network."""

from __future__ import annotations

from typing import Any

import numpy as np
import polars as pl

from fantasy_models.preseason.schema import season_of

TRUE_RATES = {  # league mean per-minute rates (roughly NBA-like)
    "fga": 0.40,
    "fg3a": 0.15,
    "fta": 0.12,
    "reb": 0.18,
    "ast": 0.10,
    "stl": 0.03,
    "blk": 0.02,
    "tov": 0.06,
}
TRUE_PCTS: dict[str, tuple[str, str, float]] = {
    "fg_pct": ("fgm", "fga", 0.47),
    "fg3_pct": ("fg3m", "fg3a", 0.36),
    "ft_pct": ("ftm", "fta", 0.78),
}
MAX_AGE, PEAK_AGE = 38, 27
MOVE_RATE = 0.2
SHAPE = 8.0  # Gamma shape of between-player rate spread (tau^2 = mu^2 / SHAPE)


def make_league(
    seed: int = 7, n_players: int = 150, first: int = 2015, last: int = 2025
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Returns (seasons in int_player_season shape, draft picks)."""
    rng = np.random.default_rng(seed)
    true = {s: rng.gamma(SHAPE, mu / SHAPE, n_players) for s, mu in TRUE_RATES.items()}
    pct_true = {n: rng.beta(p * 60, (1 - p) * 60, n_players) for n, (_, _, p) in TRUE_PCTS.items()}
    mpg = rng.uniform(8, 36, n_players)
    debut = rng.integers(first - 6, last + 1, n_players)
    age0 = rng.uniform(19, 23, n_players)
    team = rng.integers(0, 30, n_players) + 1610612737
    rows = []
    for i in range(n_players):
        for y in range(max(first, int(debut[i])), last + 1):
            age = float(age0[i] + (y - debut[i]))
            if age > MAX_AGE:
                break
            gp = int(rng.integers(20, 83))
            minutes = float(gp * mpg[i])
            age_mult = (
                1.0 + 0.02 * (PEAK_AGE - age) if age < PEAK_AGE else 1.0 - 0.03 * (age - PEAK_AGE)
            )
            row: dict[str, Any] = {
                "season": season_of(y),
                "nba_player_id": 1000 + i,
                "age": round(age, 1),
                "games_played": gp,
                "season_team_games": 82,
                "minutes": minutes,
                "first_nba_team_id": int(team[i]),
                "last_nba_team_id": int(team[i]),
            }
            for s in TRUE_RATES:
                row[s] = int(rng.poisson(true[s][i] * max(age_mult, 0.3) * minutes))
            for name, (mk, att, _) in TRUE_PCTS.items():
                row[mk] = int(rng.binomial(row[att], pct_true[name][i]))
            row["pts"] = 2 * row["fgm"] + row["fg3m"] + row["ftm"]
            rows.append(row)
            if rng.uniform() < MOVE_RATE:  # off-season move
                team[i] = int(rng.integers(0, 30)) + 1610612737
    seasons = pl.DataFrame(rows).with_columns(
        [
            pl.col(c).cast(pl.Int64)
            for c in (
                "games_played",
                "season_team_games",
                "fga",
                "fg3a",
                "fta",
                "reb",
                "ast",
                "stl",
                "blk",
                "tov",
                "fgm",
                "fg3m",
                "ftm",
                "pts",
            )
        ]
    )
    draft = pl.DataFrame(
        {
            "nba_player_id": [1000 + i for i in range(n_players)],
            "draft_year": [int(d) for d in debut],
            "overall_pick": [int(rng.integers(1, 61)) for _ in range(n_players)],
        }
    )
    return seasons, draft
