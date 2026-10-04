"""`/today`, `/matchup`, `/waivers`: views over the published brief snapshot (D-62).

Every number comes from the snapshot the daily job computed; text is assembled from its fields.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends, Request

from fantasy_api.auth import current_user
from fantasy_api.errors import ApiProblem
from fantasy_api.schemas import (
    Action,
    CategoryProjection,
    Freshness,
    Matchup,
    Source,
    Today,
    WaiverCandidate,
    Waivers,
)
from fantasy_api.system import store_of
from fantasy_decision import explain as ex
from fantasy_decision.brief import BENCH, LABELS, RATIOS

SUPPORTED_SCHEMA = 1
router = APIRouter(tags=["views"], dependencies=[Depends(current_user)])


def _snapshot(request: Request, day: date | None) -> dict[str, Any]:
    snap = store_of(request).brief_snapshot(day)
    if snap is None:
        raise ApiProblem(404, "no-brief", "No brief published", f"day={day or 'latest'}")
    if snap.get("schema") != SUPPORTED_SCHEMA:
        raise ApiProblem(
            503, "snapshot-schema", "Unsupported brief snapshot", f"schema={snap.get('schema')}"
        )
    return snap


def _freshness(snap: dict[str, Any]) -> Freshness:
    at = snap.get("generated_at")
    return Freshness(
        as_of=datetime.fromisoformat(at) if at else None,
        sources=[Source(name=s["name"], as_of=s["as_of"]) for s in snap["sources"]],
        stale_since=snap.get("stale_since"),
    )


def _fmt(cat: str, x: float) -> str:
    return f"{x:.3f}".removeprefix("0") if cat in RATIOS else f"{x:.0f}"


def _matchup(snap: dict[str, Any]) -> Matchup | None:
    outlook = snap["outlook"]
    if not outlook:
        return None
    mine, theirs = snap["totals"]["mine"], snap["totals"]["theirs"]
    day = date.fromisoformat(snap["day"])
    end = date.fromisoformat(snap["week"]["end"])
    return Matchup(
        week_start=date.fromisoformat(snap["week"]["start"]),
        week_end=end,
        days_left=(end - day).days + 1,
        opponent=snap["opponent_name"],
        expected_categories=round(sum(outlook.values()), 2),
        categories=[
            CategoryProjection(
                code=LABELS[c], mine=_fmt(c, mine[c]), theirs=_fmt(c, theirs[c]), win_prob=p
            )
            for c, p in outlook.items()
        ],
        freshness=_freshness(snap),
    )


def explained_actions(snap: dict[str, Any]) -> list[tuple[str, str, list[ex.Explanation]]]:
    """(kind, id, [title, detail, *why]) per action, every text filled only from the snapshot."""
    bench = [s for s in snap["lineup"] if s["slot"] == BENCH]
    lineup = [
        ex.render("Lineup: {active} active today", active=len(snap["lineup"]) - len(bench)),
        ex.render(
            "{benched}",
            benched=", ".join(f"{s['name']} to the bench" for s in bench)
            or "Everyone with a game starts",
        ),
        *[ex.render("{name}: {reason}", name=s["name"], reason=s["reason"]) for s in bench],
    ]
    out = [("lineup", "lineup-0", lineup)]
    out += [
        (
            "injury",
            f"injury-{i}",
            [ex.render("{name}: {status}", name=x["name"], status=x["status"]), ex.render("")],
        )
        for i, x in enumerate(snap["injuries"])
    ]
    if snap["pickups"]:
        p = snap["pickups"][0]
        texts = [
            ex.render("Add {add}, drop {drop}", add=p["add_name"], drop=p["drop_name"]),
            ex.render("{games} games left this week", games=p["games_left"]),
            ex.render("{gain:+.2f} expected categories this week", gain=p["gain"]),
            ex.render("{games} games left", games=p["games_left"]),
        ]
        if p["helps"]:
            texts.append(ex.render("Helps {cats}", cats=", ".join(LABELS[h] for h in p["helps"])))
        out.append(("stream", "stream-0", texts))
    return out


def _actions(snap: dict[str, Any]) -> list[Action]:
    return [
        Action(
            id=aid,
            kind=kind,  # type: ignore[arg-type]  # one of the Action kinds by construction
            title=texts[0].text,
            detail=texts[1].text,
            why=[e.text for e in texts[2:]],
        )
        for kind, aid, texts in explained_actions(snap)
    ]


@router.get("/today")
def today(request: Request, day: date | None = None) -> Today:
    snap = _snapshot(request, day)
    return Today(
        date=date.fromisoformat(snap["day"]),
        matchup=_matchup(snap),
        actions=_actions(snap),
        freshness=_freshness(snap),
    )


@router.get("/matchup")
def matchup(request: Request, day: date | None = None) -> Matchup:
    m = _matchup(_snapshot(request, day))
    if m is None:
        raise ApiProblem(404, "no-matchup", "No opponent this week")
    return m


@router.get("/waivers")
def waivers(request: Request, day: date | None = None) -> Waivers:
    snap = _snapshot(request, day)
    picks = snap["pickups"]
    return Waivers(
        candidates=[
            WaiverCandidate(
                id=str(p["add_id"]),
                name=p["add_name"],
                games_left=p["games_left"],
                helps=[LABELS[h] for h in p["helps"]],
                gain=p["gain"],
            )
            for p in picks
        ],
        suggested_drop=picks[0]["drop_name"] if picks else None,
        horizon=snap.get("horizon", "this week"),
        freshness=_freshness(snap),
    )
