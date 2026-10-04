"""App factory and the `fantasy-api` entry point."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import fantasy_api
from dikit.errors import ConfigError
from dikit.time.clock import Clock, SystemClock
from fantasy_api import errors, players, replay, system, views
from fantasy_api.auth import DEFAULT_PER_MINUTE, AuthConfig, RateLimiter, firebase_verifier
from fantasy_api.store import DataStore
from fantasy_api.users import routes as user_routes
from fantasy_api.users import settings_routes, sims_routes
from fantasy_api.users.service import UserService
from fantasy_api.users.settings_service import SettingsService
from fantasy_api.users.store import InMemoryUserStore, UserStore

OPENAPI = Path(__file__).parents[2] / "openapi.json"


def create_app(  # noqa: PLR0913 - the factory's injected options, keyword-only
    data_root: str,
    auth: AuthConfig | None = None,
    *,
    cors_origins: list[str] | None = None,
    cors_origin_regex: str | None = None,
    docs: bool = True,
    users: UserStore | None = None,
    clock: Clock | None = None,
    telegram_secret: str | None = None,
) -> FastAPI:
    """`auth=None` turns sign-in off: only for local development (see `require_auth_config`).

    CORS lets the website's origins (and its PR preview channels, by regex) call the API with a
    bearer token from the browser (no cookies); `docs=False` hides /docs and /openapi.json outside
    local. `users` is the user store (Firestore when served; in-memory by default).
    `telegram_secret` turns on the Telegram webhook (absent: it answers 404)."""
    app = FastAPI(
        title="NBA Fantasy Assistant API",
        version=fantasy_api.__version__,
        description=(
            "Read-only views over the published daily outputs (D-62), plus users, roles and "
            "invites (D-64)."
        ),
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    if cors_origins or cors_origin_regex:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins or [],
            allow_origin_regex=cors_origin_regex,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Accept", "Content-Type", "If-Match"],
            expose_headers=["ETag"],
            allow_credentials=False,  # bearer tokens only: no cookies, so no CSRF surface
            max_age=600,
        )
    app.add_middleware(GZipMiddleware, minimum_size=1024)  # /players is ~250 KB of JSON
    app.state.store = DataStore(data_root)
    app.state.auth = auth
    store = users or InMemoryUserStore()
    app.state.users = UserService(store, clock or SystemClock())
    app.state.settings = SettingsService(store, clock or SystemClock())
    app.state.telegram_secret = telegram_secret
    app.state.webhook_limiter = RateLimiter(DEFAULT_PER_MINUTE)
    errors.install(app)
    app.include_router(system.router)
    app.include_router(user_routes.router)
    app.include_router(settings_routes.router)
    app.include_router(settings_routes.webhook_router)
    app.include_router(sims_routes.router)
    app.include_router(views.router)
    app.include_router(players.router)
    app.include_router(replay.router)
    return app


def require_auth_config(
    *, app_env: str, allowed_emails: str, firebase_project: str | None
) -> AuthConfig | None:
    """Auth is off only in local development without an allowlist; elsewhere it must be complete.

    The allowlist (ALLOWED_EMAILS) only bootstraps the first owner; the user store decides after."""
    emails = frozenset(e.strip().lower() for e in allowed_emails.split(",") if e.strip())
    if app_env == "local" and not emails:
        return None
    if not emails:
        msg = f"ALLOWED_EMAILS must be set when APP_ENV={app_env} (the API refuses to run open)"
        raise ConfigError(msg)
    if not firebase_project:
        msg = "FIREBASE_PROJECT (or GCP_PROJECT) must be set to verify sign-in tokens"
        raise ConfigError(msg)
    return AuthConfig(emails, firebase_verifier(firebase_project), RateLimiter(DEFAULT_PER_MINUTE))


def write_openapi() -> None:
    spec = create_app("unused").openapi()
    text = json.dumps(spec, indent=2, sort_keys=True) + "\n"
    OPENAPI.write_text(text, encoding="utf-8", newline="\n")  # LF on every OS


def user_store(
    auth: AuthConfig | None, backend: str, firestore: Callable[[], UserStore]
) -> UserStore:
    """Firestore only once it exists (the owner's apply, then USERS_BACKEND=firestore): deploying
    this code before the apply must not break sign-in, so the default is the in-memory store
    that the allowlist bootstraps on each start (the behaviour before APP-008)."""
    if auth is not None and backend == "firestore":
        return firestore()
    return InMemoryUserStore()


def _firestore(project: str) -> UserStore:  # pragma: no cover - real Firestore
    from fantasy_api.users.firestore import FirestoreUserStore  # noqa: PLC0415

    return FirestoreUserStore.for_project(project)


def serve() -> None:  # pragma: no cover - process entry point
    parser = argparse.ArgumentParser(prog="fantasy-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--write-openapi", action="store_true", help="refresh openapi.json and exit"
    )
    args = parser.parse_args()
    if args.write_openapi:
        write_openapi()
        return
    import uvicorn  # noqa: PLC0415 - only when serving

    from fantasy_core.settings import get_settings  # noqa: PLC0415

    s = get_settings()
    auth = require_auth_config(
        app_env=s.app_env,
        allowed_emails=s.allowed_emails,
        firebase_project=s.firebase_project or s.gcp_project,
    )
    store = user_store(
        auth,
        s.users_backend,
        lambda: _firestore(s.firebase_project or s.gcp_project or ""),
    )
    app = create_app(
        s.data_root,
        auth,
        cors_origins=[o.strip() for o in s.cors_origins.split(",") if o.strip()],
        cors_origin_regex=s.cors_origin_regex or None,
        docs=s.app_env == "local",
        users=store,
        telegram_secret=(
            s.telegram_webhook_secret.get_secret_value() if s.telegram_webhook_secret else None
        ),
    )
    uvicorn.run(app, host=args.host, port=args.port)
