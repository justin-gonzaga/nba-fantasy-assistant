"""In-season projection update (ANL-005; methodology §14, D-61).

Empirical-Bayes-style blend of the pre-season projection (the prior, per game) with the season so
far: per game = (k * prior + season total) / (k + games played). k works like k games' worth of
prior evidence: early in the season the prior dominates, later the season's own numbers do [R-12].
One k per stat is chosen on selection data by minimising the weekly MAE over a fixed grid.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from numpy.typing import NDArray

Array = NDArray[np.float64]
# Shipped by the pre-registered ANL-005 test (docs/evaluation/reports/ANL-005-inseason-update.md):
# games' worth of pre-season prior per stat, chosen on selection weeks.
K_SHIPPED: dict[str, float] = {
    "pts": 3.0,
    "reb": 5.0,
    "ast": 3.0,
    "stl": 20.0,
    "blk": 8.0,
    "fg3m": 5.0,
    "tov": 8.0,
    "fgm": 3.0,
    "fga": 2.0,
    "ftm": 8.0,
    "fta": 5.0,
}


def update_long(per_game: pl.DataFrame, season: pl.DataFrame) -> pl.DataFrame:
    """Blend long-format per-game projections (nba_player_id, stat, mean) with the season so far.

    `season`: nba_player_id, games and season totals per stat (same names). Stats without a shipped
    k (games, minutes) and players without games this season keep their projection."""
    totals = season.unpivot(
        index=["nba_player_id", "games"], variable_name="stat", value_name="total"
    ).filter(pl.col("stat").is_in(list(K_SHIPPED)))
    k = pl.DataFrame({"stat": list(K_SHIPPED), "k": list(K_SHIPPED.values())})
    joined = per_game.join(totals, on=["nba_player_id", "stat"], how="left").join(
        k, on="stat", how="left"
    )
    blended = (pl.col("k") * pl.col("mean") + pl.col("total")) / (pl.col("k") + pl.col("games"))
    return joined.with_columns(
        pl.when(pl.col("games") > 0).then(blended).otherwise(pl.col("mean")).alias("mean")
    ).select(per_game.columns)
