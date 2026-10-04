import copy
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
import pytest

from dikit import jobs
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import nba_cdn, nba_stats
from fantasy_pipeline import draft_publish, jobs_nba, week_projection, workspace

FIX = Path(__file__).parents[3] / "packages" / "ingest" / "tests" / "fixtures"
NOW = datetime(2026, 10, 21, 20, tzinfo=UTC)  # 21 Oct, 4 PM ET


def _schedule() -> bytes:
    s = json.loads(
        (FIX / "nba_cdn" / "cdn_schedule_league_v2_sample.json").read_text(encoding="utf-8")
    )
    s = copy.deepcopy(s)
    for g in s["leagueSchedule"]["gameDates"][0]["games"]:
        g["gameStatus"] = 3
    return json.dumps(s).encode()


class Client:
    def __init__(self) -> None:
        self.closed = False

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        if url == nba_cdn.SCHEDULE_URL:
            return _schedule()
        if "boxscore" in url:
            return (FIX / "nba_cdn" / "cdn_boxscore_sample.json").read_bytes()
        rs = {"name": "LeagueGameLog", "headers": ["GAME_ID"], "rowSet": []}
        return json.dumps({"resultSets": [rs]}).encode()

    def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
        return None

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def ctx(tmp_path: Path) -> jobs_nba.Context:
    store = SnapshotStore(f"memory://{uuid.uuid4().hex}")
    roster = (FIX / "nba_stats" / "team_roster_BOS_2026_27.json").read_bytes()
    req = nba_stats.common_team_roster(1610612738, "2026-27")
    store.write(nba_stats.SOURCE, req.endpoint, req.key, roster, NOW)
    work = workspace.Workspace(str(tmp_path / "work"))  # never the real data/ folder
    work.write_parquet(
        week_projection.PROJECTIONS,
        pl.DataFrame({"nba_player_id": [1641759], "stat": ["games"], "mean": [82.0]}),
    )
    return jobs_nba.Context(
        store,
        FrozenClock(NOW),
        "2026-27",
        Client,
        Client,
        Client,
        None,
        jobs_nba.LEAGUE_SETTINGS,
        work=work,
    )


def test_the_morning_chain_runs_in_order_and_is_logged(ctx: jobs_nba.Context) -> None:
    sink = jobs.MemorySink()
    results = jobs.Runner(jobs_nba.registry(ctx), sink, ctx.clock).run(
        list(jobs_nba.DAILY_TARGETS), partitions=[date(2026, 10, 20)]
    )
    ctx.close()
    order = [r.job for r in results]
    assert order == [
        "cdn-day",
        "game-logs",
        "injury-report",
        "week-projection",
        "brief",
        "send-brief",
        "publish",
        "draft-values",
        "season-replay",
    ]
    assert jobs.overall(results) == "success"
    by = {r.job: r.rows for r in results}
    assert by["cdn-day"] == 3  # three final games on 20 Oct in the sample
    assert by["week-projection"] == 21  # the BOS roster
    assert by["brief"] == 0  # no league file yet: by design
    assert by["send-brief"] == 0
    assert by["publish"] == 0  # no serve root configured
    assert by["draft-values"] == 0  # no warehouse configured
    assert by["season-replay"] == 0  # no warehouse configured


def test_catch_up_fetches_each_missed_day(ctx: jobs_nba.Context) -> None:
    sink = jobs.MemorySink()
    runner = jobs.Runner(jobs_nba.registry(ctx), sink, ctx.clock)
    runner.run(["cdn-day"], partitions=[date(2026, 10, 17)])
    missing = jobs.missing_partitions(sink, "cdn-day", through=date(2026, 10, 20), max_days=14)
    assert missing == [date(2026, 10, 18), date(2026, 10, 19), date(2026, 10, 20)]
    results = runner.run(list(jobs_nba.DAILY_TARGETS), partitions=missing)
    assert [r.partition for r in results if r.job == "cdn-day"] == missing


def test_the_cloud_registry_leaves_out_the_nba_fetch(ctx: jobs_nba.Context) -> None:
    sink = jobs.MemorySink()
    results = jobs.Runner(jobs_nba.registry(ctx, include_fetch=False), sink, ctx.clock).run(
        list(jobs_nba.CLOUD_TARGETS), partitions=[]
    )
    ctx.close()
    ran = {r.job for r in results}
    assert not ran & set(jobs_nba.FETCH_TARGETS)
    assert {
        "injury-report",
        "week-projection",
        "brief",
        "send-brief",
        "publish",
        "draft-values",
    } <= ran


def test_draft_values_runs_independently_and_a_refusal_never_blocks_the_brief(
    ctx: jobs_nba.Context, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_: object, **__: object) -> int:
        raise draft_publish.PublishRefusedError("missing variants: ['punt_ast']")

    monkeypatch.setattr(draft_publish, "run_job", refuse)
    ctx.make_warehouse = object
    settings = FIX / "yahoo_import" / "league_settings_h2h9cat_auction.txt"
    ctx.work.write_text(ctx.settings, settings.read_text(encoding="utf-8"))
    sink = jobs.MemorySink()
    results = jobs.Runner(jobs_nba.registry(ctx, include_fetch=False), sink, ctx.clock).run(
        list(jobs_nba.CLOUD_TARGETS), partitions=[]
    )
    ctx.close()
    by = {r.job: r.status for r in results}
    assert by["draft-values"] == "degraded"  # optional: logged and alerted, not fatal
    assert by["send-brief"] != "failed"
    assert by["brief"] != "failed"
