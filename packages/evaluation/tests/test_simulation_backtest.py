from datetime import date, timedelta

import numpy as np
import polars as pl

from fantasy_evaluation import simulation_backtest as sb

RNG = np.random.default_rng(5)


def _logs(players: int = 40) -> pl.DataFrame:
    """Synthetic 2025-26 season with over-dispersed counts; weeks after 19 Jan are the holdout."""
    rows = []
    start = date(2025, 12, 1)
    for p in range(players):
        base = RNG.uniform(0.5, 2.0)
        for i in range(0, 90, 2):
            row: dict[str, object] = {
                "SEASON": "2025-26",
                "PLAYER_ID": p,
                "GAME_DATE": (start + timedelta(days=i)).isoformat(),
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
                row[col] = int(RNG.negative_binomial(3.0, 3.0 / (3.0 + m * base)))
            fga = int(RNG.negative_binomial(6.0, 6.0 / (6.0 + 12 * base)))
            fta = int(RNG.negative_binomial(2.0, 2.0 / (2.0 + 4 * base)))
            row |= {
                "FGA": fga,
                "FGM": int(RNG.binomial(fga, 0.47)),
                "FTA": fta,
                "FTM": int(RNG.binomial(fta, 0.78)),
            }
            rows.append(row)
    return pl.DataFrame(rows)


def test_backtest_scores_both_methods_on_real_outcomes() -> None:
    res = sb.run(_logs(), n_boot=100, matchups=5)
    assert res.matchups > 0
    assert set(res.table["category"].to_list()) == set(sb.CATS)
    # Both methods beat a coin flip (Brier 0.25) on average.
    assert float(res.table["b_normal"].mean()) < 0.25  # type: ignore[arg-type]
    assert float(res.table["b_sim"].mean()) < 0.25  # type: ignore[arg-type]
    assert res.ci[0] <= res.pooled_diff <= res.ci[1]
    assert 0 < res.mc_se < 0.1
    assert int(res.reliability["n"].sum()) == res.matchups * len(sb.CATS)
