import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

from dikit import jobs
from fantasy_pipeline import workspace as ws


@pytest.fixture(params=["local", "memory"])
def root(request: pytest.FixtureRequest, tmp_path: Path) -> str:
    return str(tmp_path / "work") if request.param == "local" else f"memory://{uuid.uuid4().hex}"


def test_text_and_parquet_round_trip_under_the_root(root: str) -> None:
    w = ws.Workspace(root)
    assert not w.exists("league/league.json")
    w.write_text("league/league.json", '{"my_team": []}')
    assert w.exists("league/league.json")
    assert w.read_text("league/league.json") == '{"my_team": []}'
    df = pl.DataFrame({"nba_player_id": [1, 2], "pts": [10.0, 20.0]})
    w.write_parquet("predictions/week_projection.parquet", df)
    assert w.read_parquet("predictions/week_projection.parquet").equals(df)
    assert w.url("briefs/2026-10-20.md").endswith("/briefs/2026-10-20.md")


def test_the_run_log_sink_appends_and_reads_back(root: str) -> None:
    w = ws.Workspace(root)
    sink = ws.RunLogSink(w, "ops/job_runs.jsonl")
    for job in ("brief", "send-brief"):
        sink.write(
            jobs.JobResult(
                run_id="r1",
                job=job,
                partition=date(2026, 10, 20),
                status="success",
                rows=1,
                seconds=0.1,
                started_at=datetime(2026, 10, 20, 20, 30, tzinfo=UTC),
            )
        )
    history = sink.history()
    assert [r.job for r in history] == ["brief", "send-brief"]
    assert history[0].partition == date(2026, 10, 20)


def test_the_default_workspace_follows_settings_and_can_be_switched(tmp_path: Path) -> None:
    ws.use(str(tmp_path))
    try:
        assert ws.get().root == str(tmp_path)
    finally:
        ws.use(None)
