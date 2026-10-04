"""RSCH-008: are in-season calendar trends real? (pre-registered in the task file)

Q1 — a "second-half player": is a player's after-minus-before All-Star-break change in per-game
     value repeatable from one season to the next? (correlation, bootstrap CI over players)
Q2 — late-season rest and tanking: after 1 Mar, games missed and minutes change by team context
     and role.
Q3 — fantasy playoffs: how much does weighting the playoff weeks' schedule move draft ranks?
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from itertools import pairwise

import numpy as np
import polars as pl

from fantasy_models.preseason.breakouts import _zsum  # the project's 9-cat z-sum definition

STATS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta")
MIN_HALF_GAMES = 20
MIN_PRE_GAMES = 10
MIN_TEAM_POST = 10
CONTENDERS = 4
BOTTOM = 6


def tidy(logs: pl.DataFrame) -> pl.DataFrame:
    """Raw LeagueGameLog rows → snake-case stats with a date and float minutes."""
    return logs.select(
        pl.col("SEASON").alias("season"),
        pl.col("PLAYER_ID").cast(pl.Int64).alias("player"),
        pl.col("TEAM_ID").cast(pl.Int64).alias("team"),
        pl.col("GAME_ID").alias("game"),
        pl.col("GAME_DATE").str.slice(0, 10).str.to_date().alias("day"),
        pl.col("WL").alias("wl"),
        pl.col("MIN").cast(pl.Float64).fill_null(0).alias("min"),
        *[pl.col(s.upper()).cast(pl.Float64).fill_null(0).alias(s) for s in STATS],
    )


def all_star_break(season: pl.DataFrame) -> date:
    """First day of the longest league-wide gap without games between 1 Feb and 15 Mar."""
    days = sorted(set(season.get_column("day").to_list()))
    year = max(days).year
    window = [d for d in days if date(year, 2, 1) <= d <= date(year, 3, 15)]
    best, start = 0, window[0]
    for a, b in pairwise(window):
        gap = (b - a).days
        if gap > best:
            best, start = gap, a
    return date.fromordinal(start.toordinal() + 1)


def value_of(df: pl.DataFrame) -> np.ndarray:
    """9-cat per-game z-sum of aggregated rows with a `games` column (amendment 3)."""
    return _zsum(df.rename({"games": "gp"}), "gp")


def half_values(season: pl.DataFrame) -> pl.DataFrame:
    """Per player: per-game (and per-36) value before/after the break, ≥ 20 games each half."""
    asb = all_star_break(season)
    agg = (
        season.with_columns((pl.col("day") >= asb).alias("second"))
        .group_by("player", "second")
        .agg(pl.len().alias("games"), pl.col("min").sum(), *[pl.col(s).sum() for s in STATS])
        .filter(pl.col("games") >= MIN_HALF_GAMES)
    )
    out = []
    for second in (False, True):
        part = agg.filter(pl.col("second") == second)
        per_min = part.with_columns([(pl.col(s) / pl.col("min") * 36) for s in STATS]).with_columns(
            pl.lit(1).alias("games")
        )
        out.append(
            part.select("player").with_columns(
                pl.Series(f"v{int(second)}", value_of(part)),
                pl.Series(f"m{int(second)}", value_of(per_min)),
            )
        )
    both = out[0].join(out[1], on="player", how="inner")
    return both.with_columns(
        (pl.col("v1") - pl.col("v0")).alias("delta"),
        (pl.col("m1") - pl.col("m0")).alias("delta_per36"),
    )


@dataclass(frozen=True)
class Persistence:
    n: int
    r: float
    ci: tuple[float, float]
    r_per36: float
    ci_per36: tuple[float, float]


def _boot_corr(
    x: np.ndarray, y: np.ndarray, rng: np.random.Generator, n_boot: int
) -> tuple[float, float]:
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    rs = [float(np.corrcoef(x[i], y[i])[0, 1]) for i in idx]
    return float(np.nanpercentile(rs, 2.5)), float(np.nanpercentile(rs, 97.5))


def pair_up(deltas: Mapping[str, pl.DataFrame]) -> pl.DataFrame:
    """Join each season's changes to the next season's, for consecutive seasons only."""
    keys = sorted(deltas)
    pairs = [
        deltas[a].join(deltas[b], on="player", suffix="_next")
        for a, b in pairwise(keys)
        if int(b[:4]) == int(a[:4]) + 1
    ]
    return pl.concat(pairs)


def persistence(pairs: pl.DataFrame, n_boot: int = 2000, seed: int = 0) -> Persistence:
    """Correlation of a player's change in season s with his change in s+1, pooled over pairs."""
    rng = np.random.default_rng(seed)
    x, y = pairs["delta"].to_numpy(), pairs["delta_next"].to_numpy()
    xm, ym = pairs["delta_per36"].to_numpy(), pairs["delta_per36_next"].to_numpy()
    return Persistence(
        pairs.height,
        float(np.corrcoef(x, y)[0, 1]),
        _boot_corr(x, y, rng, n_boot),
        float(np.corrcoef(xm, ym)[0, 1]),
        _boot_corr(xm, ym, rng, n_boot),
    )


