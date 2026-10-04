"""App-level sign-in (D-27, APP-005, APP-008): a Firebase ID token on every data request, verified
on the server; then the user store decides access (D-64): an owner or a member who claimed an
invite. The env allowlist only bootstraps the first owner. Plus a per-user rate limit.

Local development may run without auth (no allowlist configured); any other environment refuses to
start without one (see `main.require_auth_config`).
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fantasy_api.errors import ApiProblem
from fantasy_api.users.model import User
from fantasy_api.users.service import Identity, UserService

Verify = Callable[[str], Mapping[str, Any]]
WINDOW_SECONDS = 60.0
DEFAULT_PER_MINUTE = 60


class InvalidToken(Exception):  # noqa: N818 - a verification outcome, answered as 401
    """The token is missing, malformed, expired or not signed for this project."""


@dataclass
class RateLimiter:
    per_minute: int
    clock: Callable[[], float] = time.monotonic
    _hits: dict[str, deque[float]] = field(default_factory=dict)

    def allow(self, key: str) -> bool:
        now = self.clock()
        hits = self._hits.setdefault(key, deque())
        while hits and now - hits[0] >= WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= self.per_minute:
            return False
        hits.append(now)
        return True


@dataclass(frozen=True)
class AuthConfig:
    bootstrap_owners: frozenset[str]  # lowercased; used only while the store has no owner
    verify: Verify
    limiter: RateLimiter


def firebase_verifier(project: str) -> Verify:  # pragma: no cover - calls Google's key endpoint
    """Check a Firebase ID token's signature, expiry, issuer and audience (the project)."""
    from google.auth import exceptions  # noqa: PLC0415 - only when auth is on
    from google.auth.transport import requests as google_requests  # noqa: PLC0415
    from google.oauth2 import id_token  # noqa: PLC0415

    transport = google_requests.Request()

    def verify(token: str) -> Mapping[str, Any]:
        try:
            claims: Mapping[str, Any] | None = id_token.verify_firebase_token(  # type: ignore[no-untyped-call]
                token, transport, audience=project
            )
        except (ValueError, exceptions.GoogleAuthError) as e:
            raise InvalidToken(str(e)) from e
        if not claims:
            raise InvalidToken("no claims")
        return claims

    return verify


_bearer = HTTPBearer(auto_error=False)


def current_user(
    request: Request, creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> User:
    """The signed-in user with access (a local owner when auth is off in local development).

    The uid comes only from the verified token; the store is read on every request."""
    auth: AuthConfig | None = request.app.state.auth
    users: UserService = request.app.state.users
    if auth is None:
        now = users.clock.now()
        return User("local", "local@localhost", "Local developer", "owner", now, now)
    challenge = {"WWW-Authenticate": "Bearer"}
    if creds is None:
        raise ApiProblem(401, "unauthenticated", "Sign-in required", headers=challenge)
    try:
        claims = auth.verify(creds.credentials)
    except InvalidToken:
        raise ApiProblem(
            401, "unauthenticated", "Invalid or expired sign-in", headers=challenge
        ) from None
    uid = str(claims.get("sub") or claims.get("user_id") or "")
    email = str(claims.get("email", "")).strip().lower()
    if not uid or not email or claims.get("email_verified") is not True:
        raise ApiProblem(403, "forbidden", "This account doesn't have access")
    if not auth.limiter.allow(uid):
        raise ApiProblem(429, "rate-limited", "Too many requests; try again in a minute")
    name = claims.get("name")
    who = Identity(uid, email, str(name) if name else None)
    return users.sign_in(who, auth.bootstrap_owners)


def require_owner(user: Annotated[User, Depends(current_user)]) -> User:
    if user.role != "owner":
        raise ApiProblem(403, "forbidden", "Only an owner can do this")
    return user
