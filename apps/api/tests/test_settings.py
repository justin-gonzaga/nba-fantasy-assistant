"""Settings, Telegram linking, export and deletion through the API (APP-009): a test per story row.

The in-memory store, a frozen clock and a fake token verifier stand in for Firestore, time, Google.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from dikit.time.clock import FrozenClock
from fantasy_api.auth import AuthConfig, InvalidToken, RateLimiter
from fantasy_api.main import create_app
from fantasy_api.users.model import User
from fantasy_api.users.store import InMemoryUserStore

OWNER = "owner@example.com"
T0 = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)
SECRET = "s3cret-token"
TOKENS: dict[str, dict[str, Any]] = {
    "owner": {"sub": "uid-owner", "email": OWNER, "email_verified": True},
    "second": {"sub": "uid-second", "email": "second@example.com", "email_verified": True},
}


def _verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise InvalidToken("bad")
    return TOKENS[token]


class Api:
    def __init__(self, tmp_path: Path, *, secret: str | None = SECRET) -> None:
        self.clock = FrozenClock(T0)
        self.store = InMemoryUserStore()
        auth = AuthConfig(frozenset({OWNER, "second@example.com"}), _verify, RateLimiter(1000))
        app = create_app(
            str(tmp_path), auth, users=self.store, clock=self.clock, telegram_secret=secret
        )
        self.client = TestClient(app, raise_server_exceptions=False)

    def add(self, role: str = "member") -> None:
        """The second account, already a member (or a second owner)."""
        self.store.save_user(User("uid-second", "second@example.com", None, role, T0, T0))  # type: ignore[arg-type]

    def call(self, method: str, path: str, token: str = "owner", **kw: Any) -> Any:  # noqa: S107
        headers = {"Authorization": f"Bearer {token}", **kw.pop("headers", {})}
        return self.client.request(method, path, headers=headers, **kw)

    def patch(self, body: dict[str, Any], etag: str | None, token: str = "owner") -> Any:  # noqa: S107
        headers = {"If-Match": etag} if etag is not None else {}
        return self.call("PATCH", "/me/settings", token, json=body, headers=headers)

    def webhook(self, text: str | None, secret: str | None = SECRET, chat: int = 42) -> Any:
        update: dict[str, Any] = {"update_id": 1}
        if text is not None:
            update["message"] = {"chat": {"id": chat}, "text": text}
        headers = {"X-Telegram-Bot-Api-Secret-Token": secret} if secret else {}
        return self.client.post("/telegram/webhook", json=update, headers=headers)


# ---------- AC1: GET ----------
def test_defaults(tmp_path: Path) -> None:
    r = Api(tmp_path).call("GET", "/me/settings")
    assert r.status_code == 200
    assert r.json() == {
        "timeZone": "Australia/Sydney",
        "briefEnabled": True,
        "awakeStart": "07:00",
        "awakeEnd": "22:00",
        "alerts": ["brief", "injury", "waiver"],
        "draftStrategy": "all",
        "theme": "system",
        "displayName": None,
        "telegramLinked": False,
        "version": 0,
    }


def test_etag(tmp_path: Path) -> None:
    api = Api(tmp_path)
    r = api.call("GET", "/me/settings")
    assert r.headers["etag"] == '"settings-v0"'
    assert r.headers["cache-control"] == "no-store"
    saved = api.patch({"theme": "dark"}, r.headers["etag"])
    assert saved.headers["etag"] == '"settings-v1"'
    assert api.call("GET", "/me/settings").headers["etag"] == '"settings-v1"'


# ---------- AC2: PATCH ----------
def test_valid_partial_update_leaves_the_rest(tmp_path: Path) -> None:
    api = Api(tmp_path)
    r = api.patch({"awakeStart": "08:30", "alerts": ["waiver", "brief"]}, '"settings-v0"')
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["awakeStart"] == "08:30"
    assert body["alerts"] == ["brief", "waiver"]  # injury muted; canonical order
    assert body["timeZone"] == "Australia/Sydney"
    assert body["version"] == 1


def test_each_invalid_field_is_named(tmp_path: Path) -> None:
    api = Api(tmp_path)
    cases = {
        "timeZone": "Mars/Olympus",
        "awakeStart": "8:30",
        "awakeEnd": "24:00",
        "alerts": ["brief", "spam"],
        "draftStrategy": "punt_everything",
        "theme": "neon",
        "displayName": "   ",
        "briefEnabled": None,
    }
    for key, value in cases.items():
        r = api.patch({key: value}, '"settings-v0"')
        assert r.status_code == 422, (key, r.text)
        assert r.headers["content-type"].startswith("application/problem+json")
        assert r.json()["type"] == "/problems/invalid-setting", key
        assert r.json()["field"] in {key, _snake(key)}, key
    unknown = api.patch({"telegramChatId": "1"}, '"settings-v0"')
    assert unknown.status_code == 422  # not a user-editable field
    assert api.call("GET", "/me/settings").json()["version"] == 0  # nothing was saved


def _snake(camel: str) -> str:
    return "".join(f"_{c.lower()}" if c.isupper() else c for c in camel)


def test_stale_etag_is_412_with_the_current_document(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.patch({"theme": "dark"}, '"settings-v0"').status_code == 200  # tab A
    r = api.patch({"theme": "light"}, '"settings-v0"')  # tab B, stale
    assert r.status_code == 412
    assert r.json()["type"] == "/problems/stale-settings"
    assert r.json()["current"]["theme"] == "dark"
    assert r.headers["etag"] == '"settings-v1"'
    assert api.patch({"theme": "light"}, "garbage").status_code == 412
    assert api.call("GET", "/me/settings").json()["theme"] == "dark"


def test_missing_if_match_is_428(tmp_path: Path) -> None:
    r = Api(tmp_path).patch({"theme": "dark"}, None)
    assert r.status_code == 428
    assert r.json()["type"] == "/problems/precondition-required"


def test_settings_are_per_user(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.call("GET", "/me")  # the owner bootstraps
    api.add()
    api.patch({"theme": "dark"}, '"settings-v0"')
    assert api.call("GET", "/me/settings", "second").json()["theme"] == "system"


# ---------- AC3: Telegram ----------
def test_telegram_link_binds_the_chat(tmp_path: Path) -> None:
    api = Api(tmp_path)
    link = api.call("POST", "/me/telegram/link")
    assert link.status_code == 201
    code = link.json()["code"]
    assert len(code) == 8
    assert link.json()["expiresAt"].startswith("2026-10-04T09:10")
    r = api.webhook(f"/start {code}")
    assert r.status_code == 200
    assert r.json()["method"] == "sendMessage"
    assert r.json()["chat_id"] == 42
    assert "Linked" in r.json()["text"]
    settings = api.call("GET", "/me/settings").json()
    assert settings["telegramLinked"] is True
    assert "telegramChatId" not in settings  # the chat id is never shown


def test_telegram_link_relinking_replaces_the_old_chat(tmp_path: Path) -> None:
    api = Api(tmp_path)
    for chat in (42, 77):
        code = api.call("POST", "/me/telegram/link").json()["code"]
        assert "Linked" in api.webhook(f"/start {code}", chat=chat).json()["text"]
    stored = api.store.get_settings("uid-owner")
    assert stored is not None
    assert stored.telegram_chat_id == "77"


def test_telegram_link_codes_are_single_use(tmp_path: Path) -> None:
    api = Api(tmp_path)
    code = api.call("POST", "/me/telegram/link").json()["code"]
    api.webhook(f"/start {code}")
    again = api.webhook(f"/start {code}", chat=99)
    assert "invalid, used or expired" in again.json()["text"]
    stored = api.store.get_settings("uid-owner")
    assert stored is not None
    assert stored.telegram_chat_id == "42"


def test_telegram_link_codes_expire(tmp_path: Path) -> None:
    api = Api(tmp_path)
    code = api.call("POST", "/me/telegram/link").json()["code"]
    api.clock.advance(timedelta(minutes=10))
    assert "invalid, used or expired" in api.webhook(f"/start {code}").json()["text"]
    assert api.call("GET", "/me/settings").json()["telegramLinked"] is False


def test_telegram_link_keeps_settings_changes(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.patch({"theme": "dark"}, '"settings-v0"')
    code = api.call("POST", "/me/telegram/link").json()["code"]
    api.webhook(f"/start {code.lower()}")  # codes are case-insensitive when typed
    s = api.call("GET", "/me/settings").json()
    assert (s["theme"], s["telegramLinked"], s["version"]) == ("dark", True, 2)


def test_webhook_bad_secret_is_401(tmp_path: Path) -> None:
    api = Api(tmp_path)
    code = api.call("POST", "/me/telegram/link").json()["code"]
    assert api.webhook(f"/start {code}", secret="wrong").status_code == 401
    assert api.webhook(f"/start {code}", secret=None).status_code == 401
    assert api.call("GET", "/me/settings").json()["telegramLinked"] is False


def test_webhook_unrelated_messages_are_acknowledged_and_ignored(tmp_path: Path) -> None:
    api = Api(tmp_path)
    for text in (None, "hello", "/help", ""):
        r = api.webhook(text)
        assert r.status_code == 200, text
        assert r.json() == {}, text
    bare = api.webhook("/start")
    assert "tap Link Telegram" in bare.json()["text"]
    assert "invalid, used or expired" in api.webhook("/start NOPE1234").json()["text"]


def test_webhook_is_off_without_a_secret(tmp_path: Path) -> None:
    assert Api(tmp_path, secret=None).webhook("/start X").status_code == 404


def test_webhook_is_not_in_the_public_schema(tmp_path: Path) -> None:
    paths = Api(tmp_path).client.get("/openapi.json").json()["paths"]
    assert "/telegram/webhook" not in paths
    assert "/me/settings" in paths


# ---------- AC4: export and delete ----------
def test_export(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.patch({"awakeEnd": "21:30"}, '"settings-v0"')
    r = api.call("GET", "/me/export")
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["email"] == OWNER
    assert body["profile"]["role"] == "owner"
    assert body["settings"]["awakeEnd"] == "21:30"


def test_delete(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.call("GET", "/me")  # the owner bootstraps
    api.add()
    api.patch({"theme": "dark"}, '"settings-v0"', token="second")
    assert api.call("DELETE", "/me", "second").status_code == 204
    assert api.store.get_user("uid-second") is None
    assert api.store.get_settings("uid-second") is None


def test_last_owner_cannot_delete(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.call("GET", "/me")
    r = api.call("DELETE", "/me")
    assert r.status_code == 409
    assert r.json()["type"] == "/problems/last-owner"
    assert api.store.get_user("uid-owner") is not None


def test_routes_need_sign_in(tmp_path: Path) -> None:
    c = Api(tmp_path).client
    for method, path in (
        ("GET", "/me/settings"),
        ("PATCH", "/me/settings"),
        ("POST", "/me/telegram/link"),
        ("GET", "/me/export"),
        ("DELETE", "/me"),
    ):
        assert c.request(method, path).status_code == 401, path


def test_telegram_link_that_keeps_losing_the_race_says_so(tmp_path: Path) -> None:
    api = Api(tmp_path)
    code = api.call("POST", "/me/telegram/link").json()["code"]
    api.store.save_settings_if = lambda *_: False  # type: ignore[method-assign]
    assert "changing at the same moment" in api.webhook(f"/start {code}").json()["text"]
