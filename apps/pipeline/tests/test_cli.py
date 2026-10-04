import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dikit import jobs
from fantasy_pipeline import cli, jobs_nba, workspace

FIX = Path(__file__).parents[3] / "packages" / "ingest" / "tests" / "fixtures" / "nba_stats"


class FixtureClient:
    def __init__(self) -> None:
        self.closed = False

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        endpoint = url.rsplit("/", 1)[-1]
        if endpoint == "drafthistory":
            return json.dumps(
                {"resultSets": [{"name": "DraftHistory", "headers": ["PERSON_ID"], "rowSet": []}]}
            ).encode()
        name = {
            "leaguegamelog": "player_game_logs_2025_26.json",
            "leaguedashplayerstats": "league_dash_player_stats_2025_26.json",
            "commonteamroster": "team_roster_BOS_2026_27.json",
        }[endpoint]
        return (FIX / name).read_bytes()

    def close(self) -> None:
        self.closed = True


def test_draft_pool_backfill_and_coverage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    client = FixtureClient()
    monkeypatch.setattr(cli, "make_client", lambda: client)
    runner = CliRunner()
    args = ["draft-pool", "--root", str(tmp_path), "--first", "2025-26", "--last", "2025-26"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    assert "fetched=34 skipped=0" in result.output
    assert client.closed
    again = runner.invoke(cli.app, args)
    assert "fetched=0 skipped=34" in again.output

    cov = runner.invoke(
        cli.app,
        ["draft-pool-coverage", "--root", str(tmp_path), "--first", "2025-26", "--last", "2025-26"],
    )
    assert cov.exit_code == 0, cov.output
    assert "coverage=" in cov.output


def test_nba_daily_refresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cdn_fix = FIX.parent / "nba_cdn"

    class Cdn(FixtureClient):
        def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
            name = (
                "cdn_schedule_league_v2_sample.json"
                if "schedule" in url
                else "cdn_boxscore_sample.json"
            )
            return (cdn_fix / name).read_bytes()

    cdn, stats = Cdn(), FixtureClient()
    monkeypatch.setattr(cli, "make_cdn_client", lambda: cdn)
    monkeypatch.setattr(cli, "make_client", lambda: stats)

    class NoReports(FixtureClient):
        def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
            return None

    injuries = NoReports()
    monkeypatch.setattr(cli, "make_injury_client", lambda: injuries)
    args = ["nba-daily", "--root", str(tmp_path), "--day", "2026-10-20"]
    result = CliRunner().invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    # The fixture's games are scheduled (not final), so no box scores yet.
    assert (
        "day=2026-10-20 schedule_games=3 box_scores fetched=0 skipped=0 "
        "game_logs fetched=2 injury_rows=no new report" in result.output
    )
    assert cdn.closed
    assert stats.closed


class _Ctx:
    def close(self) -> None:
        pass


def _fake_registry(fail: bool) -> Callable[[object], jobs.Registry]:
    def build(_ctx: object, *, include_fetch: bool = True) -> jobs.Registry:
        def ok(_p: object) -> int:
            return 1

        def boom(_p: object) -> int:
            raise RuntimeError("source down")

        reg = jobs.Registry()
        if include_fetch:
            reg.add(jobs.Job("cdn-day", boom if fail else ok, partitioned=True))
            reg.add(jobs.Job("game-logs", ok))
        fetched = ("cdn-day", "game-logs") if include_fetch else ()
        reg.add(jobs.Job("injury-report", ok, optional=True))
        reg.add(jobs.Job("week-projection", ok, deps=(*fetched, "injury-report")))
        reg.add(jobs.Job("brief", ok, deps=("week-projection",)))
        reg.add(jobs.Job("send-brief", ok, deps=("brief",)))
        reg.add(jobs.Job("publish", ok, deps=("brief",), optional=True))
        reg.add(jobs.Job("draft-values", ok, optional=True))
        reg.add(jobs.Job("season-replay", ok, optional=True))
        return reg

    return build


@pytest.fixture
def runner_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(jobs_nba, "LOCK", tmp_path / "run.lock")
    monkeypatch.setattr(workspace, "_current", workspace.Workspace(str(tmp_path)))
    monkeypatch.setattr(jobs_nba, "RUNS", "runs.jsonl")
    monkeypatch.setattr(cli, "_runner_context", lambda _root, _clock: _Ctx())
    return tmp_path


def test_daily_run_uses_the_runner_logs_results_and_releases_the_lock(
    runner_paths: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs_nba, "registry", _fake_registry(fail=False))
    result = CliRunner().invoke(cli.app, ["daily-run"])
    assert result.exit_code == 0, result.output
    assert "send-brief: success" in result.output
    assert (
        len((runner_paths / "runs.jsonl").read_text(encoding="utf-8").splitlines()) == 9
    )  # six chain jobs + publish + draft-values (DATA-035) + season-replay (SIM-001)
    assert not (runner_paths / "run.lock").exists()


def test_daily_run_alerts_and_fails_when_a_job_fails(
    runner_paths: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    alerts: list[str] = []
    monkeypatch.setattr(jobs_nba, "registry", _fake_registry(fail=True))
    monkeypatch.setattr(cli, "_alert", alerts.append)
    result = CliRunner().invoke(cli.app, ["daily-run"])
    assert result.exit_code == 1
    assert "week-projection: skipped" in result.output
    assert alerts == [
        "Daily run failed (cdn-day). Logs: data/logs/daily-run.log on the PC, or the Cloud Run job."
    ]


def test_run_fetch_runs_only_the_nba_fetch(
    runner_paths: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs_nba, "registry", _fake_registry(fail=False))
    result = CliRunner().invoke(cli.app, ["run", "fetch"])
    assert result.exit_code == 0, result.output
    assert "game-logs: success" in result.output
    assert "brief" not in result.output


def test_run_cloud_runs_the_rest_without_the_fetch(
    runner_paths: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs_nba, "registry", _fake_registry(fail=False))
    result = CliRunner().invoke(cli.app, ["run", "cloud"])
    assert result.exit_code == 0, result.output
    assert "send-brief: success" in result.output
    assert "cdn-day" not in result.output
    assert "game-logs" not in result.output


def test_run_named_jobs_over_a_date_range(
    runner_paths: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs_nba, "registry", _fake_registry(fail=False))
    result = CliRunner().invoke(
        cli.app, ["run", "cdn-day", "--start", "2026-10-20", "--end", "2026-10-22"]
    )
    assert result.exit_code == 0, result.output
    assert result.output.count("cdn-day 2026-10-2") == 3
