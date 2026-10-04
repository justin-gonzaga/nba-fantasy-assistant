import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from dikit.errors import SourceUnavailable
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import nba_stats
from fantasy_ingest.draft_pool import coverage, plan, run

FIX = Path(__file__).parent / "fixtures" / "nba_stats"
T0 = datetime(2026, 9, 25, 4, 0, tzinfo=UTC)


def _fixture(name: str) -> bytes:
    return (FIX / name).read_bytes()


def _payload(result_set: str, headers: list[str], rows: list[list[object]]) -> bytes:
    return json.dumps(
        {"resultSets": [{"name": result_set, "headers": headers, "rowSet": rows}]}
    ).encode()


class FakeClient:
    """Serves fixture payloads by endpoint; can fail after N calls to simulate an interrupt."""

    source = "nba_stats"

    def __init__(
        self, fail_after: int | None = None, bodies: Mapping[str, bytes] | None = None
    ) -> None:
        self.calls: list[str] = []
        self.fail_after = fail_after
        self.bodies = bodies or {}

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        if self.fail_after is not None and len(self.calls) >= self.fail_after:
            raise SourceUnavailable("nba_stats", "simulated interrupt")
        self.calls.append(url)
        endpoint = url.rsplit("/", 1)[-1]
        if endpoint in self.bodies:
            return self.bodies[endpoint]
        return {
            "leaguegamelog": _fixture("player_game_logs_2025_26.json"),
            "leaguedashplayerstats": _fixture("league_dash_player_stats_2025_26.json"),
            "commonteamroster": _fixture("team_roster_BOS_2026_27.json"),
            "drafthistory": _payload(
                "DraftHistory", ["PERSON_ID", "SEASON", "OVERALL_PICK"], [[1, "2026", 1]]
            ),
        }[endpoint]


def _store() -> SnapshotStore:
    return SnapshotStore(f"memory://{uuid.uuid4().hex}")


def test_seasons_range() -> None:
    s = nba_stats.seasons("2015-16", "2025-26")
    assert s[0] == "2015-16"
    assert s[-1] == "2025-26"
    assert len(s) == 11
    with pytest.raises(ValueError, match="season"):
        nba_stats.seasons("2015-2016", "2025-26")


def test_request_params_match_the_verified_fixtures() -> None:
    fixture = json.loads(_fixture("player_game_logs_2025_26.json"))
    req = nba_stats.league_game_log("2025-26", "P")
    assert req.url == "https://stats.nba.com/stats/leaguegamelog"
    assert req.params == {k: str(v) for k, v in fixture["parameters"].items()}
    roster = json.loads(_fixture("team_roster_BOS_2026_27.json"))
    assert nba_stats.common_team_roster(1610612738, "2026-27").params == {
        k: str(v) for k, v in roster["parameters"].items()
    }
    dash = nba_stats.league_dash_player_stats("2025-26")
    assert dash.params["PerMode"] == "Totals"
    assert dash.params["Season"] == "2025-26"
    # the server echoes unset filters as "None" but rejects a literal "None" with HTTP 500
    assert "None" not in dash.params.values()
    assert dash.params["PORound"] == ""


def test_team_ids_are_the_30_franchises() -> None:
    assert len(nba_stats.TEAM_IDS) == 30
    assert 1610612738 in nba_stats.TEAM_IDS  # BOS


def test_row_count_reads_the_first_result_set() -> None:
    assert nba_stats.row_count(_fixture("team_roster_BOS_2026_27.json")) == 21


def test_row_count_rejects_non_stats_payload() -> None:
    from dikit.errors import ContractViolation  # noqa: PLC0415

    with pytest.raises(ContractViolation, match="resultSets"):
        nba_stats.row_count(b'{"message": "error"}')


def test_plan_covers_every_request_once() -> None:
    reqs = plan(nba_stats.seasons("2015-16", "2025-26"), roster_season="2026-27")
    assert len(reqs) == 11 * 2 + 11 + 30 + 1
    assert len({(r.endpoint, r.key) for r in reqs}) == len(reqs)


def test_run_stores_everything_then_resumes_without_refetching() -> None:
    store, clock = _store(), FrozenClock(T0)
    reqs = plan(["2025-26"], roster_season="2026-27")
    first = run(store, FakeClient(), reqs, clock)
    assert (first.fetched, first.skipped) == (len(reqs), 0)
    assert len(store.manifest("nba_stats")) == len(reqs)
    assert all(m["rows"] is not None for m in store.manifest("nba_stats"))
    clock.advance(timedelta(hours=1))
    client = FakeClient()
    second = run(store, client, reqs, clock)
    assert (second.fetched, second.skipped, client.calls) == (0, len(reqs), [])


def test_interrupted_run_resumes_where_it_stopped() -> None:
    store, clock = _store(), FrozenClock(T0)
    reqs = plan(["2025-26"], roster_season="2026-27")
    with pytest.raises(SourceUnavailable, match="interrupt"):
        run(store, FakeClient(fail_after=5), reqs, clock)
    clock.advance(timedelta(minutes=5))
    report = run(store, FakeClient(), reqs, clock)
    assert (report.skipped, report.fetched) == (5, len(reqs) - 5)


def test_coverage_lists_rostered_players_without_history() -> None:
    store, clock = _store(), FrozenClock(T0)
    roster = json.loads(_fixture("team_roster_BOS_2026_27.json"))
    head = roster["resultSets"][0]["headers"]
    rows = roster["resultSets"][0]["rowSet"]
    pid, name = head.index("PLAYER_ID"), head.index("PLAYER")
    rookie, unknown = rows[0], rows[1]
    logs = _payload(
        "LeagueGameLog",
        ["PLAYER_ID"],
        [[r[pid]] for r in rows if r[pid] not in {rookie[pid], unknown[pid]}],
    )
    draft = _payload("DraftHistory", ["PERSON_ID"], [[rookie[pid]]])
    client = FakeClient(bodies={"leaguegamelog": logs, "drafthistory": draft})
    run(store, client, plan(["2025-26"], roster_season="2026-27"), clock)
    cov = coverage(store, ["2025-26"], "2026-27")
    # every team uses the BOS fixture, so the same player ids repeat; coverage de-duplicates
    assert cov.rostered == len({r[pid] for r in rows})
    assert [m["PLAYER"] for m in cov.missing] == [unknown[name]]
    assert cov.pct == pytest.approx(100 * (cov.rostered - 1) / cov.rostered)


def test_refresh_fetches_again_as_a_new_snapshot() -> None:
    store, clock = _store(), FrozenClock(T0)
    reqs = plan(["2025-26"], roster_season="2026-27")
    run(store, FakeClient(), reqs, clock)
    clock.advance(timedelta(days=20))
    client = FakeClient()
    report = run(store, client, reqs, clock, refresh=frozenset({"commonteamroster"}))
    assert report.fetched == 30  # only the rosters
    assert all(u.endswith("commonteamroster") for u in client.calls)
    roster = nba_stats.common_team_roster(1610612738, "2026-27")
    metas = [m for m in store.manifest("nba_stats") if m["key"] == roster.key]
    assert len(metas) == 2  # the old snapshot is kept (immutable), the new one added
