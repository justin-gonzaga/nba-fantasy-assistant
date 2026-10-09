"""Draft settings and presets through the API (APP-011): a test per story row and a row per rule.

The in-memory store, a frozen clock and a fake token verifier stand in for Firestore, time, Google.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from dikit.time.clock import FrozenClock
from fantasy_api.auth import AuthConfig, InvalidToken, RateLimiter
from fantasy_api.main import create_app
from fantasy_api.users import draft_settings
from fantasy_api.users.model import User
from fantasy_api.users.store import InMemoryUserStore
from fantasy_core.league import ScoringFormat

OWNER = "owner@example.com"
T0 = datetime(2026, 10, 4, 9, 0, tzinfo=UTC)
TOKENS: dict[str, dict[str, Any]] = {
    "owner": {"sub": "uid-owner", "email": OWNER, "email_verified": True},
    "second": {"sub": "uid-second", "email": "second@example.com", "email_verified": True},
}
PATH = "/me/draft-settings"


def _verify(token: str) -> dict[str, Any]:
    if token not in TOKENS:
        raise InvalidToken("bad")
    return TOKENS[token]


class Api:
    def __init__(self, tmp_path: Path) -> None:
        self.store = InMemoryUserStore()
        auth = AuthConfig(frozenset({OWNER, "second@example.com"}), _verify, RateLimiter(1000))
        app = create_app(str(tmp_path), auth, users=self.store, clock=FrozenClock(T0))
        self.client = TestClient(app, raise_server_exceptions=False)
        self.store.save_user(User("uid-second", "second@example.com", None, "member", T0, T0))

    def call(self, method: str, path: str = PATH, token: str = "owner", **kw: Any) -> Any:  # noqa: S107
        headers = {"Authorization": f"Bearer {token}", **kw.pop("headers", {})}
        return self.client.request(method, path, headers=headers, **kw)

    def put(self, body: Any, etag: str | None = '"draft-v0"', token: str = "owner") -> Any:  # noqa: S107
        headers = {"If-Match": etag} if etag is not None else {}
        return self.call("PUT", token=token, json=body, headers=headers)


def preset(n: int = 1, **league: Any) -> dict[str, Any]:
    return {
        "id": f"p{n}",
        "name": f"Preset {n}",
        "updatedAt": "2026-10-04T09:00:00Z",
        "league": {
            "scoring": "h2h_categories",
            "drafting": "auction",
            "teams": 16,
            "budget": 200,
            "spots": 13,
            "seat": 5,
            **league,
        },
        "room": {"pace": "real", "nominateSeconds": 30, "bidSeconds": 15, "styles": "mix"},
        "strategy": {"punt": None},
        "season": "current",
    }


def doc(*presets: dict[str, Any], active: str | None = None) -> dict[str, Any]:
    fx = {"sound": True, "volume": 0.6, "tick": "last10", "motion": "auto"}
    return {"activeId": active, "presets": list(presets), "fx": fx}


# ---------- AC1: get, put, etag, stale, missing ----------
def test_get_returns_the_empty_defaults_for_a_new_user(tmp_path: Path) -> None:
    r = Api(tmp_path).call("GET")
    assert r.status_code == 200
    assert r.json() == {
        "activeId": None,
        "presets": [],
        "fx": {"sound": True, "volume": 0.6, "tick": "last10", "motion": "auto"},
        "version": 0,
    }
    assert r.headers["etag"] == '"draft-v0"'
    assert r.headers["cache-control"] == "no-store"


def test_put_saves_the_whole_document_and_etag_follows_the_version(tmp_path: Path) -> None:
    api = Api(tmp_path)
    saved = api.put(doc(preset(1), preset(2), active="p2"))
    assert saved.status_code == 200
    assert saved.headers["etag"] == '"draft-v1"'
    got = api.call("GET")
    assert got.headers["etag"] == '"draft-v1"'
    body = got.json()
    assert body["version"] == 1
    assert body["activeId"] == "p2"
    assert [p["name"] for p in body["presets"]] == ["Preset 1", "Preset 2"]
    assert body["presets"][0]["league"]["scoring"] == "h2h_categories"
    assert body["presets"][0]["room"]["nominateSeconds"] == 30
    assert body["presets"][0]["updatedAt"] == "2026-10-04T09:00:00Z"
    replaced = api.put(doc(preset(3)), '"draft-v1"')
    assert replaced.status_code == 200
    assert [p["id"] for p in api.call("GET").json()["presets"]] == ["p3"]


def test_put_with_a_stale_etag_is_412_with_the_current_document(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.put(doc(preset(1))).status_code == 200
    stale = api.put(doc(preset(2)), '"draft-v0"')
    assert stale.status_code == 412
    assert stale.headers["etag"] == '"draft-v1"'
    problem = stale.json()
    assert problem["type"] == "/problems/stale-draft-settings"
    assert problem["current"]["version"] == 1
    assert problem["current"]["presets"][0]["id"] == "p1"
    assert api.put(doc(preset(2)), "garbage").status_code == 412  # unreadable is stale, not a crash


def test_put_without_if_match_is_428_and_changes_nothing(tmp_path: Path) -> None:
    api = Api(tmp_path)
    r = api.put(doc(preset(1)), None)
    assert r.status_code == 428
    assert r.json()["type"] == "/problems/precondition-required"
    assert api.call("GET").json()["version"] == 0


def test_put_a_body_that_is_not_json_is_422(tmp_path: Path) -> None:
    api = Api(tmp_path)
    r = api.call("PUT", content=b"{nope", headers={"If-Match": '"draft-v0"'})
    assert r.status_code == 422
    assert r.json()["type"] == "/problems/invalid-json"


def test_signed_out_is_401(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.client.get(PATH).status_code == 401
    assert api.client.put(PATH, json=doc(), headers={"If-Match": '"draft-v0"'}).status_code == 401


# ---------- AC2: validation, limits, unsupported ----------
def _with(mutate: Callable[[dict[str, Any]], None], base: dict[str, Any] | None = None) -> Any:
    out = copy.deepcopy(base if base is not None else doc(preset(1), preset(2), preset(3)))
    mutate(out)
    return out


def _league(p: int, **kw: Any) -> Callable[[dict[str, Any]], None]:
    return lambda d: d["presets"][p]["league"].update(kw)


def _set(path: tuple[Any, ...], value: Any) -> Callable[[dict[str, Any]], None]:
    def run(d: dict[str, Any]) -> None:
        node = d
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

    return run


def _drop(path: tuple[Any, ...]) -> Callable[[dict[str, Any]], None]:
    def run(d: dict[str, Any]) -> None:
        node = d
        for key in path[:-1]:
            node = node[key]
        del node[path[-1]]

    return run


def _punt_outside(d: dict[str, Any]) -> None:
    _league(0, categories=["pts", "reb"])(d)
    _set(("presets", 0, "strategy", "punt"), "ast")(d)


VALIDATION: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    ("teams below 4", _league(2, teams=3), "presets[2].league.teams"),
    ("teams above 20", _league(2, teams=21), "presets[2].league.teams"),
    ("teams not a whole number", _league(2, teams=12.5), "presets[2].league.teams"),
    ("teams a boolean", _league(2, teams=True), "presets[2].league.teams"),
    ("spots below 5", _league(1, spots=4), "presets[1].league.spots"),
    ("spots above 25", _league(1, spots=30), "presets[1].league.spots"),
    ("seat above teams", _league(0, teams=10, seat=11), "presets[0].league.seat"),
    ("seat below 1", _league(0, seat=0), "presets[0].league.seat"),
    ("budget below 50", _league(0, budget=49), "presets[0].league.budget"),
    ("budget above 1000", _league(0, budget=1001), "presets[0].league.budget"),
    ("auction without a budget", _league(0, budget=None), "presets[0].league.budget"),
    ("snake with a budget", _league(0, drafting="snake"), "presets[0].league.budget"),
    ("unknown scoring", _league(0, scoring="rotto"), "presets[0].league.scoring"),
    ("unknown drafting", _league(0, drafting="keeper"), "presets[0].league.drafting"),
    (
        "duplicate category",
        _league(0, categories=["pts", "pts"]),
        "presets[0].league.categories[1]",
    ),
    ("unknown category", _league(0, categories=["pts", "zzz"]), "presets[0].league.categories[1]"),
    ("empty categories", _league(0, categories=[]), "presets[0].league.categories"),
    ("pace unknown", _set(("presets", 0, "room", "pace"), "slow"), "presets[0].room.pace"),
    (
        "nominate under 5 s",
        _set(("presets", 0, "room", "nominateSeconds"), 4),
        "presets[0].room.nominateSeconds",
    ),
    (
        "bid over 120 s",
        _set(("presets", 0, "room", "bidSeconds"), 121),
        "presets[0].room.bidSeconds",
    ),
    ("styles unknown", _set(("presets", 0, "room", "styles"), "x"), "presets[0].room.styles"),
    ("season shape", _set(("presets", 0, "season"), "2026"), "presets[0].season"),
    ("season not consecutive", _set(("presets", 0, "season"), "2025-28"), "presets[0].season"),
    (
        "updatedAt without a zone",
        _set(("presets", 0, "updatedAt"), "2026-10-04T09:00:00"),
        "presets[0].updatedAt",
    ),
    (
        "updatedAt not a time",
        _set(("presets", 0, "updatedAt"), "yesterday"),
        "presets[0].updatedAt",
    ),
    (
        "punt outside the categories",
        _set(("presets", 0, "strategy", "punt"), "dunks"),
        "presets[0].strategy.punt",
    ),
    (
        "punt not in the chosen categories",
        _punt_outside,
        "presets[0].strategy.punt",
    ),
    ("bad id characters", _set(("presets", 1, "id"), "has space"), "presets[1].id"),
    ("id too long", _set(("presets", 1, "id"), "x" * 41), "presets[1].id"),
    ("duplicate id", _set(("presets", 2, "id"), "p1"), "presets[2].id"),
    ("empty name", _set(("presets", 0, "name"), "   "), "presets[0].name"),
    ("name too long", _set(("presets", 0, "name"), "n" * 41), "presets[0].name"),
    ("duplicate name ignoring case", _set(("presets", 2, "name"), "PRESET 1"), "presets[2].name"),
    ("active preset that does not exist", _set(("activeId",), "ghost"), "activeId"),
    ("volume above 1", _set(("fx", "volume"), 1.2), "fx.volume"),
    ("volume below 0", _set(("fx", "volume"), -0.1), "fx.volume"),
    ("sound not a boolean", _set(("fx", "sound"), "yes"), "fx.sound"),
    ("tick unknown", _set(("fx", "tick"), "loud"), "fx.tick"),
    ("motion unknown", _set(("fx", "motion"), "wild"), "fx.motion"),
    ("presets not a list", _set(("presets",), {}), "presets"),
    ("preset not an object", _set(("presets", 0), "x"), "presets[0]"),
    ("preset field missing", _drop(("presets", 1, "room")), "presets[1].room"),
    ("document field missing", _drop(("fx",)), "fx"),
    ("unknown key in the document", _set(("owner",), "x"), "owner"),
    ("version not a number", _set(("version",), "3"), "version"),
    ("unknown key in a preset", _set(("presets", 0, "color"), "red"), "presets[0].color"),
    ("unknown key in league", _league(0, flavour="x"), "presets[0].league.flavour"),
    ("unknown key in fx", _set(("fx", "echo"), True), "fx.echo"),
]


@pytest.mark.parametrize(("label", "mutate", "path"), VALIDATION, ids=[v[0] for v in VALIDATION])
def test_validation_names_the_field(
    tmp_path: Path, label: str, mutate: Callable[[dict[str, Any]], None], path: str
) -> None:
    api = Api(tmp_path)
    r = api.put(_with(mutate))
    assert r.status_code == 422, label
    problem = r.json()
    assert problem["field"] == path
    assert problem["type"] == "/problems/invalid-draft-settings"
    assert api.call("GET").json()["version"] == 0  # nothing saved


def test_validation_runs_before_the_stale_check(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.put(doc(preset(1)))
    assert api.put(_with(_league(0, teams=3)), '"draft-v0"').status_code == 422


def test_validation_document_is_not_an_object(tmp_path: Path) -> None:
    r = Api(tmp_path).put([1, 2])
    assert r.status_code == 422
    assert r.json()["field"] == ""


def test_validation_accepts_the_boundaries(tmp_path: Path) -> None:
    api = Api(tmp_path)
    edge = doc(
        preset(1, teams=4, seat=4, spots=5, budget=50),
        preset(2, teams=20, seat=1, spots=25, budget=1000, categories=["pts", "reb", "tov"]),
    )
    edge["presets"][1]["strategy"]["punt"] = "tov"
    edge["presets"][1]["room"].update(nominateSeconds=5, bidSeconds=120)
    edge["fx"].update(volume=0, sound=False, tick="off", motion="reduced")
    edge["presets"][0]["season"] = "2025-26"
    assert api.put(edge).status_code == 200


def test_validation_normalises_names_and_times(tmp_path: Path) -> None:
    api = Api(tmp_path)
    body = doc(preset(1))
    body["presets"][0]["name"] = "  Spaced  "
    body["presets"][0]["updatedAt"] = "2026-10-04T19:00:00+10:00"
    saved = api.put(body).json()["presets"][0]
    assert saved["name"] == "Spaced"
    assert saved["updatedAt"] == "2026-10-04T09:00:00Z"


def test_limits_ten_presets_and_not_eleven(tmp_path: Path) -> None:
    api = Api(tmp_path)
    ten = doc(*(preset(i) for i in range(10)))
    assert api.put(ten).status_code == 200
    eleven = doc(*(preset(i) for i in range(11)))
    r = api.put(eleven, '"draft-v1"')
    assert r.status_code == 422
    assert r.json()["field"] == "presets"


def test_limits_a_body_over_16_kb_is_413(tmp_path: Path) -> None:
    api = Api(tmp_path)
    big = doc(preset(1))
    big["presets"][0]["name"] = "x" * 20_000
    r = api.put(big)
    assert r.status_code == 413
    assert r.json()["type"] == "/problems/too-large"
    streamed = api.call(
        "PUT",
        content=iter([b" " * 10_000, b" " * 10_000]),  # no Content-Length: the stream is capped
        headers={"If-Match": '"draft-v0"'},
    )
    assert streamed.status_code == 413
    assert api.call("GET").json()["version"] == 0


def test_limits_ten_full_presets_fit_in_16_kb(tmp_path: Path) -> None:
    import json  # noqa: PLC0415

    full = doc(*(preset(i) for i in range(10)))
    for p in full["presets"]:
        p["name"] = f"{p['name']} " + "n" * 30
        p["league"]["categories"] = [
            "pts",
            "reb",
            "ast",
            "stl",
            "blk",
            "fg3m",
            "fg_pct",
            "ft_pct",
            "tov",
        ]
    assert len(json.dumps(full)) < draft_settings.MAX_BODY_BYTES
    assert Api(tmp_path).put(full).status_code == 200


UNSUPPORTED: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    (
        "points scoring",
        _league(0, scoring="h2h_points", weights={"pts": 1}),
        "presets[0].league.scoring",
    ),
    ("rotisserie", _league(0, scoring="rotisserie"), "presets[0].league.scoring"),
    ("snake drafting", _league(1, drafting="snake", budget=None), "presets[1].league.drafting"),
    ("weights on a category format", _league(0, weights={"pts": 1}), "presets[0].league.weights"),
]


@pytest.mark.parametrize(("label", "mutate", "path"), UNSUPPORTED, ids=[u[0] for u in UNSUPPORTED])
def test_unsupported_format_is_a_well_formed_422(
    tmp_path: Path, label: str, mutate: Callable[[dict[str, Any]], None], path: str
) -> None:
    r = Api(tmp_path).put(_with(mutate))
    assert r.status_code == 422, label
    assert r.json()["type"] == "/problems/unsupported-format"
    assert r.json()["field"] == path


def test_unsupported_points_format_without_weights_is_invalid_not_unsupported(
    tmp_path: Path,
) -> None:
    r = Api(tmp_path).put(_with(_league(0, scoring="h2h_points")))
    assert r.json()["type"] == "/problems/invalid-draft-settings"
    assert r.json()["field"] == "presets[0].league.weights"


# ---------- AC6: the format gate is one constant ----------
def test_supported_constant_is_the_only_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    points_snake = doc(preset(1, scoring="h2h_points", drafting="snake", budget=None))
    points_snake["presets"][0]["league"]["weights"] = {"pts": 1, "reb": 1.2, "tov": -1}
    api = Api(tmp_path)
    assert api.put(points_snake).status_code == 422
    monkeypatch.setattr(
        draft_settings,
        "SUPPORTED_COMBINATIONS",
        {*draft_settings.SUPPORTED_COMBINATIONS, (ScoringFormat.H2H_POINTS, "snake")},
    )
    ok = api.put(points_snake)
    assert ok.status_code == 200
    assert ok.json()["presets"][0]["league"]["weights"] == {"pts": 1, "reb": 1.2, "tov": -1}
    # the other rules still hold for the newly allowed combination
    no_weights = _with(_set(("presets", 0, "league", "weights"), {"pts": 0}), points_snake)
    assert api.put(no_weights, '"draft-v1"').json()["field"] == "presets[0].league.weights"
    categories_on_points = _with(_league(0, categories=["pts"]), points_snake)
    r = api.put(categories_on_points, '"draft-v1"')
    assert r.json()["type"] == "/problems/unsupported-format"


# ---------- AC4: delete, export, isolation ----------
def test_isolation_between_users(tmp_path: Path) -> None:
    api = Api(tmp_path)
    assert api.put(doc(preset(1), active="p1")).status_code == 200
    other = api.call("GET", token="second")
    assert other.json()["presets"] == []
    assert other.json()["version"] == 0
    assert api.put(doc(preset(9)), '"draft-v0"', token="second").status_code == 200
    assert [p["id"] for p in api.call("GET").json()["presets"]] == ["p1"]
    assert [p["id"] for p in api.call("GET", token="second").json()["presets"]] == ["p9"]


def test_export_includes_the_draft_settings(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.put(doc(preset(1), active="p1"))
    exported = api.call("GET", "/me/export").json()
    assert exported["draftSettings"]["activeId"] == "p1"
    assert exported["draftSettings"]["version"] == 1
    assert exported["draftSettings"]["presets"][0]["name"] == "Preset 1"
    empty = api.call("GET", "/me/export", token="second").json()
    assert empty["draftSettings"]["version"] == 0


def test_delete_account_removes_the_draft_settings(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.put(doc(preset(1)), token="second")
    assert api.store.get_draft_settings("uid-second") is not None
    assert api.call("DELETE", "/me", token="second").status_code == 204
    assert api.store.get_draft_settings("uid-second") is None
    assert api.store.get_draft_settings("uid-owner") is None


def test_put_accepts_the_document_exactly_as_get_returned_it(tmp_path: Path) -> None:
    api = Api(tmp_path)
    api.put(doc(preset(1), active="p1"))
    got = api.call("GET")
    again = api.put(got.json(), got.headers["etag"])
    assert again.status_code == 200
    assert again.json()["version"] == 2  # the server assigns it; the body's 1 was ignored
