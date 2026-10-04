"""`/players`: every projected player with the draft values (WEB-005), from the published tables.

Values come from `predictions/auction_values.parquet` (one ranking per variant: all categories or a
punt strategy), per-game projections from `predictions/preseason_projection.parquet`, and team and
today's injury status from the week table when it exists. Every number is a stored model output.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import polars as pl
from fastapi import APIRouter, Depends, Request

from fantasy_api import indicators as ind
from fantasy_api.auth import current_user
from fantasy_api.badges import BREAKOUT, HISTORY, badges_for, load_inputs
from fantasy_api.errors import ApiProblem
from fantasy_api.schemas import Freshness, PlayerProjection, PlayerRow, Players, Source
from fantasy_api.store import WEEK_PROJECTION
from fantasy_api.system import store_of

VALUES = "predictions/auction_values.parquet"
PROJECTIONS = "predictions/preseason_projection.parquet"
CONSISTENCY = "predictions/player_consistency.parquet"  # WEB-020
ROLE = "predictions/role_context.parquet"
CATS = ("fg_pct", "ft_pct", "fg3m", "pts", "reb", "ast", "stl", "blk", "tov")
COUNTS = ("games", "mpg", "pts", "reb", "ast", "stl", "blk", "fg3m", "tov")

router = APIRouter(tags=["players"], dependencies=[Depends(current_user)])


def _ratio(makes: float | None, attempts: float | None) -> float | None:
    if makes is None or not attempts:
        return None
    return round(makes / attempts, 3)


def _opt_int(x: object) -> int | None:
    return int(x) if isinstance(x, int | float) else None


def _opt_round(x: object) -> float | None:
    return round(float(x), 1) if isinstance(x, int | float) else None


def _projections(table: pl.DataFrame | None) -> dict[int, PlayerProjection]:
    if table is None:
        return {}
    latest = table.filter(pl.col("season") == table["season"].max())  # one row per player and stat
    wide = latest.pivot(on="stat", index="nba_player_id", values="mean")
    out = {}
    for r in wide.iter_rows(named=True):
        if any(r.get(c) is None for c in COUNTS):
            continue
        out[int(r["nba_player_id"])] = PlayerProjection(
            **{c: round(float(r[c]), 2) for c in COUNTS},
            fg_pct=_ratio(r.get("fgm"), r.get("fga")),
            ft_pct=_ratio(r.get("ftm"), r.get("fta")),
        )
    return out


def _context(week: pl.DataFrame | None) -> dict[int, dict[str, Any]]:
    if week is None:
        return {}
    return {
        int(r["nba_player_id"]): r
        for r in week.select("nba_player_id", "team", "status_today").iter_rows(named=True)
    }


@router.get("/players")
def players(request: Request, variant: str = "all") -> Players:
    store = store_of(request)
    values = store.read_parquet(VALUES)
    if values is None:
        raise ApiProblem(404, "no-players", "No player values published")
    variants = sorted(set(values["variant"].to_list()), key=lambda v: (v != "all", v))
    if variant not in variants:
        raise ApiProblem(422, "invalid-request", "Unknown strategy", f"variant={variant}")
    proj_table = store.read_parquet(PROJECTIONS)
    proj = _projections(proj_table)
    ctx = _context(store.read_parquet(WEEK_PROJECTION))
    chosen = values.filter(pl.col("variant") == variant).sort("overall_rank")
    history = store.read_parquet(HISTORY)
    inputs = load_inputs(chosen, history, store.read_parquet(BREAKOUT))
    signals = ind.load_inputs(values, variant, proj_table, history, store.read_parquet(CONSISTENCY))
    ind.add_role_context(signals, store.read_parquet(ROLE))
    rows = []
    for r in chosen.iter_rows(named=True):
        pid = int(r["nba_player_id"])
        c = ctx.get(pid, {})
        indicators = ind.indicators_for(pid, signals)
        rows.append(
            PlayerRow(
                id=pid,
                name=r["player_name"],
                team=c.get("team"),
                positions=r["nba_position"],
                rank=int(r["overall_rank"]),
                tier=int(r["tier"]),
                dollars=round(float(r["dollars"]), 1),
                healthy_rank=_opt_int(r.get("healthy_rank")),
                healthy_dollars=_opt_round(r.get("healthy_dollars")),
                value=round(float(r["value"]), 3),
                in_pool=bool(r["drafted"]),
                status=c.get("status_today"),
                strengths={cat: round(float(r[f"s_{cat}"]), 3) for cat in CATS},
                projection=proj.get(pid),
                badges=badges_for(pid, int(r["overall_rank"]), c.get("status_today"), inputs),
                indicators=indicators,
                signal=ind.signal(indicators),
            )
        )
    created = None
    if proj_table is not None and "created_at" in proj_table.columns:
        latest = proj_table["created_at"].max()
        created = latest if isinstance(latest, datetime) else None
    return Players(
        variant=variant,
        variants=variants,
        players=rows,
        badge_notes=[*inputs.notes, *signals.notes],
        freshness=Freshness(
            as_of=created,
            sources=[
                Source(name="draft projections", as_of=created.isoformat() if created else None)
            ],
        ),
    )
