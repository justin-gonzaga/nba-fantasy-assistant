"""`/me/settings`, `/me/telegram/link`, `/me/export`, `DELETE /me`, the Telegram webhook (APP-009).

Only `/me/...` routes: the acting user is always the verified token's uid, so no request can name
another user. The webhook is Telegram's call, authenticated by the secret token Telegram echoes in
`X-Telegram-Bot-Api-Secret-Token` (set with `setWebhook`, G-30 A); it answers `/start <code>` inline
(a `sendMessage` in the response body), so the API needs no outbound call to Telegram.
"""

from __future__ import annotations

import secrets
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse

from fantasy_api import schemas
from fantasy_api.auth import RateLimiter, current_user
from fantasy_api.errors import ApiProblem
from fantasy_api.users import draft_settings_routes, sims_routes
from fantasy_api.users.etag import etag_version
from fantasy_api.users.model import User
from fantasy_api.users.settings import InvalidSettingError, Settings
from fantasy_api.users.settings_service import SettingsService, StaleSettingsError

router = APIRouter(tags=["settings"])
webhook_router = APIRouter(include_in_schema=False)
Me = Annotated[User, Depends(current_user)]
SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"  # noqa: S105 - a header name


def settings_of(request: Request) -> SettingsService:
    service: SettingsService = request.app.state.settings
    return service


Service = Annotated[SettingsService, Depends(settings_of)]


def etag(s: Settings) -> str:
    return f'"settings-v{s.version}"'


def to_schema(s: Settings) -> schemas.UserSettings:
    return schemas.UserSettings(
        time_zone=s.time_zone,
        brief_enabled=s.brief_enabled,
        awake_start=s.awake_start,
        awake_end=s.awake_end,
        alerts=list(s.alerts),
        draft_strategy=s.draft_strategy,
        theme=s.theme,
        display_name=s.display_name,
        telegram_linked=s.telegram_chat_id is not None,
        version=s.version,
    )


@router.get("/me/settings")
def get_settings(user: Me, service: Service, response: Response) -> schemas.UserSettings:
    s = service.get(user.uid)
    response.headers["ETag"] = etag(s)
    response.headers["Cache-Control"] = "no-store"
    return to_schema(s)


@router.patch(
    "/me/settings",
    responses={
        412: {"description": "Changed elsewhere: the body's `current` is the stored document"},
        428: {"description": "If-Match is required"},
    },
)
def patch_settings(
    user: Me,
    service: Service,
    body: schemas.SettingsPatch,
    response: Response,
    if_match: Annotated[str | None, Header()] = None,
) -> schemas.UserSettings:
    if if_match is None:
        raise ApiProblem(
            428,
            "precondition-required",
            "Send If-Match with the ETag from GET /me/settings",
        )
    changes = body.model_dump(exclude_unset=True)
    expected = etag_version(if_match, "settings-v")
    try:
        updated = service.update(user.uid, -1 if expected is None else expected, changes)
    except InvalidSettingError as e:
        raise ApiProblem(
            422, "invalid-setting", f"Invalid {e.field}", str(e), extra={"field": e.field}
        ) from None
    except StaleSettingsError as e:
        raise ApiProblem(
            412,
            "stale-settings",
            "These settings changed elsewhere",
            "Review the current values and save again.",
            headers={"ETag": etag(e.current)},
            extra={"current": to_schema(e.current).model_dump(mode="json", by_alias=True)},
        ) from None
    response.headers["ETag"] = etag(updated)
    return to_schema(updated)


@router.post("/me/telegram/link", status_code=status.HTTP_201_CREATED)
def telegram_link(user: Me, service: Service) -> schemas.TelegramLink:
    code = service.new_link_code(user.uid)
    return schemas.TelegramLink(
        code=code.code,
        expires_at=code.expires_at,
        instructions=f"Send /start {code.code} to the bot within 10 minutes.",
    )


@router.get("/me/export")
def export(user: Me, service: Service) -> schemas.AccountExport:
    profile = schemas.Member(
        uid=user.uid,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        created_at=user.created_at,
        last_seen_at=user.last_seen_at,
    )
    sims = sorted(service.store.list_sims(user.uid), key=lambda x: (x.created_at, x.id))
    return schemas.AccountExport(
        profile=profile,
        settings=to_schema(service.get(user.uid)),
        draft_settings=draft_settings_routes.to_schema(service.get_draft(user.uid)),
        sims=[sims_routes.to_full(x) for x in sims],
    )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={409: {"description": "The last owner can't delete their account"}},
)
def delete_me(user: Me, service: Service) -> None:
    service.delete_me(user.uid)


LINK_REPLIES = {
    "linked": "Linked: your briefs and alerts will arrive here.",
    "busy": "Your settings were changing at the same moment. Get a new code and retry.",
    "invalid": "That code is invalid, used or expired. Get a new one in the app's Settings.",
}


def _reply(chat_id: Any, text: str) -> JSONResponse:
    return JSONResponse({"method": "sendMessage", "chat_id": chat_id, "text": text})


@webhook_router.post("/telegram/webhook")
def telegram_webhook(
    request: Request,
    service: Service,
    update: Annotated[dict[str, Any], Body()],
    secret: Annotated[str | None, Header(alias=SECRET_HEADER)] = None,
) -> JSONResponse:
    expected: str | None = request.app.state.telegram_secret
    if expected is None:
        raise ApiProblem(404, "not-found", "Not found")
    if secret is None or not secrets.compare_digest(secret.encode(), expected.encode()):
        raise ApiProblem(401, "unauthenticated", "Bad webhook secret")
    limiter: RateLimiter = request.app.state.webhook_limiter
    if not limiter.allow("telegram"):
        raise ApiProblem(429, "rate-limited", "Too many updates")
    message = update.get("message")
    if not isinstance(message, dict):
        return JSONResponse({})  # edits, joins, callbacks: acknowledged, ignored
    chat = message.get("chat")
    text = message.get("text")
    if not isinstance(chat, dict) or "id" not in chat or not isinstance(text, str):
        return JSONResponse({})
    parts = text.split()
    if not parts or parts[0].split("@")[0] != "/start":
        return JSONResponse({})
    if len(parts) < 2:  # noqa: PLR2004 - "/start" and its code
        return _reply(chat["id"], "Open Settings in the app and tap Link Telegram for a code.")
    return _reply(chat["id"], LINK_REPLIES[service.link_telegram(parts[1], str(chat["id"]))])
