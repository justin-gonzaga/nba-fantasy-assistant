"""`/me/sims`: a signed-in user's saved practice drafts and replay leagues (SIM-005).

Only `/me/...`: the uid is the token's, so another user's sim answers 404 (never 403: that would
reveal it exists).
Retention rules live in `sims.py`; the store applies each plan atomically.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, Request, Response, status

from dikit.time.clock import Clock
from fantasy_api import schemas
from fantasy_api.auth import current_user
from fantasy_api.errors import ApiProblem
from fantasy_api.users.model import User
from fantasy_api.users.sims import (
    MAX_DETAIL_BYTES,
    MAX_SUMMARY_BYTES,
    SEASON,
    SIM_ID,
    Plan,
    Sim,
    SimRuleError,
    plan_pin,
    plan_save,
)
from fantasy_api.users.store import UserStore

router = APIRouter(tags=["sims"])
Me = Annotated[User, Depends(current_user)]


def store_of(request: Request) -> UserStore:
    store: UserStore = request.app.state.users.store
    return store


Store = Annotated[UserStore, Depends(store_of)]


def clock_of(request: Request) -> Clock:
    clock: Clock = request.app.state.users.clock
    return clock


Now = Annotated[Clock, Depends(clock_of)]


def _size(value: object) -> int:
    return len(json.dumps(value, separators=(",", ":")).encode())


def _invalid(field: str, message: str) -> ApiProblem:
    return ApiProblem(422, "invalid-sim", f"Invalid {field}", message, extra={"field": field})


def _check(
    sim_id: str, season: str, title: str, summary: dict[str, Any], detail: dict[str, Any]
) -> None:
    if not SIM_ID.match(sim_id):
        raise _invalid("id", "1-80 letters, digits or : _ . -")
    if not SEASON.match(season):
        raise _invalid("season", "like 2024-25")
    if not 1 <= len(title) <= 80:  # noqa: PLR2004 - a short label
        raise _invalid("title", "1 to 80 characters")
    if _size(summary) > MAX_SUMMARY_BYTES:
        raise _invalid("summary", f"at most {MAX_SUMMARY_BYTES // 1024} KB")
    if _size(detail) > MAX_DETAIL_BYTES:
        raise ApiProblem(
            413,
            "too-large",
            "This sim is too large to save",
            f"at most {MAX_DETAIL_BYTES // 1024} KB",
        )


def etag(s: Sim) -> str:
    return f'"sim-v{s.version}"'


def to_summary(s: Sim) -> schemas.SimSummary:
    return schemas.SimSummary(
        id=s.id,
        kind=s.kind,
        season=s.season,
        title=s.title,
        summary=s.summary,
        pinned=s.pinned,
        has_detail=s.detail is not None,
        created_at=s.created_at,
        updated_at=s.updated_at,
        version=s.version,
    )


def to_full(s: Sim) -> schemas.SimFull:
    return schemas.SimFull(**to_summary(s).model_dump(), detail=s.detail)


def _rule(e: SimRuleError) -> ApiProblem:
    return ApiProblem(409, e.kind, str(e))


@router.get("/me/sims")
def list_sims(
    user: Me,
    store: Store,
    kind: Literal["practice", "league"] | None = None,
    season: str | None = None,
) -> list[schemas.SimSummary]:
    sims = [
        s
        for s in store.list_sims(user.uid)
        if (kind is None or s.kind == kind) and (season is None or s.season == season)
    ]
    sims.sort(key=lambda s: (s.created_at, s.id), reverse=True)
    return [to_summary(s) for s in sims]


@router.post(
    "/me/sims",
    status_code=status.HTTP_201_CREATED,
    responses={
        200: {"description": "Already saved (same id): the stored copy"},
        409: {"description": "too-many-leagues"},
        413: {"description": "Over 256 KB"},
    },
)
def save_sim(
    user: Me, store: Store, clock: Now, body: schemas.SimIn, response: Response
) -> schemas.SimFull:
    _check(body.id, body.season, body.title, body.summary, body.detail)
    now = clock.now()
    new = Sim(
        id=body.id,
        kind=body.kind,
        season=body.season,
        title=body.title,
        summary=body.summary,
        detail=body.detail,
        pinned=False,
        created_at=now,
        updated_at=now,
    )
    try:
        stored = store.mutate_sims(user.uid, lambda sims: plan_save(sims, new))
    except SimRuleError as e:
        raise _rule(e) from None
    if stored is not new:
        response.status_code = status.HTTP_200_OK
    response.headers["ETag"] = etag(stored)
    return to_full(stored)


def _known_id(sim_id: str) -> None:
    """Every route checks the id's shape (defence in depth): a malformed one can't exist."""
    if not SIM_ID.match(sim_id):
        raise ApiProblem(404, "not-found", "No such sim")


def _find(store: UserStore, uid: str, sim_id: str) -> Sim:
    _known_id(sim_id)
    found = next((s for s in store.list_sims(uid) if s.id == sim_id), None)
    if found is None:
        raise ApiProblem(404, "not-found", "No such sim")
    return found


@router.get("/me/sims/{sim_id}")
def get_sim(sim_id: str, user: Me, store: Store, response: Response) -> schemas.SimFull:
    found = _find(store, user.uid, sim_id)
    response.headers["ETag"] = etag(found)
    return to_full(found)


@router.put(
    "/me/sims/{sim_id}",
    responses={
        412: {"description": "Changed elsewhere: the body's `current` is the stored copy"},
        428: {"description": "If-Match is required"},
    },
)
def update_league(  # noqa: PLR0913 - FastAPI's injected parameters
    sim_id: str,
    *,
    user: Me,
    store: Store,
    clock: Now,
    body: schemas.SimUpdate,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> schemas.SimFull:
    """A replay league as it progresses (weeks kept, roster): compare-and-set on its version."""
    _known_id(sim_id)
    if if_match is None:
        raise ApiProblem(428, "precondition-required", "Send If-Match with the sim's ETag")
    _check(sim_id, "2000-01", body.title, body.summary, body.detail)  # the season can't change
    now = clock.now()

    def decide(sims: list[Sim]) -> tuple[Plan, Sim | tuple[str, Sim | None]]:
        current = next((s for s in sims if s.id == sim_id), None)
        if current is None or current.kind != "league":
            return Plan(), ("missing", None)
        if if_match.strip().removeprefix("W/") != etag(current):
            return Plan(), ("stale", current)
        updated = replace(
            current,
            title=body.title,
            summary=body.summary,
            detail=body.detail,
            updated_at=now,
            version=current.version + 1,
        )
        return Plan(upserts=(updated,)), updated

    out = store.mutate_sims(user.uid, decide)
    if isinstance(out, tuple):
        reason, current = out
        if reason == "missing" or current is None:
            raise ApiProblem(404, "not-found", "No such replay league")
        raise ApiProblem(
            412,
            "stale-sim",
            "This league changed elsewhere",
            "Reload it and play on from there.",
            headers={"ETag": etag(current)},
            extra={"current": to_full(current).model_dump(mode="json", by_alias=True)},
        )
    response.headers["ETag"] = etag(out)
    return to_full(out)


@router.patch("/me/sims/{sim_id}/pin", responses={409: {"description": "too-many-pins"}})
def pin_sim(
    sim_id: str, user: Me, store: Store, clock: Now, body: schemas.SimPin
) -> schemas.SimSummary:
    _known_id(sim_id)
    now = clock.now()
    try:
        updated = store.mutate_sims(user.uid, lambda sims: plan_pin(sims, sim_id, body.pinned, now))
    except SimRuleError as e:
        raise _rule(e) from None
    if updated is None:
        raise ApiProblem(404, "not-found", "No such sim")
    return to_summary(updated)


@router.delete("/me/sims/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sim(sim_id: str, user: Me, store: Store) -> None:
    _known_id(sim_id)

    def decide(sims: list[Sim]) -> tuple[Plan, bool]:
        found = any(s.id == sim_id for s in sims)
        return (Plan(deletes=(sim_id,)) if found else Plan()), found

    if not store.mutate_sims(user.uid, decide):
        raise ApiProblem(404, "not-found", "No such sim")
