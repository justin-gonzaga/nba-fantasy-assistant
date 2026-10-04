"""Daily brief (MVP-003): the rest-of-week table + league file -> Telegram-ready markdown.

League file (JSON; filled from the owner's Yahoo pastes after the draft; data/ is git-ignored):
    {"my_team": [ids or names], "opponent_name": "Team 7", "opponent": [ids or names],
     "opponent_next": [next week's opponent, optional],
     "rostered": [every rostered id or name in the league]}
With next week's opponent and table, pickups use DEC-008's method (this week + half of next);
otherwise the this-week rule.
`sample_league` builds a snake-draft stand-in for dry runs before the real draft.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import date, datetime
from pathlib import Path
from typing import Any

import polars as pl

from dikit.errors import ContractViolation
from fantasy_decision import brief, moves
from fantasy_decision import explain as ex
from fantasy_models.valuation import eligibility
from fantasy_models.weekly import name_key
from fantasy_pipeline import workspace
from fantasy_pipeline.week_projection import default_week

# Relative to the workspace root (INFRA-006): a local folder or the serve bucket.
WEEK = "predictions/week_projection.parquet"
VALUES = "predictions/auction_values.parquet"
LEAGUE = "league/league.json"
BRIEFS = "briefs"


@dataclass(frozen=True)
class League:
    my_team: list[int]
    opponent_name: str | None
    opponent: list[int] | None
    rostered: set[int]
    opponent_next: list[int] | None = None


def _resolve(entries: list[Any], week: pl.DataFrame) -> list[int]:
    by_key = {
        name_key(n): i for i, n in zip(week["nba_player_id"], week["player_name"], strict=True)
    }
    ids, missing = [], []
    for e in entries:
        if isinstance(e, int):
            ids.append(e)
        elif name_key(str(e)) in by_key:
            ids.append(by_key[name_key(str(e))])
        else:
            missing.append(str(e))
    if missing:
        msg = f"league file names not found among NBA players: {missing}"
        raise ContractViolation(msg)
    return ids


def load_league(path: Path, week: pl.DataFrame) -> League:
    return league_from_text(path.read_text(encoding="utf-8"), week)


def league_from_text(text: str, week: pl.DataFrame) -> League:
    doc = json.loads(text)
    mine = _resolve(doc["my_team"], week)
    opp = _resolve(doc["opponent"], week) if doc.get("opponent") else None
    nxt = _resolve(doc["opponent_next"], week) if doc.get("opponent_next") else None
    rostered = set(_resolve(doc.get("rostered", []), week)) | set(mine) | set(opp or [])
    return League(mine, doc.get("opponent_name"), opp, rostered | set(nxt or []), nxt)


def sample_league(
    values: pl.DataFrame, *, teams: int = 16, rounds: int = 14, me: int = 0, opp: int = 6
) -> dict[str, Any]:
    """Snake draft by value: a stand-in league for dry runs (clearly not the real one)."""
    opp = min(opp, teams - 1)
    order = values.sort("value", descending=True)["nba_player_id"].to_list()[: teams * rounds]
    squads: list[list[int]] = [[] for _ in range(teams)]
    for i, pid in enumerate(order):
        rnd, pos = divmod(i, teams)
        squads[pos if rnd % 2 == 0 else teams - 1 - pos].append(pid)
    return {
        "my_team": squads[me],
        "opponent_name": f"Team {opp + 1} (sample)",
        "opponent": squads[opp],
        "rostered": order,
    }


TWO_WEEK = "this week + half of next"
SNAPSHOT_SCHEMA = 1  # bump when the snapshot's shape changes (the API reads it; D-62)


@dataclass(frozen=True)
class Composed:
    markdown: str  # the Telegram text
    snapshot: dict[str, Any]  # the same brief as structured data, published for the API


def compose(  # noqa: PLR0913, PLR0917 - the brief's inputs
    week: pl.DataFrame,
    values: pl.DataFrame,
    league: League,
    slots: dict[str, int],
    day: date,
    next_week: pl.DataFrame | None = None,
) -> Composed:
    as_of = week["as_of_day"][0] if "as_of_day" in week.columns else None
    if as_of is not None and as_of != day:
        msg = f"the week table is for {as_of}, not {day}: run `week-projection` first"
        raise ContractViolation(msg)
    v = values.filter(pl.col("variant") == "all")
    value = dict(zip(v["nba_player_id"].to_list(), v["value"].to_list(), strict=True))
    positions = {
        pid: eligibility(pos)
        for pid, pos in zip(v["nba_player_id"].to_list(), v["nba_position"].to_list(), strict=True)
    }
    active = {k: n for k, n in slots.items() if k not in {"BN", "IL"}}
    b = brief.build(
        week,
        league.my_team,
        league.opponent,
        rostered=league.rostered,
        positions=positions,
        value=value,
        slots=active,
    )
    if next_week is not None and league.opponent and league.opponent_next:
        picks = moves.pickups(
            week,
            next_week,
            league.my_team,
            league.opponent,
            league.opponent_next,
            rostered=league.rostered,
            value=value,
            seed=day.toordinal(),
        )
        b = replace(b, pickups=picks, horizon=TWO_WEEK)
    md = brief.render(b, day=f"{day:%a %d %b}", opponent=league.opponent_name)
    stale = stale_since(week)
    if stale is not None:  # INFRA-007: the PC's NBA fetch didn't run; say so before anything else
        warning = ex.render(
            "⚠️ Stats are missing games since {since}: the morning NBA download didn't run.",
            since=f"{stale:%a %d %b}",
        )
        md = f"{warning.text}\n\n{md}"
    return Composed(md, snapshot(b, week, league, day, as_of))


def snapshot(
    b: brief.Brief, week: pl.DataFrame, league: League, day: date, as_of: date | None
) -> dict[str, Any]:
    """The brief as JSON-ready data: only numbers the engine computed (explanations standard)."""
    bounds = default_week(day)

    def means(ids: list[int] | None) -> dict[str, float] | None:
        return {c: m for c, (m, _) in brief.team_totals(week, ids).items()} if ids else None

    return {
        "schema": SNAPSHOT_SCHEMA,
        "day": day.isoformat(),
        "week": {"start": bounds.start.isoformat(), "end": bounds.end.isoformat()},
        "opponent_name": league.opponent_name,
        "outlook": b.outlook,
        "totals": {"mine": means(league.my_team), "theirs": means(league.opponent)},
        "lineup": [
            {"player_id": s.player_id, "name": s.name, "slot": s.slot, "reason": s.reason}
            for s in b.lineup
        ],
        "injuries": [{"name": n, "status": st} for n, st in b.injuries],
        "pickups": [
            {
                "add_id": p.add_id,
                "add_name": p.add_name,
                "drop_id": p.drop_id,
                "drop_name": p.drop_name,
                "games_left": p.games_left,
                "gain": p.gain,
                "helps": p.helps,
            }
            for p in b.pickups
        ],
        "horizon": b.horizon,
        "stale_since": (s.isoformat() if (s := stale_since(week)) else None),
        "sources": [{"name": "week projection", "as_of": as_of.isoformat() if as_of else None}],
    }


def run(
    week: pl.DataFrame, values: pl.DataFrame, league: League, slots: dict[str, int], day: date
) -> str:
    return compose(week, values, league, slots, day).markdown


def stale_since(week: pl.DataFrame) -> date | None:
    """The first game missing from the stats behind this week table (INFRA-007), if any."""
    if "stale_since" not in week.columns or week.height == 0:
        return None
    value = week["stale_since"][0]
    return value if isinstance(value, date) else None


def brief_path(day: date, ext: str) -> str:
    return f"{BRIEFS}/{day.isoformat()}.{ext}"


def publish(
    out: Composed, day: date, generated_at: datetime, w: workspace.Workspace | None = None
) -> None:
    """Write the brief as markdown (Telegram) and as the JSON snapshot the API serves (D-62)."""
    w = w or workspace.get()
    w.write_text(brief_path(day, "md"), out.markdown)
    snap = {**out.snapshot, "generated_at": generated_at.isoformat()}
    w.write_text(brief_path(day, "json"), json.dumps(snap, indent=1))


def next_week_table(w: workspace.Workspace | None = None) -> pl.DataFrame | None:
    """Next week's projection table if the week-projection job wrote one (DEC-010)."""
    from fantasy_pipeline.week_projection import NEXT_OUT  # noqa: PLC0415 - avoid an import cycle

    w = w or workspace.get()
    return w.read_parquet(NEXT_OUT) if w.exists(NEXT_OUT) else None
