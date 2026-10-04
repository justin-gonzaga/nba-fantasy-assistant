"""Availability overrides (D-47 Q2; data-pipeline-design S8).

Owner-reviewed absences from public news.

The CSV lives in the repo (warehouse/seeds/availability_overrides.csv). Each row caps a player's
expected games; nothing is guessed:
- est_games_missed given -> games cap = season games - est_games_missed
- else expected_return given -> cap = season games x share of the season left after that date
- else (out indefinitely, no estimate) -> no numeric change; the board shows the status tag
DATA-036 raises (status `cleared`, e.g. "no minutes restriction"): `expected_games` raises games
(never lowers them) and `expected_mpg` sets minutes, scaling every per-game counting stat by the
minutes ratio (the projection is per-minute rates x minutes). Same evidence rule: a source URL, its
date and a verbatim quote, reviewed by the owner.
Point in time: every source_date must be on or before the draft (as_of).
"""

from __future__ import annotations

import unicodedata
from datetime import date
from pathlib import Path

import polars as pl

from dikit.errors import ContractViolation

SEASON_START = date(2026, 10, 20)
SEASON_END = date(2027, 4, 11)
SEASON_GAMES = 82
STATUSES = {
    "out_indefinitely",
    "out_until_date",
    "suspended",
    "questionable_start",
    "holdout",
    "cleared",
}
RAISE_COLUMNS = ("expected_games", "expected_mpg")
MAX_MPG = 40.0
DEFAULT_PATH = Path("warehouse/seeds/availability_overrides.csv")


def norm(name: str) -> str:
    """Accent/case/punctuation-insensitive key: 'Nikola Jokic' == 'Nikola Jokić'."""
    ascii_ = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(ch for ch in ascii_.lower() if ch.isalnum())


def load(path: Path, as_of: date) -> pl.DataFrame:
    if not path.exists():
        return pl.DataFrame(
            schema={"player_name": pl.String, "status": pl.String, "games_cap": pl.Float64}
        )
    df = pl.read_csv(path, try_parse_dates=False, infer_schema_length=0)
    for col in RAISE_COLUMNS:  # older files predate DATA-036
        if col not in df.columns:
            df = df.with_columns(pl.lit(None, pl.String).alias(col))
    bad = df.filter(~pl.col("status").is_in(sorted(STATUSES)))
    if bad.height:
        msg = f"unknown override status: {bad['status'].to_list()}"
        raise ContractViolation(msg)
    late = df.filter(pl.col("source_date").str.to_date() > pl.lit(as_of))
    if late.height:
        names = late["player_name"].to_list()
        msg = f"override sources dated after the draft (as_of {as_of}): {names}"
        raise ContractViolation(msg)
    _check_raises(df)
    return df.with_columns(
        games_cap_expr().alias("games_cap"),
        pl.when(pl.col("status") == "cleared")
        .then(pl.col("expected_games").cast(pl.Float64, strict=False))
        .alias("games_floor"),
        pl.when(pl.col("status") == "cleared")
        .then(pl.col("expected_mpg").cast(pl.Float64, strict=False))
        .alias("mpg_set"),
    )


def _check_raises(df: pl.DataFrame) -> None:
    """DATA-036: cleared rows need evidence, a number, plausible values and no contradiction."""
    raises = df.filter(pl.col("status") == "cleared")
    if raises.height == 0:
        return
    blank = (pl.col("source_url").fill_null("") == "") | (pl.col("quote").fill_null("") == "")
    if (missing := raises.filter(blank)).height:
        names = missing["player_name"].to_list()
        msg = f"cleared overrides need evidence (source_url and quote): {names}"
        raise ContractViolation(msg)
    capped = (pl.col("est_games_missed").fill_null("") != "") | (
        pl.col("expected_return").fill_null("") != ""
    )
    if (mixed := raises.filter(capped)).height:
        names = mixed["player_name"].to_list()
        msg = f"cleared overrides cannot carry cap fields (games missed, return date): {names}"
        raise ContractViolation(msg)
    games = pl.col("expected_games").cast(pl.Float64, strict=False)
    mpg = pl.col("expected_mpg").cast(pl.Float64, strict=False)
    if (empty := raises.filter(games.is_null() & mpg.is_null())).height:
        names = empty["player_name"].to_list()
        msg = f"cleared overrides need expected_games or expected_mpg: {names}"
        raise ContractViolation(msg)
    wild = raises.filter(
        (games.is_not_null() & ((games <= 0) | (games > SEASON_GAMES)))
        | (mpg.is_not_null() & ((mpg <= 0) | (mpg > MAX_MPG)))
    )
    if wild.height:
        names = wild["player_name"].to_list()
        msg = f"implausible cleared values (games 1-{SEASON_GAMES}, mpg 1-{MAX_MPG:.0f}): {names}"
        raise ContractViolation(msg)
    keys = df.with_columns(
        pl.col("player_name").map_elements(norm, return_dtype=pl.String).alias("k")
    )
    both = (
        keys.group_by("k")
        .agg(
            (pl.col("status") == "cleared").any().alias("raise"),
            (pl.col("status") != "cleared").any().alias("cap"),
        )
        .filter(pl.col("raise") & pl.col("cap"))
    )
    if both.height:
        msg = f"contradictory overrides (a raise and a cap) for: {both['k'].to_list()}"
        raise ContractViolation(msg)


