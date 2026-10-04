"""Shared definitions for preseason projections (ml-methodology-plan §1).

Inputs mirror the warehouse tables `intermediate.int_player_season` (one row per player-season)
and `intermediate.int_player_profile` (one row per rostered player). Shooting stats stay as
makes and attempts; percentages are derived, never averaged.
"""

from __future__ import annotations

import re

import polars as pl

from dikit.errors import LeakageError

# Per-minute counting stats modelled directly. Makes come from attempts x a shooting %.
ATTEMPT_STATS = ("fga", "fg3a", "fta")
OTHER_RATE_STATS = ("reb", "ast", "stl", "blk", "tov")
RATE_STATS = ATTEMPT_STATS + OTHER_RATE_STATS
# shooting % name -> (makes, attempts)
PCT_STATS = {"fg_pct": ("fgm", "fga"), "fg3_pct": ("fg3m", "fg3a"), "ft_pct": ("ftm", "fta")}
# Per-game outputs (every stat Yahoo can score from the box score).
PER_GAME_STATS = (
    "fgm",
    "fga",
    "fg3m",
    "fg3a",
    "ftm",
    "fta",
    "reb",
    "ast",
    "stl",
    "blk",
    "tov",
    "pts",
)

SEASON_COLUMNS = {
    "season": pl.String,
    "nba_player_id": pl.Int64,
    "age": pl.Float64,
    "games_played": pl.Int64,
    "season_team_games": pl.Int64,
    "minutes": pl.Float64,
    **dict.fromkeys(
        ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "reb", "ast", "stl", "blk", "tov", "pts"),
        pl.Int64,
    ),
}

TEAM_COLUMNS = ("first_nba_team_id", "last_nba_team_id")

_SEASON = re.compile(r"^(\d{4})-(\d{2})$")


def start_year(season: str) -> int:
    m = _SEASON.match(season)
    if not m:
        msg = f"invalid season {season!r}"
        raise ValueError(msg)
    return int(m.group(1))


def season_of(year: int) -> str:
    return f"{year}-{(year + 1) % 100:02d}"


def assert_no_future(history: pl.DataFrame, target: str) -> None:
    """Leakage guard (AC3): a projection for `target` may only see earlier seasons."""
    bad = history.filter(pl.col("season") >= target)
    if bad.height:
        seasons = sorted(bad.get_column("season").unique().to_list())
        msg = f"history for target {target} contains seasons {seasons}"
        raise LeakageError(msg)


def history_before(seasons: pl.DataFrame, target: str) -> pl.DataFrame:
    return seasons.filter(pl.col("season") < target)


def validate_seasons(seasons: pl.DataFrame) -> pl.DataFrame:
    missing = set(SEASON_COLUMNS) - set(seasons.columns)
    if missing:
        msg = f"int_player_season frame is missing columns {sorted(missing)}"
        raise ValueError(msg)
    cols = [pl.col(c).cast(t) for c, t in SEASON_COLUMNS.items()]
    # optional team columns (DRAFT-007 features)
    cols += [pl.col(c).cast(pl.Int64) for c in TEAM_COLUMNS if c in seasons.columns]
    return seasons.select(cols)
