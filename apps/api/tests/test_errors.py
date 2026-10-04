from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient

from fantasy_api.errors import PROBLEM_BASE


def test_unknown_route_is_problem_json(
    client_for: Callable[[Path], TestClient], tmp_path: Path
) -> None:
    r = client_for(tmp_path).get("/nope")
    assert r.status_code == 404
    assert r.headers["content-type"].startswith("application/problem+json")
    body = r.json()
    assert body["type"] == f"{PROBLEM_BASE}/not-found"
    assert body["status"] == 404


def test_unexpected_errors_hide_the_stack_trace(
    client_for: Callable[[Path], TestClient], tmp_path: Path
) -> None:
    (tmp_path / "ops").mkdir()
    (tmp_path / "ops" / "job_runs.jsonl").write_text("{not json\n", encoding="utf-8")
    r = client_for(tmp_path).get("/system/freshness")
    assert r.status_code == 500
    body = r.json()
    assert body["type"] == f"{PROBLEM_BASE}/internal"
    assert "Traceback" not in r.text
    assert "JSONDecodeError" not in r.text
