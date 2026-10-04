"""`/replay`: the season replay files the pipeline publishes (SIM-001; G-31 A: browser simulates).

Read-only and signed-in like the other views. A season's file never changes once published, so it is
served as stored, with a long private cache.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from fantasy_api.auth import current_user
from fantasy_api.errors import ApiProblem
from fantasy_api.schemas import ApiModel
from fantasy_api.system import store_of

SEASONS = ("2023-24", "2024-25", "2025-26")  # G-31 Q5 A (mirrors the pipeline's season_replay)
CACHE = "private, max-age=86400"

router = APIRouter(tags=["replay"], dependencies=[Depends(current_user)])


class ReplaySeasons(ApiModel):
    seasons: list[str]


def _path(season: str) -> str:
    return f"replay/{season}.json"


@router.get("/replay/seasons")
def replay_seasons(request: Request) -> ReplaySeasons:
    store = store_of(request)
    return ReplaySeasons(seasons=[s for s in SEASONS if store.exists(_path(s))])


@router.get(
    "/replay/{season}",
    responses={200: {"content": {"application/json": {}}, "description": "The season document"}},
)
def replay_season(season: str, request: Request) -> Response:
    store = store_of(request)
    if season not in SEASONS or not store.exists(_path(season)):
        raise ApiProblem(404, "no-replay", "No replay for this season", f"season={season}")
    body = store.read_bytes(_path(season))
    return Response(body, media_type="application/json", headers={"Cache-Control": CACHE})
