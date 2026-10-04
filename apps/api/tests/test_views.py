import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from fantasy_api.errors import PROBLEM_BASE
from fantasy_api.views import explained_actions
from fantasy_decision import explain as ex

Client = Callable[[Path], TestClient]

CATS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fg_pct", "ft_pct")


def snapshot(day: str = "2026-10-21", schema: int = 1) -> dict[str, Any]:
    return {
        "schema": schema,
        "day": day,
        "week": {"start": "2026-10-19", "end": "2026-10-25"},
        "opponent_name": "Team 7",
        "outlook": dict(zip(CATS, [0.8, 0.3, 0.6, 0.5, 0.2, 0.7, 0.4, 0.65, 0.35], strict=True)),
        "totals": {
            "mine": dict(zip(CATS, [512.4, 201, 118, 34, 19, 58, 40, 0.4812, 0.7921], strict=True)),
            "theirs": dict(zip(CATS, [488, 214, 102, 31, 24, 49, 44, 0.466, 0.815], strict=True)),
        },
        "lineup": [
            {"player_id": 1, "name": "A Guard", "slot": "G", "reason": "plays"},
            {"player_id": 2, "name": "B Big", "slot": "BN", "reason": "no game today"},
        ],
        "injuries": [{"name": "C Wing", "status": "Questionable"}],
        "pickups": [
            {
                "add_id": 9,
                "add_name": "D Stream",
                "drop_id": 2,
                "drop_name": "B Big",
                "games_left": 3,
                "gain": 0.42,
                "helps": ["blk", "reb"],
            }
        ],
        "sources": [{"name": "week projection", "as_of": day}],
        "generated_at": f"{day}T20:30:00+00:00",
    }


def seed(root: Path, *snaps: dict[str, Any]) -> Path:
    (root / "briefs").mkdir(parents=True, exist_ok=True)
    for s in snaps:
        (root / "briefs" / f"{s['day']}.json").write_text(json.dumps(s), encoding="utf-8")
    return root


def test_matchup_serves_computed_numbers_and_nulls_the_rest(
    client_for: Client, tmp_path: Path
) -> None:
    body = client_for(seed(tmp_path, snapshot())).get("/matchup").json()
    assert body["opponent"] == "Team 7"
    assert body["weekStart"] == "2026-10-19"
    assert body["daysLeft"] == 5  # Wed 21 to Sun 25 inclusive
    assert body["expectedCategories"] == 4.5
    assert body["record"] is None  # not computed: never invented
    pts = body["categories"][0]
    assert pts == {"code": "PTS", "mine": "512", "theirs": "488", "winProb": 0.8, "note": None}
    fg = next(c for c in body["categories"] if c["code"] == "FG%")
    assert (fg["mine"], fg["theirs"]) == (".481", ".466")
    assert body["freshness"]["asOf"] == "2026-10-21T20:30:00Z"


def test_today_turns_the_brief_into_actions(client_for: Client, tmp_path: Path) -> None:
    body = client_for(seed(tmp_path, snapshot())).get("/today").json()
    assert body["date"] == "2026-10-21"
    kinds = [a["kind"] for a in body["actions"]]
    assert kinds == ["lineup", "injury", "stream"]
    stream = body["actions"][2]
    assert stream["title"] == "Add D Stream, drop B Big"
    assert stream["why"] == [
        "+0.42 expected categories this week",
        "3 games left",
        "Helps BLK, REB",
    ]
    assert stream["deadline"] is None
    assert stream["confidence"] is None


def test_waivers_list_the_pickups(client_for: Client, tmp_path: Path) -> None:
    body = client_for(seed(tmp_path, snapshot())).get("/waivers").json()
    (c,) = body["candidates"]
    assert c == {
        "id": "9",
        "name": "D Stream",
        "team": None,
        "positions": None,
        "gamesLeft": 3,
        "helps": ["BLK", "REB"],
        "gain": 0.42,
    }
    assert body["suggestedDrop"] == "B Big"
    assert body["horizon"] == "this week"  # snapshots before DEC-010 default to one week


def test_latest_snapshot_by_default_or_a_chosen_day(client_for: Client, tmp_path: Path) -> None:
    client = client_for(seed(tmp_path, snapshot("2026-10-20"), snapshot("2026-10-21")))
    assert client.get("/today").json()["date"] == "2026-10-21"
    assert client.get("/today", params={"day": "2026-10-20"}).json()["date"] == "2026-10-20"


def test_missing_and_unsupported_snapshots_are_problems(client_for: Client, tmp_path: Path) -> None:
    r = client_for(tmp_path).get("/today")
    assert r.status_code == 404
    assert r.json()["type"] == f"{PROBLEM_BASE}/no-brief"
    r = client_for(seed(tmp_path, snapshot(schema=99))).get("/matchup")
    assert r.status_code == 503
    assert r.json()["type"] == f"{PROBLEM_BASE}/snapshot-schema"


def test_an_invalid_day_is_a_422_problem(client_for: Client, tmp_path: Path) -> None:
    r = client_for(seed(tmp_path, snapshot())).get("/today", params={"day": "not-a-date"})
    assert r.status_code == 422
    assert r.json()["type"] == f"{PROBLEM_BASE}/invalid-request"


def test_every_number_in_the_actions_comes_from_the_snapshot() -> None:
    texts = [e for _, _, es in explained_actions(snapshot()) for e in es]
    assert texts
    assert [(e.text, ex.ungrounded(e)) for e in texts if ex.ungrounded(e)] == []


def test_freshness_carries_stale_since(client_for: Client, tmp_path: Path) -> None:
    stale = {**snapshot(), "stale_since": "2026-10-20"}
    for path in ("/today", "/matchup", "/waivers"):
        assert client_for(seed(tmp_path, stale)).get(path).json()["freshness"]["staleSince"] == (
            "2026-10-20"
        )
    fresh = client_for(seed(tmp_path / "fresh", snapshot())).get("/today").json()
    assert fresh["freshness"]["staleSince"] is None
