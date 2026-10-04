"""SIM-001 AC2: the replay files through the API (signed in, read-only, cached)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from fantasy_api.auth import AuthConfig, RateLimiter
from fantasy_api.main import create_app

OWNER = "owner@example.com"


def _verify(token: str) -> dict[str, Any]:
    return {"sub": "uid-owner", "email": OWNER, "email_verified": True}


def _client(root: Path, auth: bool = True) -> TestClient:
    cfg = AuthConfig(frozenset({OWNER}), _verify, RateLimiter(1000)) if auth else None
    return TestClient(create_app(str(root), cfg), raise_server_exceptions=False)


def _publish(root: Path, season: str) -> dict[str, Any]:
    doc = {"season": season, "players": [], "weeks": [], "lines": {"dates": []}}
    (root / "replay").mkdir(exist_ok=True)
    (root / "replay" / f"{season}.json").write_text(json.dumps(doc), encoding="utf-8")
    return doc


H = {"Authorization": "Bearer t"}


def test_lists_only_published_seasons(tmp_path: Path) -> None:
    _publish(tmp_path, "2024-25")
    r = _client(tmp_path).get("/replay/seasons", headers=H)
    assert r.status_code == 200
    assert r.json() == {"seasons": ["2024-25"]}


def test_serves_a_season_with_a_long_private_cache(tmp_path: Path) -> None:
    doc = _publish(tmp_path, "2024-25")
    r = _client(tmp_path).get("/replay/2024-25", headers=H)
    assert r.status_code == 200
    assert r.json() == doc
    assert r.headers["cache-control"] == "private, max-age=86400"


def test_unknown_or_unpublished_season_is_404(tmp_path: Path) -> None:
    c = _client(tmp_path)
    for season in ("2025-26", "1999-00", "../secrets"):
        r = c.get(f"/replay/{season}", headers=H)
        assert r.status_code == 404, season
        assert r.headers["content-type"].startswith("application/problem+json")


def test_needs_sign_in(tmp_path: Path) -> None:
    _publish(tmp_path, "2024-25")
    assert _client(tmp_path).get("/replay/2024-25").status_code == 401
