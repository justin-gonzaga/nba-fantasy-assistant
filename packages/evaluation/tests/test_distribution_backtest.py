from datetime import date, timedelta

import numpy as np
import polars as pl

from fantasy_evaluation import distribution_backtest as db

RNG = np.random.default_rng(3)


def _logs(size: float, players: int = 60, days: int = 150) -> pl.DataFrame:
    """Synthetic season: every player plays every other day, per-game counts NB(size)."""
    rows = []
    start = date(2025, 10, 20)
    for p in range(players):
        base = RNG.uniform(0.5, 2.0)
        for i in range(0, days, 2):
            day = start + timedelta(days=i)
            row: dict[str, object] = {
                "SEASON": "2025-26",
                "PLAYER_ID": p,
                "GAME_DATE": day.isoformat(),
            }
            for col, m in {
                "PTS": 15,
                "REB": 6,
                "AST": 4,
                "STL": 1,
                "BLK": 0.8,
                "FG3M": 1.5,
                "TOV": 2,
            }.items():
                mu = m * base
                row[col] = int(RNG.negative_binomial(size, size / (size + mu)))
            fga = int(RNG.negative_binomial(size, size / (size + 12 * base)))
            fta = int(RNG.negative_binomial(size, size / (size + 4 * base)))
            row |= {
                "FGA": fga,
                "FGM": int(RNG.binomial(fga, 0.47)),
                "FTA": fta,
                "FTM": int(RNG.binomial(fta, 0.78)),
            }
            rows.append(row)
    return pl.DataFrame(rows)


def test_player_weeks_use_only_earlier_games_for_the_mean() -> None:
    logs = pl.DataFrame(
        {
            "SEASON": ["s"] * 7,
            "PLAYER_ID": [1] * 7,
            "GAME_DATE": [f"2025-10-{d}" for d in (20, 21, 22, 23, 24, 27, 28)],
            **{
                c: [10] * 7
                for c in [
                    "PTS",
                    "REB",
                    "AST",
                    "STL",
                    "BLK",
                    "FG3M",
                    "TOV",
                    "FGM",
                    "FGA",
                    "FTM",
                    "FTA",
                ]
            },
        }
    )
    pw = db.player_weeks(logs)
    assert pw.height == 1  # week of 27 Oct: 5 earlier games
    row = pw.row(0, named=True)
    assert (row["n"], row["prior_n"], row["prior_PTS"], row["PTS"]) == (2, 5, 50, 20)


def test_overdispersed_data_favours_the_negative_binomial() -> None:
    res = db.run(_logs(size=2.0), n_boot=200)
    counts = res.table.filter(pl.col("category").is_in(list(db.COUNTS)))
    assert counts["crps_nb"].mean() < counts["crps_poisson"].mean()  # type: ignore[operator]
    assert 1.0 < res.dispersion["pts"] < 4.0


def test_poisson_data_gives_no_real_gain() -> None:
    logs = _logs(size=1e7, players=40)
    res = db.run(logs, n_boot=200)
    assert not res.ships