def games_cap_expr() -> pl.Expr:
    season_days = (SEASON_END - SEASON_START).days
    ret = pl.col("expected_return").str.to_date(strict=False)
    left = (
        (pl.lit(SEASON_END) - ret).dt.total_days().clip(0, season_days) / season_days
    ) * SEASON_GAMES
    est = pl.col("est_games_missed").cast(pl.Float64, strict=False)
    return (
        pl.when(est.is_not_null())
        .then((SEASON_GAMES - est).clip(0, SEASON_GAMES))
        .when(ret.is_not_null())
        .then(left)
        .otherwise(None)
    )


def resolve(overrides: pl.DataFrame, profile: pl.DataFrame) -> pl.DataFrame:
    """Attach nba_player_id by normalised name; every override must match exactly one player."""
    keys = profile.select(
        "nba_player_id", pl.col("player_name").map_elements(norm, return_dtype=pl.String).alias("k")
    )
    o = overrides.with_columns(
        pl.col("player_name").map_elements(norm, return_dtype=pl.String).alias("k")
    )
    j = o.join(keys, on="k", how="left")
    missing = j.filter(pl.col("nba_player_id").is_null())["player_name"].to_list()
    dupes = j.group_by("k").len().filter(pl.col("len") > 1)["k"].to_list()
    if missing or dupes:
        msg = (
            f"override names not matched uniquely to 2026-27 rosters: "
            f"missing={missing} ambiguous={dupes}"
        )
        raise ContractViolation(msg)
    return j.drop("k")


def apply(proj: pl.DataFrame, resolved: pl.DataFrame) -> pl.DataFrame:
    """Cap (absences) or raise (cleared) projected games, and set minutes with per-game stats scaled
    (wide projection frame with nba_player_id, games, mpg and per-game stats)."""
    cols = [c for c in ("games_cap", "games_floor", "mpg_set") if c in resolved.columns]
    adj = resolved.select("nba_player_id", *cols)
    for c in ("games_cap", "games_floor", "mpg_set"):
        if c not in adj.columns:
            adj = adj.with_columns(pl.lit(None, pl.Float64).alias(c))
    out = proj.join(adj, on="nba_player_id", how="left").with_columns(
        pl.min_horizontal("games", pl.col("games_cap").fill_null(float("inf"))).alias("games")
    )
    out = out.with_columns(
        pl.max_horizontal("games", pl.col("games_floor").fill_null(float("-inf"))).alias("games")
    )
    if "mpg" in out.columns:
        counts = [
            c
            for c, t in out.schema.items()
            if t.is_numeric()
            and c not in {"nba_player_id", "games", "mpg", "games_cap", "games_floor", "mpg_set"}
            and not c.endswith("_pct")
        ]
        ratio = (
            pl.when(pl.col("mpg_set").is_not_null() & (pl.col("mpg") > 0))
            .then(pl.col("mpg_set") / pl.col("mpg"))
            .otherwise(1.0)
        )
        out = out.with_columns([(pl.col(c) * ratio).alias(c) for c in counts]).with_columns(
            pl.coalesce("mpg_set", "mpg").alias("mpg")
        )
    return out.drop("games_cap", "games_floor", "mpg_set")


def adjustments(resolved: pl.DataFrame) -> pl.DataFrame:
    """DATA-036: per raised player, the note the site shows ("Cleared: <quote> (<date>)")."""
    cleared = resolved.filter(pl.col("status") == "cleared")
    return cleared.select(
        "nba_player_id",
        pl.format("Cleared: {} ({})", pl.col("quote"), pl.col("source_date")).alias("adjusted"),
    )
