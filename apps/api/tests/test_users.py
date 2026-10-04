"""Users, roles and invites through the API (APP-008): one test per user-story row.

The in-memory store and a fake token verifier stand in for Firestore and Google (no real accounts).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dikit.time.clock import FrozenClock
from fantasy_api.auth import AuthConfig, InvalidToken, RateLimiter
from fantasy_api.errors import PROBLEM_BASE
from fantasy_api.main import create_app, user_store
from fantasy_api.users.store import InMemoryUserStore

OWNER = "owner@example.com"
T0 = datetime(2026, 10, 3, 9, 0, tzinfo=UTC)


def _claims(
    uid: str, email: str, *, verified: bool = True, name: str | None = None
) -> dict[str, Any]:
    c: dict[str, Any] = {"sub": uid, "email": email, "email_verified": verified}
    if name:
        c["name"] = name
    return c


TOKENS: dict[str, dict[str, Any]] = {
    "owner": _claims("uid-owner", OWNER, name="Olive Owner"),
    "owner-caps": _claims("uid-owner", "Owner@Example.COM", name="Olive Owner"),
    "friend": _claims("uid-friend", "friend@example.com", name="Fred"),
    "friend-new-email": _claims("uid-friend", "fred@example.org", name="Fred"),
    "friend-other-account": _claims("uid-friend-2", "fred.other@example.com"),
    "second-bootstrap": _claims("uid-second", "second@example.com"),
    "stranger": _claims("uid-stranger", "someone@example.com"),
    "unverified": _claims("uid-owner", OWNER, verified=False),
    "no-uid": {"email": OWNER, "email_verified": True},
}


def fake_verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise InvalidToken("bad signature")
    return TOKENS[token]


class Api:
    def __init__(self, tmp_path: Path) -> None:
        (tmp_path / "briefs").mkdir(exist_ok=True)
        self.clock = FrozenClock(T0)
        self.store = InMemoryUserStore()
        auth = AuthConfig(
            bootstrap_owners=frozenset({OWNER, "second@example.com"}),
            verify=fake_verify,
            limiter=RateLimiter(1000),
        )
        app = create_app(str(tmp_path), auth=auth, users=self.store, clock=self.clock)
        self.client = TestClient(app, raise_server_exceptions=False)

    def call(self, method: str, path: str, token: str, **kw: Any) -> Any:
        return self.client.request(method, path, headers={"Authorization": f"Bearer {token}"}, **kw)

    def get(self, path: str, token: str) -> Any:
        return self.call("GET", path, token)

    def invite(self, email: str, who: str = "owner", **body: Any) -> Any:
        return self.call("POST", "/invites", who, json={"email": email, **body})


@pytest.fixture
def api(tmp_path: Path) -> Api:
    a = Api(tmp_path)
    assert a.get("/me", "owner").status_code == 200  # the owner bootstraps first
    return a


def _kind(r: Any) -> str:
    assert r.headers["content-type"].startswith("application/problem+json")
    return str(r.json()["type"]).removeprefix(f"{PROBLEM_BASE}/")


# ---------- Owner (first sign-in) ----------
def test_bootstrap_owner_once(tmp_path: Path) -> None:
    a = Api(tmp_path)
    first = a.get("/me", "owner-caps")  # the email compare is case-insensitive
    assert first.status_code == 200
    assert first.json()["role"] == "owner"
    assert first.json()["email"] == OWNER
    a.clock.advance(timedelta(days=1))
    assert a.get("/me", "owner").json()["role"] == "owner"  # not demoted
    assert [u.uid for u in a.store.list_users()] == ["uid-owner"]  # not duplicated
    # Bootstrap happens once: another allowlisted email after the first owner needs an invite.
    r = a.get("/me", "second-bootstrap")
    assert r.status_code == 403
    assert _kind(r) == "not-invited"


def test_me(api: Api) -> None:
    r = api.get("/me", "owner")
    assert r.status_code == 200
    assert r.json() == {
        "uid": "uid-owner",
        "email": OWNER,
        "displayName": "Olive Owner",
        "role": "owner",
    }


def test_uninvited_is_403(api: Api) -> None:
    r = api.get("/me", "stranger")
    assert r.status_code == 403
    assert _kind(r) == "not-invited"
    assert api.get("/system/freshness", "stranger").status_code == 403


def test_unverified_or_uidless_tokens_are_forbidden(api: Api) -> None:
    for token in ("unverified", "no-uid"):
        r = api.get("/me", token)
        assert r.status_code == 403
        assert _kind(r) == "forbidden"
    assert api.get("/me", "forged").status_code == 401


# ---------- Owner: invite, remove ----------
def test_owner_invites_lists_and_revokes(api: Api) -> None:
    r = api.invite("Friend@Example.com ")
    assert r.status_code == 201
    inv = r.json()
    assert inv["email"] == "friend@example.com"
    assert inv["role"] == "member"
    assert inv["createdBy"] == "uid-owner"
    assert inv["status"] == "open"
    assert datetime.fromisoformat(inv["expiresAt"]) == T0 + timedelta(days=14)
    assert [i["id"] for i in api.get("/invites", "owner").json()] == [inv["id"]]
    assert api.call("DELETE", f"/invites/{inv['id']}", "owner").status_code == 204
    assert api.get("/invites", "owner").json() == []
    assert _kind(api.call("DELETE", f"/invites/{inv['id']}", "owner")) == "not-found"
    assert api.get("/me", "friend").status_code == 403  # a revoked invite grants nothing


def test_duplicate_invite_returns_the_existing_one(api: Api) -> None:
    first = api.invite("friend@example.com")
    again = api.invite("FRIEND@example.com")
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert len(api.get("/invites", "owner").json()) == 1


def test_inviting_an_existing_member_is_409(api: Api) -> None:
    api.invite("friend@example.com")
    api.get("/me", "friend")
    r = api.invite("friend@example.com")
    assert r.status_code == 409
    assert _kind(r) == "already-member"
    assert _kind(api.invite(OWNER)) == "already-member"


def test_invites_expire_after_14_days(api: Api) -> None:
    old = api.invite("friend@example.com").json()
    api.clock.advance(timedelta(days=14))
    assert api.get("/invites", "owner").json()[0]["status"] == "expired"
    r = api.get("/me", "friend")
    assert r.status_code == 403
    assert _kind(r) == "invite-expired"
    fresh = api.invite("friend@example.com")  # re-inviting replaces the expired invite
    assert fresh.status_code == 201
    assert fresh.json()["id"] != old["id"]
    assert api.get("/me", "friend").status_code == 200


def test_last_owner_cannot_remove_themself(api: Api) -> None:
    r = api.call("DELETE", "/members/uid-owner", "owner")
    assert r.status_code == 409
    assert _kind(r) == "last-owner"
    assert api.get("/me", "owner").status_code == 200


def test_a_second_owner_can_be_invited_and_one_owner_removed(api: Api) -> None:
    assert api.invite("friend@example.com", role="owner").json()["role"] == "owner"
    assert api.get("/me", "friend").json()["role"] == "owner"
    assert api.call("DELETE", "/members/uid-owner", "friend").status_code == 204
    assert _kind(api.call("DELETE", "/members/uid-friend", "friend")) == "last-owner"
    assert _kind(api.call("DELETE", "/members/nobody", "friend")) == "not-found"


def test_invite_needs_a_valid_email(api: Api) -> None:
    for bad in ("not-an-email", "", "a@b"):
        r = api.invite(bad)
        assert r.status_code == 422
        assert _kind(r) == "invalid-request"
    assert api.invite("x@example.com", role="admin").status_code == 422


# ---------- Invited member ----------
def test_invite_claim(api: Api) -> None:
    inv = api.invite("friend@example.com").json()
    api.clock.advance(timedelta(minutes=1))  # members list in joining order
    r = api.get("/me", "friend")
    assert r.status_code == 200
    assert r.json() == {
        "uid": "uid-friend",
        "email": "friend@example.com",
        "displayName": "Fred",
        "role": "member",
    }
    listed = {i["id"]: i for i in api.get("/invites", "owner").json()}
    assert listed[inv["id"]]["claimedBy"] == "uid-friend"
    assert listed[inv["id"]]["status"] == "claimed"
    members = api.get("/members", "owner").json()
    assert [(m["uid"], m["role"]) for m in members] == [
        ("uid-owner", "owner"),
        ("uid-friend", "member"),
    ]
    assert api.get("/system/freshness", "friend").status_code == 200  # the views work for members


def test_a_different_email_is_403_with_a_clear_problem(api: Api) -> None:
    api.invite("friend@example.com")
    r = api.get("/me", "friend-other-account")
    assert r.status_code == 403
    assert _kind(r) == "not-invited"
    assert "invite was sent to" in r.json()["detail"]


# ---------- Removed member ----------
def test_removed_member_is_locked_out(api: Api) -> None:
    api.invite("friend@example.com")
    assert api.get("/system/freshness", "friend").status_code == 200
    assert api.call("DELETE", "/members/uid-friend", "owner").status_code == 204
    r = api.get("/system/freshness", "friend")  # the same, still-valid token
    assert r.status_code == 403
    assert _kind(r) == "not-invited"
    assert api.get("/me", "friend").status_code == 403


# ---------- Any user: email change ----------
def test_email_change_keeps_the_account(api: Api) -> None:
    api.invite("friend@example.com")
    api.clock.advance(timedelta(minutes=1))
    api.get("/me", "friend")
    r = api.get("/me", "friend-new-email")
    assert r.status_code == 200
    assert (r.json()["uid"], r.json()["email"], r.json()["role"]) == (
        "uid-friend",
        "fred@example.org",
        "member",
    )
    assert [u.email for u in api.store.list_users()] == [OWNER, "fred@example.org"]


def test_last_seen_is_refreshed_but_throttled(api: Api) -> None:
    api.clock.advance(timedelta(minutes=5))
    api.get("/me", "owner")
    user = api.store.get_user("uid-owner")
    assert user is not None
    assert user.last_seen_at == T0
    api.clock.advance(timedelta(minutes=15))
    api.get("/me", "owner")
    user = api.store.get_user("uid-owner")
    assert user is not None
    assert user.last_seen_at == T0 + timedelta(minutes=20)


# ---------- Attacker ----------
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/invites"),
        ("GET", "/invites"),
        ("DELETE", "/invites/any"),
        ("GET", "/members"),
        ("DELETE", "/members/uid-owner"),
    ],
)
def test_members_get_403_on_owner_endpoints(api: Api, method: str, path: str) -> None:
    api.invite("friend@example.com")
    body = {"json": {"email": "x@example.com"}} if method == "POST" else {}
    r = api.call(method, path, "friend", **body)
    assert r.status_code == 403
    assert _kind(r) == "forbidden"
    assert api.call(method, path, "stranger", **body).status_code == 403
    assert api.client.request(method, path, **body).status_code == 401


def test_the_uid_comes_only_from_the_verified_token(api: Api) -> None:
    api.invite("friend@example.com")
    api.get("/me", "friend")
    forged = api.client.get(
        "/me?uid=uid-owner",
        headers={"Authorization": "Bearer friend", "X-User-Id": "uid-owner"},
    )
    assert forged.json()["uid"] == "uid-friend"
    r = api.call("POST", "/invites", "owner", json={"email": "y@example.com", "createdBy": "x"})
    assert r.json()["createdBy"] == "uid-owner"
    assert api.call("DELETE", "/members/uid-owner", "friend").status_code == 403


# ---------- Local development (auth off) ----------
def test_local_development_is_the_owner(tmp_path: Path) -> None:
    client = TestClient(create_app(str(tmp_path)))
    me = client.get("/me").json()
    assert (me["uid"], me["role"]) == ("local", "owner")
    assert client.post("/invites", json={"email": "f@example.com"}).status_code == 201


def test_the_store_stays_in_memory_until_the_owner_switches_to_firestore() -> None:
    """Deploying APP-008 before the Terraform apply must not break sign-in."""
    made: list[str] = []

    def firestore() -> InMemoryUserStore:
        made.append("firestore")
        return InMemoryUserStore()

    auth = object()
    assert isinstance(user_store(auth, "memory", firestore), InMemoryUserStore)  # type: ignore[arg-type]
    assert made == []
    user_store(auth, "firestore", firestore)  # type: ignore[arg-type]
    assert made == ["firestore"]
    user_store(None, "firestore", firestore)  # auth off (local dev): never Firestore
    assert made == ["firestore"]
