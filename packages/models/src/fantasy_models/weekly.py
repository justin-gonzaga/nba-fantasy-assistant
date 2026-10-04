"""Rest-of-week projections for the daily brief (MVP piece 2).

expected stat total = per-game projection x expected games left this fantasy week, where each
remaining game counts with the probability the player plays it:
- no injury listing for that game: the base availability, projected season games / 82;
- listed on the official injury report for that game date: the probability for his status.

The status probabilities are measured from our own injury-report history (MVP-002), because
RSCH-002 found no measured source and the circulating numbers are unverifiable.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

import polars as pl

SEASON_GAMES = 82.0
STATUS_PLAY_PROB: dict[str, float] = {  # measured: MVP-002, 2024-25 + 2025-26, ~5:30 PM ET report
    "Available": 0.827,
    "Probable": 0.918,
    "Questionable": 0.489,
    "Doubtful": 0.011,
    "Out": 0.001,
}
STATUS_PLAY_PROB_SOURCE = (
    "MEASURED: docs/evaluation/reports/MVP-002-availability.md (327 game days, 25,809 scored rows; "
    "day-clustered bootstrap CIs)"
)
_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


@dataclass(frozen=True)
class Week:
    start: date
    end: date


@dataclass(frozen=True)
class InjuryMatch:
    matched: pl.DataFrame  # nba_player_id, game_date, status
    unmatched: list[str]


def name_key(name: str) -> str:
    """'Dončić, Luka' and 'Luka Doncic' -> 'luka doncic'; suffixes (Jr., III) dropped."""
    if "," in name:
        last, first = (p.strip() for p in name.split(",", 1))
        name = f"{first} {last}"
    ascii_ = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    words = re.sub(r"[^a-z ]", "", ascii_.lower().replace("-", " ")).split()
    return " ".join(w for w in words if w not in _SUFFIXES)


def match_injuries(
    injuries: pl.DataFrame, roster: pl.DataFrame, teams: dict[str, str]
) -> InjuryMatch:
    """Map report rows (player 'Last, First', team full name) to nba_player_id by name + team."""
    keyed = roster.with_columns(
        pl.col("player_name").map_elements(name_key, return_dtype=pl.String).alias("key")
    )
    lookup = {(r["key"], r["team"]): r["nba_player_id"] for r in keyed.iter_rows(named=True)}
    rows, unmatched = [], []
    for r in injuries.iter_rows(named=True):
        pid = lookup.get((name_key(r["player"]), teams.get(r["team"], "")))
        if pid is None:
            unmatched.append(r["player"])
        else:
            rows.append({"nba_player_id": pid, "game_date": r["game_date"], "status": r["status"]})
    schema = {"nba_player_id": pl.Int64, "game_date": pl.Date, "status": pl.String}
    return InjuryMatch(pl.DataFrame(rows, schema=schema), unmatched)


def project(  # noqa: PLR0913 - the brief's inputs, all explicit
    per_game: pl.DataFrame,
    roster: pl.DataFrame,
    schedule: pl.DataFrame,
    *,
    week: Week,
    today: date,
    injuries: pl.DataFrame | None = None,
    teams: dict[str, str] | None = None,
) -> pl.DataFrame:
    """One row per rostered player: games_left, plays_today, status_today, exp_games and the
    expected rest-of-week total of every projected per-game stat."""
    wide = per_game.pivot(on="stat", index="nba_player_id", values="mean")
    stats = [c for c in wide.columns if c not in {"nba_player_id", "games", "mpg"}]
    base = wide.select(
        "nba_player_id",
        (pl.col("games") / SEASON_GAMES).clip(0.0, 1.0).alias("base_avail"),
        *stats,
    )
    left = schedule.filter(
        (pl.col("game_date") >= max(today, week.start)) & (pl.col("game_date") <= week.end)
    )
    team_games = pl.concat(
        [
            left.select("game_id", "game_date", pl.col("away").alias("team")),
            left.select("game_id", "game_date", pl.col("home").alias("team")),
        ]
    )
    games = roster.select("nba_player_id", "team").join(team_games, on="team", how="inner")
    status = pl.DataFrame(
        schema={"nba_player_id": pl.Int64, "game_date": pl.Date, "status": pl.String}
    )
    if injuries is not None:
        status = match_injuries(injuries, roster, teams or {}).matched
    probs = pl.DataFrame(
        {"status": list(STATUS_PLAY_PROB), "status_prob": list(STATUS_PLAY_PROB.values())}
    )
    games = (
        games.join(base.select("nba_player_id", "base_avail"), on="nba_player_id", how="left")
        .join(status, on=["nba_player_id", "game_date"], how="left")
        .join(probs, on="status", how="left")
        .with_columns(
            pl.coalesce("status_prob", "base_avail").fill_null(0.0).alias("p_play"),
            (pl.col("game_date") == today).alias("today"),
        )
    )
    per_player = games.group_by("nba_player_id").agg(
        pl.len().alias("games_left"),
        pl.col("p_play").sum().alias("exp_games"),
        pl.col("today").any().alias("plays_today"),
        pl.col("status").filter(pl.col("today")).first().alias("status_today"),
    )
    out = (
        roster.join(per_player, on="nba_player_id", how="left")
        .join(base, on="nba_player_id", how="left")
        .with_columns(
            pl.col("games_left").fill_null(0).cast(pl.Int64),
            pl.col("exp_games").fill_null(0.0),
            pl.col("plays_today").fill_null(value=False),
        )
    )
    return out.with_columns([(pl.col(s) * pl.col("exp_games")).alias(s) for s in stats]).drop(
        "base_avail"
    )
