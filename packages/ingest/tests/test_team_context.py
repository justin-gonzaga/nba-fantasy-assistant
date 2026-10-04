"""DATA-038: team and head-coach context (payload shapes as recorded live, 2026-10-03)."""

import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime

import pytest

from dikit.errors import ContractViolation
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock
from fantasy_ingest import draft_pool, nba_stats, team_context
from fantasy_ingest.nba_stats import SOURCE

COACH_HEADERS = [
    "TEAM_ID",
    "SEASON",
    "COACH_ID",
    "FIRST_NAME",
    "LAST_NAME",
    "COACH_NAME",
    "IS_ASSISTANT",
    "COACH_TYPE",
    "SORT_SEQUENCE",
    "SUB_SORT_SEQUENCE",
]
MIL = 1610612749


def roster(team: int, season: str, head: tuple[int, str]) -> bytes:
    coaches = [
        [team, season[:4], 999, "A", "Assistant", "A Assistant", 2, "Assistant Coach", None, 5],
        [team, season[:4], head[0], *head[1].split(" ", 1), head[1], 1, "Head Coach", None, 1],
    ]
    return json.dumps(
        {
            "resultSets": [
                {"name": "CommonTeamRoster", "headers": ["TeamID"], "rowSet": [[team]]},
                {"name": "Coaches", "headers": COACH_HEADERS, "rowSet": coaches},
            ]
        }
    ).encode()


def team_stats() -> bytes:
    headers = ["TEAM_ID", "TEAM_NAME", "OFF_RATING", "DEF_RATING", "PACE"]
    rows = [
        [t, f"T{t}", 110.0 + i % 5, 108.0, 98.0 + i % 7] for i, t in enumerate(nba_stats.TEAM_IDS)
    ]
    rs = {"name": "LeagueDashTeamStats", "headers": headers, "rowSet": rows}
    return json.dumps({"resultSets": [rs]}).encode()


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        self.calls.append(url)
        p = params or {}
        if url.endswith("commonteamroster"):
            return roster(int(p["TeamID"]), p["Season"], (1, "Mike Budenholzer"))
        return team_stats()


@pytest.fixture
def store() -> SnapshotStore:
    return SnapshotStore(f"memory://{uuid.uuid4().hex}")


def test_plan_covers_every_team_and_the_league_stats_each_season() -> None:
    reqs = team_context.plan(["2019-20", "2020-21"])
    assert len(reqs) == 2 * (30 + 1)
    assert {r.endpoint for r in reqs} == {"commonteamroster", "leaguedashteamstats"}
    adv = next(r for r in reqs if r.endpoint == "leaguedashteamstats")
    assert adv.params["MeasureType"] == "Advanced"
    assert adv.key == "season=2019-20/measure=advanced"


def test_backfill_stores_raw_and_resumes(store: SnapshotStore) -> None:
    clock = FrozenClock(datetime(2026, 10, 3, tzinfo=UTC))
    reqs = team_context.plan(["2019-20"])
    first = draft_pool.run(store, FakeClient(), reqs, clock)
    assert (first.fetched, first.skipped) == (31, 0)
    again = FakeClient()
    second = draft_pool.run(store, again, reqs, clock)
    assert (second.fetched, second.skipped, again.calls) == (0, 31, [])


def test_head_coach_is_read_from_the_coaches_result_set() -> None:
    coach = team_context.head_coach(roster(MIL, "2023-24", (204097, "Doc Rivers")))
    assert coach == team_context.HeadCoach(MIL, 204097, "Doc Rivers")


def test_a_payload_without_coaches_is_a_contract_violation() -> None:
    only_players = {"name": "CommonTeamRoster", "headers": [], "rowSet": []}
    bare = json.dumps({"resultSets": [only_players]}).encode()
    with pytest.raises(ContractViolation, match="Coaches"):
        team_context.head_coach(bare)


def test_head_coach_as_of_ignores_a_later_snapshot(store: SnapshotStore) -> None:
    req = nba_stats.common_team_roster(MIL, "2026-27")
    before = datetime(2026, 9, 1, tzinfo=UTC)
    after = datetime(2026, 10, 25, tzinfo=UTC)
    store.write(SOURCE, req.endpoint, req.key, roster(MIL, "2026-27", (1, "Old Coach")), before)
    store.write(SOURCE, req.endpoint, req.key, roster(MIL, "2026-27", (2, "New Coach")), after)
    draft = datetime(2026, 10, 18, tzinfo=UTC)
    assert team_context.head_coach_as_of(store, MIL, "2026-27", draft) == team_context.HeadCoach(
        MIL, 1, "Old Coach"
    )
    assert team_context.head_coach_as_of(store, MIL, "2026-27", after) == team_context.HeadCoach(
        MIL, 2, "New Coach"
    )
    august = datetime(2026, 8, 1, tzinfo=UTC)
    assert team_context.head_coach_as_of(store, MIL, "2026-27", august) is None


def test_team_advanced_reads_pace_and_ratings() -> None:
    adv = team_context.team_advanced(team_stats())
    assert len(adv) == 30
    assert adv[nba_stats.TEAM_IDS[0]] == {"pace": 98.0, "off_rating": 110.0, "def_rating": 108.0}
