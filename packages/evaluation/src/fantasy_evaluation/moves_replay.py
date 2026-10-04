"""DEC-008: replay weekly add/drop decisions on the 2025-26 holdout (pre-registered).

Each team-week, from fixed drafted rosters, a method proposes at most one move on Monday using only
what was known then (the in-season blend of the leak-free prior, expected games from the team's
schedule x the player's share of team games so far). The move is scored on what actually
happened: categories won against that week's opponent with the added player's actual stats in
place of the dropped player's, minus without the move, plus 0.5 x the same for next week.

- Method A: `brief.pickups` (normal approximation, this week, lowest-value drop).
- Method B: `moves.best_moves` (simulation with common random numbers, this week + d x next week;
  d = 0.5 decides, 0.3 and 0.7 are sensitivity).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from dikit.methods import shrinkage
from fantasy_decision import brief
from fantasy_decision import moves as mv
from fantasy_evaluation.distribution_backtest import HOLDOUT_START
from fantasy_models import inseason

RAW = ("PTS", "REB", "AST", "STL", "BLK", "FG3M", "TOV", "FGM", "FGA", "FTM", "FTA")
STATS = tuple(s.lower() for s in RAW)
COUNT_IDX = range(7)
TOV = 6
REALISED_WEIGHT = 0.5  # U13: next week counts half in the realised outcome
DECISION = 0.5
SENSITIVITY = (0.3, 0.7)


@dataclass(frozen=True)
class Week:
    proj: dict[int, mv.PlayerWeek]  # as of Monday
    actual: dict[int, np.ndarray]  # the week's actual totals, RAW order


@dataclass(frozen=True)
class Result:
    rows: pl.DataFrame  # one per team-week: week, team, gain_<method>, moved_<method>
    summary: pl.DataFrame  # per method: mean realised gain, CI, share of team-weeks with a move
    b_minus_a: tuple[float, float, float]  # mean, CI low, CI high
    ships: bool


def monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def weeks_of(logs: pl.DataFrame) -> list[date]:
    """Holdout Mondays whose following week also has games."""
    days = {date.fromisoformat(str(d)) for d in logs["GAME_DATE"].unique().to_list()}
    mondays = {monday(d) for d in days}
    return sorted(m for m in mondays if m >= HOLDOUT_START and m + timedelta(days=7) in mondays)


def week_inputs(logs: pl.DataFrame, priors: pl.DataFrame, start: date) -> Week:
    """`logs`: PLAYER_ID, TEAM_ID, GAME_DATE and RAW; `priors`: PLAYER_ID and per-game STATS."""
    g = logs.with_columns(pl.col("GAME_DATE").cast(pl.Utf8).str.to_date().alias("day"))
    end = start + timedelta(days=7)
    before = g.filter(pl.col("day") < start)
    during = g.filter((pl.col("day") >= start) & (pl.col("day") < end))
    team_games_week = dict(
        during.select("TEAM_ID", "day").unique().group_by("TEAM_ID").len().iter_rows()
    )
    team_games_so_far = dict(
        before.select("TEAM_ID", "day").unique().group_by("TEAM_ID").len().iter_rows()
    )
    so_far = (
        before.sort("day")
        .group_by("PLAYER_ID")
        .agg(
            pl.len().alias("n"),
            pl.col("TEAM_ID").last().alias("team"),
            *[pl.col(r).sum() for r in RAW],
        )
    )
    rows = priors.join(so_far, on="PLAYER_ID", how="left").fill_null(0)
    proj = {}
    for r in rows.iter_rows(named=True):
        n = float(r["n"])
        per_game = {
            s: float(
                shrinkage.blend(
                    np.array([r[s]]), np.array([r[raw]]), np.array([n]), inseason.K_SHIPPED[s]
                )[0]
            )
            for s, raw in zip(STATS, RAW, strict=True)
        }
        team = r["team"]
        share = (
            min(n / team_games_so_far[team], 1.0) if team and team_games_so_far.get(team) else 0.0
        )
        proj[int(r["PLAYER_ID"])] = mv.PlayerWeek(per_game, team_games_week.get(team, 0) * share)
    actual = {
        int(r[0]): np.asarray(r[1:], dtype=float)
        for r in during.group_by("PLAYER_ID")
        .agg(*[pl.col(c).sum() for c in RAW])
        .select("PLAYER_ID", *RAW)
        .iter_rows()
    }
    return Week(proj, actual)


def categories(mine: np.ndarray, theirs: np.ndarray) -> float:
    """Categories won (ties 0.5) from two teams' RAW totals."""
    won = 0.0
    for k in COUNT_IDX:
        a, b = (theirs[k], mine[k]) if k == TOV else (mine[k], theirs[k])
        won += float(a > b) + 0.5 * float(a == b)
    for m, a_ in ((7, 8), (9, 10)):
        pa = mine[m] / mine[a_] if mine[a_] else 0.0
        pb = theirs[m] / theirs[a_] if theirs[a_] else 0.0
        won += float(pa > pb) + 0.5 * float(pa == pb)
    return won


