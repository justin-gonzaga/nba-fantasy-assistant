"""DEC-007: replay the lineup optimiser against greedy on every 2025-26 game day (pre-registered).

16 sample rosters (a snake draft of the top 224 by value); on each game day, the players with a
game-log row are the ones who play. Both methods maximise (active players, then total value).
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import polars as pl

from fantasy_decision import lineup as lu
from fantasy_models.valuation import eligibility

TEAMS = 16
ROUNDS = 14
SLOTS = {"G": 3, "F": 3, "C": 1, "Util": 3}
STATS = ["PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV", "FGM", "FGA", "FTM", "FTA"]


@dataclass(frozen=True)
class Result:
    lineups: int
    better_count: int  # more active players than greedy
    better_value: int  # same active count, more value
    worse: int  # must be 0 to ship
    illegal: int  # must be 0 to ship
    max_seconds: float
    mean_extra_active: float  # over the lineups where the optimiser started more players
    ships: bool
    standings: pl.DataFrame | None = None  # per roster: actual stats of started players, roto ranks


def rosters(values: pl.DataFrame) -> list[list[int]]:
    order = values.sort("value", descending=True)["nba_player_id"].to_list()[: TEAMS * ROUNDS]
    squads: list[list[int]] = [[] for _ in range(TEAMS)]
    for i, pid in enumerate(order):
        rnd, pos = divmod(i, TEAMS)
        squads[pos if rnd % 2 == 0 else TEAMS - 1 - pos].append(pid)
    return squads


def run(logs: pl.DataFrame, values: pl.DataFrame) -> Result:
    value = dict(zip(values["nba_player_id"].to_list(), values["value"].to_list(), strict=True))
    elig = {
        pid: eligibility(pos)
        for pid, pos in zip(
            values["nba_player_id"].to_list(), values["nba_position"].to_list(), strict=True
        )
    }
    played = logs.group_by("GAME_DATE").agg(pl.col("PLAYER_ID").cast(pl.Int64).alias("ids"))
    stat_cols = [c for c in STATS if c in logs.columns]
    lines = {
        (d, int(p)): row
        for d, p, *row in logs.select("GAME_DATE", "PLAYER_ID", *stat_cols).iter_rows()
    }
    squads = rosters(values)
    n = more = more_value = worse = illegal = 0
    extra: list[int] = []
    slowest = 0.0
    totals = [dict.fromkeys(stat_cols, 0.0) | {"starts": 0.0} for _ in squads]
    for day, day_ids in zip(played["GAME_DATE"].to_list(), played["ids"].to_list(), strict=True):
        plays = set(day_ids)
        for t, squad in enumerate(squads):
            cands = [lu.Candidate(p, value.get(p, 0.0), elig.get(p, ()), p in plays) for p in squad]
            t0 = time.perf_counter()
            best = lu.optimise(cands, SLOTS)
            slowest = max(slowest, time.perf_counter() - t0)
            greedy = lu.greedy(cands, SLOTS)
            n += 1
            illegal += int(not lu.legal(best, cands, SLOTS))
            for pid in best:
                row = lines.get((day, pid))
                if row is not None:
                    totals[t]["starts"] += 1
                    for c, v in zip(stat_cols, row, strict=True):
                        totals[t][c] += float(v)
            b, g = lu.score(best, cands), lu.score(greedy, cands)
            if b[0] > g[0]:
                more += 1
                extra.append(b[0] - g[0])
            elif b[0] == g[0] and b[1] > g[1] + 1e-9:
                more_value += 1
            elif b < g:
                worse += 1
    mean_extra = sum(extra) / len(extra) if extra else 0.0
    ships = worse == 0 and illegal == 0 and slowest < 1.0
    standings = _standings(totals) if stat_cols else None
    return Result(n, more, more_value, worse, illegal, slowest, mean_extra, ships, standings)


def _standings(totals: list[dict[str, float]]) -> pl.DataFrame:
    """Rotisserie-style table: each roster's season totals from its started players, ranked per
    category (16 = best), summed. Turnovers: fewer is better."""
    df = (
        pl.DataFrame(totals)
        .with_row_index("roster", offset=1)
        .with_columns(
            (pl.col("FGM") / pl.col("FGA")).alias("FG%"),
            (pl.col("FTM") / pl.col("FTA")).alias("FT%"),
        )
    )
    cats = ["PTS", "REB", "AST", "STL", "BLK", "FG3M", "FG%", "FT%"]
    ranks = [pl.col(c).rank("average").alias(f"r_{c}") for c in cats]
    ranks.append(pl.col("TOV").rank("average", descending=True).alias("r_TOV"))
    df = df.with_columns(ranks)
    rank_cols = [c for c in df.columns if c.startswith("r_")]
    return df.with_columns(pl.sum_horizontal(rank_cols).alias("roto_points")).sort(
        "roto_points", descending=True
    )
