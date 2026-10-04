"""DRAFT-013 AC3: the web room's TypeScript port must match the Python helper.

This test owns `apps/web/src/features/draft/fixtures/advise-parity.json`: it rebuilds the case,
runs the reference engine and checks the committed expectations, which `draftRoom.test.ts`
replays in TypeScript. Regenerate with `REGEN_PARITY=1 uv run pytest <this file>`.
"""

import json
import os
import random
from pathlib import Path
from typing import Any

from fantasy_models import draft_live as dl

WEB = Path(__file__).parents[2] / "web"
FIXTURE = WEB / "src" / "features" / "draft" / "fixtures" / "advise-parity.json"
TEAMS = [f"T{i}" for i in range(1, 17)]


def _case() -> dict[str, Any]:
    rng = random.Random(11)
    players = [
        {
            "id": str(i),
            "usd": max(1.0, round(60 - i * 0.25, 1)),
            "z": [round(rng.gauss(0.4 - i / 250, 0.8), 2) for _ in range(9)],
        }
        for i in range(240)
    ]
    picks: list[dict[str, Any]] = []
    for k in range(14):  # a finished roster with cash left: the dead-money rule
        picks.append({"pid": str(200 + k), "team": "T3", "price": 3})
    for k in range(60):
        pid = str(rng.randrange(200))
        if any(p["pid"] == pid for p in picks):
            continue
        picks.append({"pid": pid, "team": TEAMS[k % 16], "price": rng.randint(1, 40)})
    return {
        "players": players,
        "picks": picks,
        "teams": TEAMS,
        "me": "T1",
        "budget": 200,
        "slots": 14,
        "punted": [7],
    }


def _expected(case: dict[str, Any]) -> dict[str, Any]:
    a = dl.advise(
        case["players"],
        case["picks"],
        case["teams"],
        case["me"],
        case["budget"],
        case["slots"],
        set(case["punted"]),
    )
    return {
        "inflation": a["inflation"],
        "weights": a["weights"],
        "my_max_bid": a["my_max_bid"],
        "targets": a["targets"],
        "hints": a["hints"],
        "players": {
            pid: {"adj": r["adj"], "fit": r["fit"], "ceiling": r["ceiling"]}
            for pid, r in a["players"].items()
        },
        "teams": {
            t: {"left": s["left"], "open": s["open"], "max_bid": s["max_bid"]}
            for t, s in a["teams"].items()
        },
    }


def test_parity_fixture_matches_the_python_engine() -> None:
    case = _case()
    expected = _expected(case)
    if os.environ.get("REGEN_PARITY"):
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps({"case": case, "expected": expected}), encoding="utf-8")
    saved = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert saved["case"] == case
    assert saved["expected"] == json.loads(json.dumps(expected))
