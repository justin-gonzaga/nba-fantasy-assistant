from datetime import date
from pathlib import Path

from fantasy_pipeline import publish
from fantasy_pipeline.workspace import Workspace


def _local(root: Path) -> None:
    for rel, text in {
        "briefs/2026-10-21.json": "{}",
        "briefs/2026-10-21.md": "*brief*",
        "briefs/2026-10-20.json": "{}",  # an older day: not re-sent
        "predictions/week_projection.parquet": "pq",
        "ops/job_runs.jsonl": "{}\n",
    }.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")


def test_publishes_the_days_files_in_the_api_layout(tmp_path: Path) -> None:
    local, serve = tmp_path / "data", tmp_path / "serve"
    _local(local)
    n = publish.publish(Workspace(str(local)), str(serve), date(2026, 10, 21))
    assert n == 4  # the draft files are absent here: skipped
    assert (serve / "briefs" / "2026-10-21.json").read_text(encoding="utf-8") == "{}"
    assert (serve / "predictions" / "week_projection.parquet").exists()
    assert (serve / "ops" / "job_runs.jsonl").exists()
    assert not (serve / "briefs" / "2026-10-20.json").exists()


def test_missing_files_are_skipped(tmp_path: Path) -> None:
    local = tmp_path / "data"
    (local / "ops").mkdir(parents=True)
    (local / "ops" / "job_runs.jsonl").write_text("{}\n", encoding="utf-8")
    assert publish.publish(Workspace(str(local)), str(tmp_path / "serve"), date(2026, 10, 21)) == 1


def test_draft_files_are_published_when_present(tmp_path: Path) -> None:
    local = tmp_path / "data"
    for rel in ("predictions/auction_values.parquet", "predictions/player_history.parquet"):
        (local / rel).parent.mkdir(parents=True, exist_ok=True)
        (local / rel).write_text("pq", encoding="utf-8")
    assert publish.publish(Workspace(str(local)), str(tmp_path / "serve"), date(2026, 10, 21)) == 2
    assert (tmp_path / "serve" / "predictions" / "player_history.parquet").exists()
