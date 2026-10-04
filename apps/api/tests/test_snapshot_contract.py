"""The API reads exactly what the pipeline publishes (D-62): a snapshot built by the pipeline's own
`compose` must serve through every view."""

import importlib.util
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from types import ModuleType

from fastapi.testclient import TestClient

from fantasy_pipeline import daily_brief as db

TESTS = Path(__file__).parents[2] / "pipeline" / "tests" / "test_daily_brief.py"


def _pipeline_fixtures() -> ModuleType:  # the pipeline test's sample tables
    spec = importlib.util.spec_from_file_location("pipeline_brief_fixtures", TESTS)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_pipeline_snapshot_serves_through_every_view(
    client_for: Callable[[Path], TestClient], tmp_path: Path
) -> None:
    fx = _pipeline_fixtures()
    league_file = tmp_path / "league.json"
    league_file.write_text(
        json.dumps(db.sample_league(fx._values(), teams=4, rounds=5, opp=2)), encoding="utf-8"
    )
    league = db.load_league(league_file, fx._week())
    snap = db.compose(fx._week(), fx._values(), league, fx.SLOTS, date(2026, 10, 20)).snapshot
    snap["generated_at"] = "2026-10-20T20:30:00+00:00"
    (tmp_path / "briefs").mkdir()
    (tmp_path / "briefs" / "2026-10-20.json").write_text(json.dumps(snap), encoding="utf-8")
    client = client_for(tmp_path)
    for route in ("/today", "/matchup", "/waivers"):
        assert client.get(route).status_code == 200, route