def _total(ids: Sequence[int], actual: Mapping[int, np.ndarray]) -> np.ndarray:
    return sum((actual.get(p, np.zeros(len(RAW))) for p in ids), np.zeros(len(RAW)))


def realised(  # noqa: PLR0913, PLR0917 - a move scored on two weeks
    move: tuple[int, int] | None,
    mine: Sequence[int],
    opp: Sequence[int],
    opp_next: Sequence[int],
    now: Mapping[int, np.ndarray],
    nxt: Mapping[int, np.ndarray],
) -> float:
    if move is None:
        return 0.0
    add, drop = move
    new = [add if p == drop else p for p in mine]
    gain = 0.0
    for week, their, w in ((now, opp, 1.0), (nxt, opp_next, REALISED_WEIGHT)):
        t = _total(their, week)
        gain += w * (categories(_total(new, week), t) - categories(_total(mine, week), t))
    return gain


def _brief_frame(proj: Mapping[int, mv.PlayerWeek]) -> pl.DataFrame:
    ids = list(proj)
    return pl.DataFrame(
        {
            "nba_player_id": ids,
            "player_name": [str(p) for p in ids],
            "exp_games": [proj[p].games for p in ids],
            "games_left": [proj[p].games for p in ids],
            **{s: [proj[p].per_game[s] * proj[p].games for p in ids] for s in STATS},
        }
    )


def method_a(
    week: Week,
    mine: Sequence[int],
    opp: Sequence[int],
    rostered: set[int],
    value: Mapping[int, float],
) -> tuple[int, int] | None:
    frame = _brief_frame({p: w for p, w in week.proj.items() if p in rostered or w.games > 0})
    picks = brief.pickups(frame, mine, opp, rostered=rostered, value=value, n=1)
    return (picks[0].add_id, picks[0].drop_id) if picks and picks[0].gain > 0 else None


def schedule(teams: int, weeks: int, seed: int) -> list[np.ndarray]:
    """A fixed random opponent per team per week: opp[w][t]."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(weeks):
        order = rng.permutation(teams)
        opp = np.empty(teams, dtype=int)
        opp[order[0::2]], opp[order[1::2]] = order[1::2], order[0::2]
        out.append(opp)
    return out


def run(  # noqa: PLR0913 - the replay's inputs and knobs
    squads: Sequence[Sequence[int]],
    weeks: Mapping[date, Week],
    value: Mapping[int, float],
    *,
    draws: int = 1000,
    n_boot: int = 2000,
    seed: int = 0,
) -> Result:
    mondays = sorted(weeks)
    decided = [m for m in mondays if m + timedelta(days=7) in weeks]
    opps = schedule(len(squads), len(mondays), seed)
    rostered = {p for s in squads for p in s}
    methods = {"A": None, **{f"B{d}": d for d in (DECISION, *SENSITIVITY)}}
    rows = []
    for m in decided:
        i = mondays.index(m)
        now, nxt = weeks[m], weeks[m + timedelta(days=7)]
        fas = [p for p, w in now.proj.items() if p not in rostered and p in value]
        for t, mine in enumerate(squads):
            opp, opp_next = squads[opps[i][t]], squads[opps[i + 1][t]]
            row: dict[str, object] = {"week": m, "team": t}
            for name, d in methods.items():
                if d is None:
                    move = method_a(now, mine, opp, rostered, value)
                else:
                    best = mv.best_moves(
                        mine,
                        opp,
                        opp_next,
                        fas,
                        now.proj,
                        nxt.proj,
                        value=value,
                        discount=d,
                        draws=draws,
                        seed=m.toordinal() * 100 + t,
                    )
                    move = (best[0].add, best[0].drop) if best else None
                row[f"gain_{name}"] = realised(move, mine, opp, opp_next, now.actual, nxt.actual)
                row[f"moved_{name}"] = move is not None
            rows.append(row)
    df = pl.DataFrame(rows)
    rng = np.random.default_rng(seed)
    wk = np.array([w.toordinal() for w in df["week"].to_list()])
    summary = []
    for name in methods:
        g = df[f"gain_{name}"].to_numpy()
        lo, hi = bs.clustered_mean_ci(g, wk, n_boot, rng)
        summary.append(
            {
                "method": name,
                "mean_gain": float(g.mean()),
                "ci_lo": lo,
                "ci_hi": hi,
                "move_share": float(df[f"moved_{name}"].to_numpy().mean()),
            }
        )
    diff = (df[f"gain_B{DECISION}"] - df["gain_A"]).to_numpy()
    lo, hi = bs.clustered_mean_ci(diff, wk, n_boot, rng)
    return Result(df, pl.DataFrame(summary), (float(diff.mean()), lo, hi), lo > 0)
