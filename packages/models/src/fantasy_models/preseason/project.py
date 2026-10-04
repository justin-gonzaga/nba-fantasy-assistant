"""Assemble projections for a draft pool: history-based method + rookie priors + uncertainty."""

from __future__ import annotations

from collections.abc import Callable

import polars as pl

from fantasy_models.preseason.methods import rookie_priors, rookie_projection, this_draft_pick
from fantasy_models.preseason.schema import PER_GAME_STATS, assert_no_future, history_before

Method = Callable[[pl.DataFrame, str], pl.DataFrame]

# Minutes-per-game bands used for the empirical sd (plan §1 "Uncertainty").
MPG_BANDS = (0.0, 15.0, 25.0, 32.0, 60.0)
ROOKIE_SD_INFLATION = 1.5
SD_STATS = ("mpg", "games", *PER_GAME_STATS)


def mpg_band(mpg: pl.Expr) -> pl.Expr:
    return mpg.cut(list(MPG_BANDS[1:-1]), labels=[f"b{i}" for i in range(len(MPG_BANDS) - 1)]).cast(
        pl.String
    )


def project_pool(  # noqa: PLR0913 - explicit inputs keep the leakage boundary visible
    seasons: pl.DataFrame,
    draft: pl.DataFrame,
    pool: pl.DataFrame,
    target: str,
    method: Method,
    *,
    season_games: int = 82,
) -> pl.DataFrame:
    """Per-game means for every player in `pool` (nba_player_id, overall_pick).

    Players with at least one season in the three-season window use `method`; everyone else
    gets their draft-bucket rookie prior. `source` records which.
    """
    history = history_before(seasons, target)
    assert_no_future(history, target)
    vets = method(history, target).with_columns(pl.lit("history").alias("source"))
    in_pool = pool.select("nba_player_id")
    vets = vets.join(in_pool, on="nba_player_id", how="semi")
    newcomers = this_draft_pick(
        in_pool.join(vets.select("nba_player_id"), on="nba_player_id", how="anti"), draft, target
    )
    rookies = rookie_projection(
        newcomers, rookie_priors(history, draft, target), season_games
    ).with_columns(pl.lit("rookie_prior").alias("source"))
    return pl.concat([vets, rookies], how="vertical_relaxed").with_columns(
        mpg_band(pl.col("mpg")).alias("mpg_band")
    )


def residual_sds(pred: pl.DataFrame, actual: pl.DataFrame) -> pl.DataFrame:
    """Empirical per-game sd (RMSE of the residuals) per stat and mpg band, long format."""
    df = pred.join(actual, on="nba_player_id", suffix="_actual")
    return (
        df.unpivot(
            index=["nba_player_id", "mpg_band"],
            on=list(SD_STATS),
            variable_name="stat",
            value_name="pred",
        )
        .join(
            df.unpivot(
                index=["nba_player_id"],
                on=[f"{s}_actual" for s in SD_STATS],
                variable_name="stat",
                value_name="actual",
            ).with_columns(pl.col("stat").str.strip_suffix("_actual")),
            on=["nba_player_id", "stat"],
        )
        .group_by("stat", "mpg_band")
        .agg(
            ((pl.col("pred") - pl.col("actual")) ** 2).mean().sqrt().alias("sd"),
            pl.len().alias("n"),
        )
    )


def with_uncertainty(proj: pl.DataFrame, sds: pl.DataFrame) -> pl.DataFrame:
    """Long format: one row per player x stat with mean and sd (AC1)."""
    long = proj.unpivot(
        index=["nba_player_id", "source", "mpg_band"],
        on=list(SD_STATS),
        variable_name="stat",
        value_name="mean",
    )
    fallback = sds.group_by("stat").agg(pl.col("sd").max().alias("sd_fallback"))
    out = (
        long.join(sds.select("stat", "mpg_band", "sd"), on=["stat", "mpg_band"], how="left")
        .join(fallback, on="stat", how="left")
        .with_columns(pl.coalesce("sd", "sd_fallback").alias("sd"))
        .with_columns(
            pl.when(pl.col("source") == "rookie_prior")
            .then(pl.col("sd") * ROOKIE_SD_INFLATION)
            .otherwise(pl.col("sd"))
            .alias("sd")
        )
    )
    return out.select("nba_player_id", "source", "stat", "mean", "sd")