def team_context(season: pl.DataFrame, cutoff: date) -> pl.DataFrame:
    """Each team's group on `cutoff` by league-wide win % (amendment 1)."""
    games = season.filter(pl.col("day") < cutoff).unique(["team", "game"])
    wp = games.group_by("team").agg((pl.col("wl") == "W").mean().alias("win_pct"))
    ranked = wp.sort("win_pct", descending=True).with_row_index("rank", offset=1)
    n = ranked.height
    return ranked.select(
        "team",
        pl.when(pl.col("rank") <= CONTENDERS)
        .then(pl.lit("contender"))
        .when(pl.col("rank") > n - BOTTOM)
        .then(pl.lit("bottom-6"))
        .otherwise(pl.lit("mid-race"))
        .alias("context"),
    )


def late_season(season: pl.DataFrame, cutoff: date, roles: pl.DataFrame) -> pl.DataFrame:
    """Per player: extra games missed after `cutoff` and the mpg change (amendment 4).

    `roles`: player, role. Players are attributed to the team they played for last before `cutoff`.
    """
    team_games = season.unique(["team", "game", "day"]).with_columns(
        (pl.col("day") >= cutoff).alias("post")
    )
    tg = team_games.group_by("team", "post").agg(pl.len().alias("team_games"))
    s = season.with_columns((pl.col("day") >= cutoff).alias("post"))
    last_team = s.filter(~pl.col("post")).sort("day").group_by("player").agg(pl.col("team").last())
    pg = s.group_by("player", "post").agg(pl.len().alias("games"), pl.col("min").sum())
    pre = pg.filter(~pl.col("post")).drop("post").rename({"games": "g0", "min": "min0"})
    post = pg.filter(pl.col("post")).drop("post").rename({"games": "g1", "min": "min1"})
    df = (
        pre.join(last_team, on="player")
        .join(post, on="player", how="left")
        .join(
            tg.filter(~pl.col("post")).select("team", pl.col("team_games").alias("t0")), on="team"
        )
        .join(tg.filter(pl.col("post")).select("team", pl.col("team_games").alias("t1")), on="team")
        .fill_null(0)
        .filter((pl.col("g0") >= MIN_PRE_GAMES) & (pl.col("t1") >= MIN_TEAM_POST))
        .join(team_context(season, cutoff), on="team")
        .join(roles, on="player")
    )
    return df.select(
        "player",
        "context",
        "role",
        ((pl.col("g0") / pl.col("t0") - pl.col("g1") / pl.col("t1")) * pl.col("t1")).alias(
            "games_missed_extra"
        ),
        pl.when(pl.col("g1") > 0)
        .then(pl.col("min1") / pl.col("g1") - pl.col("min0") / pl.col("g0"))
        .otherwise(None)
        .alias("mpg_change"),
    )


def effect_table(rows: pl.DataFrame, n_boot: int = 2000, seed: int = 0) -> pl.DataFrame:
    """Mean effects with bootstrap 95 % CIs per (context, role)."""
    rng = np.random.default_rng(seed)
    out = []
    for (ctx, role), g in rows.group_by("context", "role"):
        rec: dict[str, object] = {"context": ctx, "role": role, "n": g.height}
        for col in ("games_missed_extra", "mpg_change"):
            x = g.get_column(col).drop_nulls().to_numpy()
            if len(x) < 2:  # noqa: PLR2004
                rec |= {col: None, f"{col}_lo": None, f"{col}_hi": None}
                continue
            idx = rng.integers(0, len(x), size=(n_boot, len(x)))
            means = x[idx].mean(axis=1)
            rec |= {
                col: float(x.mean()),
                f"{col}_lo": float(np.percentile(means, 2.5)),
                f"{col}_hi": float(np.percentile(means, 97.5)),
            }
        out.append(rec)
    return pl.DataFrame(out).sort("context", "role")


def material(row: Mapping[str, object]) -> bool:
    """Pre-registered: ≥ 2 extra games missed or a ≥ 3 mpg change, with a CI excluding 0."""

    def sig(col: str, size: float) -> bool:
        v, lo, hi = row.get(col), row.get(f"{col}_lo"), row.get(f"{col}_hi")
        if not isinstance(v, float) or not isinstance(lo, float) or not isinstance(hi, float):
            return False
        return abs(v) >= size and (lo > 0 or hi < 0)

    return sig("games_missed_extra", 2.0) or sig("mpg_change", 3.0)


def playoff_weighted_ranks(
    values: pl.DataFrame, playoff_games: Mapping[int, int], season_games: int, w: float
) -> pl.DataFrame:
    """Q3 (amendment 5): value * (1 + (w - 1) * P/S), P = his team's playoff-week games."""
    p = pl.DataFrame(
        {"team": list(playoff_games), "p": [playoff_games[t] for t in playoff_games]},
        schema={"team": pl.Int64, "p": pl.Int64},
    )
    df = values.join(p, on="team", how="left").with_columns(pl.col("p").fill_null(0))
    weighted = df.with_columns(
        (pl.col("value") * (1 + (w - 1) * pl.col("p") / season_games)).alias("value_w")
    )
    return weighted.with_columns(
        # signed ints: rank differences can be negative (unsigned ranks wrap around)
        pl.col("value").rank("ordinal", descending=True).cast(pl.Int64).alias("rank"),
        pl.col("value_w").rank("ordinal", descending=True).cast(pl.Int64).alias("rank_w"),
    )
