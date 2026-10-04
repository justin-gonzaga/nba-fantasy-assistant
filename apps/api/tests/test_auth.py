import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dikit.errors import ConfigError
from fantasy_api.auth import AuthConfig, InvalidToken, RateLimiter
from fantasy_api.errors import PROBLEM_BASE
from fantasy_api.main import create_app, require_auth_config

OWNER = "owner@example.com"
TOKENS: dict[str, dict[str, Any]] = {
    "owner": {"sub": "uid-owner", "email": OWNER, "email_verified": True},
    "stranger": {"sub": "uid-x", "email": "someone@example.com", "email_verified": True},
    "unverified": {"sub": "uid-owner", "email": OWNER, "email_verified": False},
}


def fake_verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise InvalidToken("bad signature")
    return TOKENS[token]


class Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def _app(tmp_path: Path, per_minute: int = 60, clock: Clock | None = None) -> TestClient:
    (tmp_path / "briefs").mkdir(exist_ok=True)
    auth = AuthConfig(
        bootstrap_owners=frozenset({OWNER}),
        verify=fake_verify,
        limiter=RateLimiter(per_minute, clock or Clock()),
    )
    return TestClient(create_app(str(tmp_path), auth=auth), raise_server_exceptions=False)


def _get(client: TestClient, path: str, token: str | None) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get(path, headers=headers)


def test_health_stays_public(tmp_path: Path) -> None:
    assert _get(_app(tmp_path), "/system/health", None).status_code == 200


@pytest.mark.parametrize("path", ["/today", "/matchup", "/waivers", "/system/freshness"])
def test_data_routes_need_a_token(tmp_path: Path, path: str) -> None:
    r = _get(_app(tmp_path), path, None)
    assert r.status_code == 401
    assert r.json()["type"] == f"{PROBLEM_BASE}/unauthenticated"
    assert r.headers["www-authenticate"] == "Bearer"


def test_invalid_tokens_are_401_and_strangers_403(tmp_path: Path) -> None:
    client = _app(tmp_path)
    assert _get(client, "/system/freshness", "forged").status_code == 401
    r = _get(client, "/system/freshness", "stranger")
    assert r.status_code == 403
    assert r.json()["type"] == f"{PROBLEM_BASE}/not-invited"  # APP-008: the store decides
    r = _get(client, "/system/freshness", "unverified")
    assert r.status_code == 403
    assert r.json()["type"] == f"{PROBLEM_BASE}/forbidden"


def test_the_allowlisted_owner_gets_through(tmp_path: Path) -> None:
    client = _app(tmp_path)
    assert _get(client, "/system/freshness", "owner").status_code == 200
    assert _get(client, "/today", "owner").status_code == 404  # authorised; no brief yet


def test_rate_limit_per_user_with_a_window(tmp_path: Path) -> None:
    clock = Clock()
    client = _app(tmp_path, per_minute=2, clock=clock)
    assert [_get(client, "/system/freshness", "owner").status_code for _ in range(3)] == [
        200,
        200,
        429,
    ]
    r = _get(client, "/system/freshness", "owner")
    assert r.json()["type"] == f"{PROBLEM_BASE}/rate-limited"
    clock.t += 61
    assert _get(client, "/system/freshness", "owner").status_code == 200


def test_outside_local_an_allowlist_is_required() -> None:
    with pytest.raises(ConfigError):
        require_auth_config(app_env="prod", allowed_emails="", firebase_project="p")
    with pytest.raises(ConfigError):
        require_auth_config(app_env="dev", allowed_emails=OWNER, firebase_project=None)
    assert require_auth_config(app_env="local", allowed_emails="", firebase_project=None) is None
    cfg = require_auth_config(
        app_env="prod", allowed_emails=f" {OWNER} , x@y.z", firebase_project="p"
    )
    assert cfg is not None
    assert cfg.bootstrap_owners == frozenset({OWNER, "x@y.z"})


def test_openapi_documents_bearer_auth(tmp_path: Path) -> None:
    spec = json.loads(json.dumps(_app(tmp_path).app.openapi()))  # type: ignore[attr-defined]
    assert "HTTPBearer" in spec["components"]["securitySchemes"]
