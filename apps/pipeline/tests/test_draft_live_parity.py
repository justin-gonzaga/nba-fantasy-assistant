"""Parity: the page's JavaScript helper gives the same numbers as the Python reference."""

import json
import random
import shutil
import subprocess
from pathlib import Path

import pytest

from fantasy_models import draft_live as dl

JS = Path(__file__).parents[1] / "src" / "fantasy_pipeline" / "draft_live.js"
NODE = shutil.which("node")
TEAMS = [f"T{i}" for i in range(1, 17)]


@pytest.mark.skipif(NODE is None, reason="node not installed")
def test_js_matches_python_through_a_draft() -> None:
    rng = random.Random(7)
    players = [
        {
            "id": str(i),
            "usd": max(1.0, round(28 - i * 0.12, 1)),
            "z": [round(rng.gauss(0.3 - i / 300, 0.8), 2) for _ in range(9)],
        }
        for i in range(260)
    ]
    picks: list[dict[str, object]] = []
    # two rosters finished early (one with leftover cash) to cover the dead-money rule
    for k in range(14):
        picks.append({"pid": str(200 + k), "team": "T2", "price": 1})
        picks.append({"pid": str(230 + k), "team": "T3", "price": 14})
    for k in range(40):
        pid = str(rng.randrange(260))
        if any(p["pid"] == pid for p in picks):
            continue
        team = TEAMS[4 + k % 12]
        picks.append({"pid": pid, "team": team, "price": rng.randint(1, 30)})
    case = {
        "players": players,
        "picks": picks,
        "teams": TEAMS,
        "me": "T1",
        "budget": 200,
        "slots": 14,
        "punted": [8],
    }
    script = (
        f"const L = require({json.dumps(str(JS))});"
        "const c = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
        "const a = L.advise(c.players, c.picks, c.teams, c.me, c.budget, c.slots,"
        " new Set(c.punted));"
        "process.stdout.write(JSON.stringify(a));"
    )
    out = subprocess.run(
        [NODE or "node", "-e", script],
        input=json.dumps(case),
        capture_output=True,
        text=True,
        check=True,
    )
    js = json.loads(out.stdout)
    py = dl.advise(players, picks, TEAMS, "T1", 200, 14, {8})
    assert js["inflation"] == pytest.approx(py["inflation"], abs=1e-9)
    assert js["weights"] == pytest.approx(py["weights"], abs=1e-9)
    assert js["my_max_bid"] == py["my_max_bid"]
    assert js["targets"] == py["targets"]
    assert js["hints"] == py["hints"]
    for pid, row in py["players"].items():
        assert js["players"][pid]["ceiling"] == row["ceiling"]
        assert js["players"][pid]["fit"] == pytest.approx(row["fit"], abs=1e-9)
