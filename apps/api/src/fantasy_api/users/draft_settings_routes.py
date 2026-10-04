"""`/me/draft-settings` (APP-011): the signed-in user's draft presets, one versioned document.

Only a `/me/...` route: the acting user is the verified token's uid. The body is read with a hard
16 KB cap and validated by hand so each problem names its field path (`presets[2].league.teams`).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response

from fantasy_api import schemas
from fantasy_api.auth import current_user
from fantasy_api.errors import ApiProblem
from fantasy_api.users.draft_settings import MAX_BODY_BYTES, DraftDoc, DraftSettingsError
from fantasy_api.users.etag import etag_version
from fantasy_api.users.model import User
from fantasy_api.users.settings_service import SettingsService, StaleDraftSettingsError

router = APIRouter(tags=["settings"])
Me = Annotated[User, Depends(current_user)]
PREFIX = "draft-v"


def _service(request: Request) -> SettingsService:
    service: SettingsService = request.app.state.settings
    return service


Service = Annotated[SettingsService, Depends(_service)]


def etag(doc: DraftDoc) -> str:
    return f'"{PREFIX}{doc.version}"'


def to_schema(doc: DraftDoc) -> schemas.DraftSettings:
    return schemas.DraftSettings.model_validate({**doc.data, "version": doc.version})


def _too_large() -> ApiProblem:
    return ApiProblem(
        413, "too-large", "Draft settings are too large", f"at most {MAX_BODY_BYTES // 1024} KB"
    )


async def capped_body(request: Request) -> bytes:
    """The request body, refused as soon as it passes the cap (declared or streamed)."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise _too_large()
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_BODY_BYTES:
            raise _too_large()
        chunks.append(chunk)
    return b"".join(chunks)


Body = Annotated[bytes, Depends(capped_body)]


@router.get("/me/draft-settings")
def get_draft_settings(user: Me, service: Service, response: Response) -> schemas.DraftSettings:
    doc = service.get_draft(user.uid)
    response.headers["ETag"] = etag(doc)
    response.headers["Cache-Control"] = "no-store"
    return to_schema(doc)


@router.put(
    "/me/draft-settings",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/DraftSettings"}}
            },
        }
    },
    responses={
        412: {"description": "Changed elsewhere: the body's `current` is the stored document"},
        413: {"description": "Over 16 KB"},
        422: {"description": "A field failed validation: `field` is its path"},
        428: {"description": "If-Match is required"},
    },
)
def put_draft_settings(
    user: Me,
    service: Service,
    raw: Body,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> schemas.DraftSettings:
    if if_match is None:
        raise ApiProblem(
            428,
            "precondition-required",
            "Send If-Match with the ETag from GET /me/draft-settings",
        )
    expected = etag_version(if_match, PREFIX)
    try:
        updated = service.update_draft(user.uid, -1 if expected is None else expected, _json(raw))
    except DraftSettingsError as e:
        raise ApiProblem(
            422, e.kind, f"Invalid {e.path or 'body'}", str(e), extra={"field": e.path}
        ) from None
    except StaleDraftSettingsError as e:
        raise ApiProblem(
            412,
            "stale-draft-settings",
            "Draft settings changed elsewhere",
            "Review the current values and save again.",
            headers={"ETag": etag(e.current)},
            extra={"current": to_schema(e.current).model_dump(mode="json", by_alias=True)},
        ) from None
    response.headers["ETag"] = etag(updated)
    return to_schema(updated)


def _json(raw: bytes) -> object:
    import json  # noqa: PLC0415

    try:
        return json.loads(raw)
    except ValueError:
        raise ApiProblem(422, "invalid-json", "The body isn't valid JSON") from None
