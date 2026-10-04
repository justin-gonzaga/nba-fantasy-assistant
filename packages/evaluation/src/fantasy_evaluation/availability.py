"""How often players listed on the official injury report actually play (MVP-002).

RSCH-002 found no measured source for these rates, so we measure them: each report row (player,
status, game date) is joined to that season's game logs. The player plays if he has a log row on
that date. Rows whose player never appears in the season's logs can't be scored and are counted
as unmatched. Intervals: bootstrap resampling whole game days, since rows from the same day share
news and schedules [R-54].
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from fantasy_models.weekly import name_key

ORDER = ["Available", "Probable", "Questionable", "Doubtful", "Out"]


@dataclass(frozen=True)
class Outcomes:
    rows: pl.DataFrame  # player, team, game_date, status, played
    unmatched: int


def outcomes(report: pl.DataFrame, logs: pl.DataFrame) -> Outcomes:
    keyed = logs.with_columns(
        pl.col("PLAYER_NAME").map_elements(name_key, return_dtype=pl.String).alias("key"),
        pl.col("GAME_DATE").str.to_date(),
    )
    ids = keyed.select("key", pl.col("TEAM_NAME").alias("team"), "PLAYER_ID").unique()
    played = keyed.select("PLAYER_ID", pl.col("GAME_DATE").alias("game_date")).unique()
    rep = report.with_columns(
        pl.col("player").map_elements(name_key, return_dtype=pl.String).alias("key")
    ).join(ids, on=["key", "team"], how="left")
    unmatched = rep.filter(pl.col("PLAYER_ID").is_null()).height
    scored = (
        rep.filter(pl.col("PLAYER_ID").is_not_null())
        .join(
            played.with_columns(pl.lit(value=True).alias("played")),
            on=["PLAYER_ID", "game_date"],
            how="left",
        )
        .with_columns(pl.col("played").fill_null(value=False))
        .select("player", "team", "game_date", "status", "played")
    )
    return Outcomes(scored, unmatched)


def rates(rows: pl.DataFrame, *, n_boot: int = 2000, seed: int = 0) -> pl.DataFrame:
    """Per status: n, play rate, and a 95 % day-clustered bootstrap interval."""
    rng = np.random.default_rng(seed)
    out = []
    for status in [s for s in ORDER if s in set(rows["status"].to_list())]:
        sub = rows.filter(pl.col("status") == status)
        by_day = (
            sub.group_by("game_date")
            .agg(pl.col("played").sum().alias("k"), pl.len().alias("n"))
            .sort("game_date")  # a fixed cluster order keeps the bootstrap reproducible
        )
        k, n = by_day["k"].to_numpy(), by_day["n"].to_numpy()
        lo, hi = bs.ratio_ci(k, n, n_boot, rng)
        out.append(
            {
                "status": status,
                "n": int(n.sum()),
                "rate": float(k.sum() / n.sum()),
                "lo": lo,
                "hi": hi,
            }
        )
    return pl.DataFrame(out)
