from datetime import date, timedelta

import numpy as np
import polars as pl

from fantasy_evaluation import inseason_backtest as ib

RNG = np.random.default_rng(11)
PER_GAME = {"PTS": 15, "REB": 6, "AST": 4, "STL": 1, "BLK": 0.8, "FG3M": 1.5, "TOV": 2}


def _data(players: int = 80) -> tuple[pl.DataFrame, pl.DataFrame]:
    """A 2025-26 season where each player's true level differs from his (noisy) pre-season prior."""
    logs, priors = [], []
    start = date(2025, 10, 20)
    for p in range(players):
        talent = RNG.uniform(0.5, 2.0)
        noise = RNG.normal(1.0, 0.25)  # the prior misses by ~25 %
        prior = {c.lower(): m * talent * noise for c, m in PER_GAME.items()}
        prior |= {
            "fga": 12 * talent * noise,
            "fgm": 5.6 * talent * noise,
            "fta": 4 * talent * noise,
            "ftm": 3.1 * talent * noise,
        }
        priors.append({"SEASON": "2025-26", "PLAYER_ID": p, **prior})
        for i in range(0, 160, 2):
            row: dict[str, object] = {
                "SEASON": "2025-26",
                "PLAYER_ID": p,
                "GAME_DATE": (start + timedelta(days=i)).isoformat(),
            }
            for c, m in PER_GAME.items():
                row[c] = int(RNG.poisson(m * talent))
            fga, fta = int(RNG.poisson(12 * talent)), int(RNG.poisson(4 * talent))
            row |= {
                "FGA": fga,
                "FGM": int(RNG.binomial(fga, 0.47)),
                "FTA": fta,
                "FTM": int(RNG.binomial(fta, 0.78)),
            }
            logs.append(row)
    return pl.DataFrame(logs), pl.DataFrame(priors)


def test_updating_a_noisy_prior_with_the_season_beats_freezing_it() -> None:
    logs, priors = _data()
    res = ib.run(logs, priors, n_boot=200)
    counts = res.table.filter(pl.col("category").is_in(list(ib.COUNTS)))
    assert counts["mae_blend"].mean() < counts["mae_prior"].mean()  # type: ignore[operator]
    assert res.rows["holdout"] > 0
    assert set(res.table["category"].to_list()) == {*ib.COUNTS, *ib.PCTS}
