"""Saved sims through the API (SIM-005): save, list, get, pin, update a league, delete, export."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from dikit.time.clock import FrozenClock
from fantasy_api.auth import AuthConfig, InvalidToken, RateLimiter
from fantasy_api.main import create_app
from fantasy_api.users.model import User
from fantasy_api.users.sims import FULL_RUNS, LEAGUES, PINS
from fantasy_api.users.store import InMemoryUserStore

OWNER = "owner@example.com"
T0 = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)
TOKENS: dict[str, dict[str, Any]] = {
    "owner": {"sub": "uid-owner", "email": OWNER, "email_verified": True},
    "friend": {"sub": "uid-friend", "email": "friend@example.com", "email_verified": True},
}


def _verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise InvalidToken("bad")
    return TOKENS[token]


class Api:
    def __init__(self, tmp_path: Path) -> None:
        self.clock = FrozenClock(T0)
        self.store = InMemoryUserStore()
        auth = AuthConfig(frozenset({OWNER}), _verify, RateLimiter(10_000))
        app = create_app(str(tmp_path), auth, users=self.store, clock=self.clock)
        self.client = TestClient(app, raise_server_exceptions=False)
        self.call("GET", "/me")  # the owner bootstraps
        self.store.save_user(User("uid-friend", "friend@example.com", None, "member", T0, T0))

    def call(self, method: str, path: str, token: str = "owner", **kw: Any) -> Any:  # noqa: S107
        headers = {"Authorization": f"Bearer {token}", **kw.pop("headers", {})}
        return self.client.request(method, path, headers=headers, **kw)

    def save(self, sim_id: str, kind: str = "practice", token: str = "owner", **kw: Any) -> Any:  # noqa: S107
        body = {
            "id": sim_id,
            "kind": kind,
            "season": kw.pop("season", "2026-27"),
            "title": "All categories",
            "summary": {"surplus": 12},
            "detail": kw.pop("detail", {"sales": [{"pid": "1", "team": "me", "price": 30}]}),
        }
        self.clock.advance(timedelta(minutes=1))
        return self.call("POST", "/me/sims", token, json=body)


def test_save_list_get_delete(tmp_path: Path) -> None:
    api = Api(tmp_path)
    r = api.save("run-1")
    assert r.status_code == 201
    assert r.json()["detail"]["sales"][0]["price"] == 30
    assert r.headers["etag"] == '"sim-v1"'
    api.save("league-1", kind="league", season="2024-25")
    listed = api.call("GET", "/me/sims").json()
    assert [s["id"] for s in listed] == ["league-1", "run-1"]  # newest first
    assert "detail" not in listed[0]
    assert listed[0]["hasDetail"] is True
    assert [s["id"] for s in api.call("GET", "/me/sims?kind=league").json()] == ["league-1"]
    assert [s["id"] for s in api.call("GET", "/me/sims?season=2026-27").json()] == ["run-1"]
    assert api.call("GET", "/me/sims/run-1").json()["summary"] == {"surplus": 12}
    assert api.call("DELETE", "/me/sims/run-1").status_code == 204
    assert api.call("GET", "/me/sims/run-1").status_code == 404
    assert api.call("DELETE", "/me/sims/run-1").status_code == 404


def test_resaving_the_same_id_is_idempotent(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.save("run-1").status_code == 201
    again = api.save("run-1", detail={"sales": []})  # an offline retry
    assert again.status_code == 200
    assert again.json()["detail"]["sales"][0]["price"] == 30  # the stored copy wins
    assert len(api.call("GET", "/me/sims").json()) == 1


def test_another_users_sim_is_404(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.save("run-1")
    assert api.call("GET", "/me/sims", "friend").json() == []
    assert api.call("GET", "/me/sims/run-1", "friend").status_code == 404
    assert api.call("DELETE", "/me/sims/run-1", "friend").status_code == 404
    assert api.call("GET", "/me/sims/run-1").status_code == 200


def test_retention_trims_old_runs_in_the_same_write(tmp_path: Path) -> None:
    api = Api(tmp_path)
    for i in range(FULL_RUNS + 1):
        api.save(f"run-{i}")
    oldest = api.call("GET", "/me/sims/run-0").json()
    assert oldest["hasDetail"] is False
    assert oldest["detail"] is None
    assert oldest["summary"] == {"surplus": 12}


def test_retention_pins(tmp_path: Path) -> None:
    api = Api(tmp_path)
    for i in range(PINS + 1):
        api.save(f"run-{i}")
    for i in range(PINS):
        r = api.call("PATCH", f"/me/sims/run-{i}/pin", json={"pinned": True})
        assert r.status_code == 200
        assert r.json()["pinned"] is True
    over = api.call("PATCH", f"/me/sims/run-{PINS}/pin", json={"pinned": True})
    assert over.status_code == 409
    assert over.json()["type"] == "/problems/too-many-pins"
    assert api.call("PATCH", "/me/sims/nope/pin", json={"pinned": True}).status_code == 404


def test_retention_leagues(tmp_path: Path) -> None:
    api = Api(tmp_path)
    for i in range(LEAGUES):
        assert api.save(f"league-{i}", kind="league", season="2024-25").status_code == 201
    r = api.save("league-x", kind="league", season="2024-25")
    assert r.status_code == 409
    assert r.json()["type"] == "/problems/too-many-leagues"


def test_league_cas_update_and_stale(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.save("league-1", kind="league", season="2024-25")
    body = {"title": "2024-25", "summary": {"record": "1-0-0"}, "detail": {"results": {"1": 1}}}
    ok = api.call("PUT", "/me/sims/league-1", json=body, headers={"If-Match": '"sim-v1"'})
    assert ok.status_code == 200
    assert ok.headers["etag"] == '"sim-v2"'
    stale = api.call("PUT", "/me/sims/league-1", json=body, headers={"If-Match": '"sim-v1"'})
    assert stale.status_code == 412
    assert stale.json()["current"]["summary"] == {"record": "1-0-0"}
    assert stale.headers["etag"] == '"sim-v2"'


def test_league_cas_needs_if_match_and_a_league(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.save("run-1")
    body = {"title": "x", "summary": {}, "detail": {}}
    assert api.call("PUT", "/me/sims/run-1", json=body).status_code == 428
    r = api.call("PUT", "/me/sims/run-1", json=body, headers={"If-Match": '"sim-v1"'})
    assert r.status_code == 404  # practice runs don't change after saving


def test_limits(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.save("bad id!").json()["field"] == "id"
    assert api.save("run-1", season="2024").json()["field"] == "season"
    big = api.save("run-2", detail={"blob": "x" * (256 * 1024 + 1)})
    assert big.status_code == 413
    assert big.json()["type"] == "/problems/too-large"
    huge_summary = {
        "id": "run-3",
        "kind": "practice",
        "season": "2026-27",
        "title": "t",
        "summary": {"x": "y" * 5000},
        "detail": {},
    }
    r = api.call("POST", "/me/sims", json=huge_summary)
    assert r.status_code == 422
    assert r.json()["field"] == "summary"
    assert api.call("GET", "/me/sims").json() == []
    for method in ("GET", "DELETE"):  # a malformed id is simply not found
        assert api.call(method, "/me/sims/bad%20id").status_code == 404
    assert api.call("PATCH", "/me/sims/bad%20id/pin", json={"pinned": True}).status_code == 404


def test_export_and_delete(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.save("run-1", token="friend")
    exported = api.call("GET", "/me/export", "friend").json()
    assert [s["id"] for s in exported["sims"]] == ["run-1"]
    assert exported["sims"][0]["detail"]["sales"][0]["price"] == 30
    assert api.call("DELETE", "/me", "friend").status_code == 204
    assert api.store.list_sims("uid-friend") == []


def test_sims_need_sign_in(tmp_path: Path) -> None:
    c = Api(tmp_path).client
    assert c.get("/me/sims").status_code == 401
    assert c.post("/me/sims", json={}).status_code == 401
