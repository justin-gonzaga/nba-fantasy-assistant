import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

import polars as pl
from fastapi.testclient import TestClient

import fantasy_api

Client = Callable[[Path], TestClient]


def test_health_reports_ok_and_version(client_for: Client, tmp_path: Path) -> None:
    r = client_for(tmp_path).get("/system/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": fantasy_api.__version__}


def test_freshness_reports_missing_products_without_failing(
    client_for: Client, tmp_path: Path
) -> None:
    r = client_for(tmp_path).get("/system/freshness")
    assert r.status_code == 200
    body = r.json()
    assert {p["name"]: p["asOf"] for p in body["products"]} == {
        "week_projection": None,
        "brief": None,
    }
    assert body["jobs"] == []


def _run(run_id: str, job: str, status: str, started_at: str) -> dict[str, object]:
    return {
        "run_id": run_id,
        "job": job,
        "partition": None,
        "status": status,
        "rows": 0,
        "seconds": 0.1,
        "started_at": started_at,
        "error": None,
    }


def _seed(root: Path) -> None:
    (root / "predictions").mkdir(parents=True)
    pl.DataFrame({"nba_player_id": [1], "as_of_day": [date(2026, 10, 21)]}).write_parquet(
        root / "predictions" / "week_projection.parquet"
    )
    (root / "briefs").mkdir()
    (root / "briefs" / "2026-10-20.md").write_text("old", encoding="utf-8")
    (root / "briefs" / "2026-10-21.md").write_text("new", encoding="utf-8")
    (root / "ops").mkdir()
    runs = [
        {
            "run_id": "a",
            "job": "brief",
            "partition": None,
            "status": "success",
            "rows": 1,
            "seconds": 0.1,
            "started_at": "2026-10-20T20:30:00+00:00",
            "error": None,
        },
        {
            "run_id": "b",
            "job": "brief",
            "partition": None,
            "status": "failed",
            "rows": 0,
            "seconds": 0.1,
            "started_at": "2026-10-21T20:30:00+00:00",
            "error": "boom",
        },
        _run("c", "send-brief", "failed", "2026-10-21T20:31:00+00:00"),  # never succeeded
        # by string this success sorts first; by instant (23:00Z) it is the later run
        _run("d", "tz", "success", "2026-10-21T19:00:00-04:00"),
        _run("e", "tz", "failed", "2026-10-21T22:00:00+00:00"),
    ]
    (root / "ops" / "job_runs.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in runs), encoding="utf-8"
    )


def test_freshness_reads_the_data_root(client_for: Client, tmp_path: Path) -> None:
    _seed(tmp_path)
    body = client_for(tmp_path).get("/system/freshness").json()
    products = {p["name"]: p["asOf"] for p in body["products"]}
    assert products == {"week_projection": "2026-10-21", "brief": "2026-10-21"}
    jobs = {j["job"]: j for j in body["jobs"]}
    assert jobs["brief"] == {
        "job": "brief",
        "lastStatus": "failed",
        "lastRun": "2026-10-21T20:30:00Z",
        "lastSuccess": "2026-10-20T20:30:00Z",
    }
    assert jobs["send-brief"]["lastSuccess"] is None
    assert jobs["tz"]["lastStatus"] == "success"  # ordered by instant, not by string
