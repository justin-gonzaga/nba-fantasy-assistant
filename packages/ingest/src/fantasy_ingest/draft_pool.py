"""Draft-pool raw backfill (DRAFT-001): plan → skip what's stored → fetch → store.

Resumable by construction: a request whose key already has a snapshot is skipped, so an
interrupted run continues where it stopped.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from dikit.logging import get_logger
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_ingest import nba_stats
from fantasy_ingest.nba_stats import SOURCE, StatsRequest

log = get_logger(__name__)


class Fetcher(Protocol):
    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes: ...


@dataclass(frozen=True)
class RunReport:
    fetched: int
    skipped: int


@dataclass(frozen=True)
class Coverage:
    rostered: int
    missing: list[dict[str, object]]

    @property
    def pct(self) -> float:
        return 100.0 * (self.rostered - len(self.missing)) / self.rostered if self.rostered else 0.0


def plan(history: list[str], roster_season: str) -> list[StatsRequest]:
    reqs: list[StatsRequest] = []
    for season in history:
        reqs += [
            nba_stats.league_game_log(season, "P"),
            nba_stats.league_game_log(season, "T"),
            nba_stats.league_dash_player_stats(season),
        ]
    reqs += [nba_stats.common_team_roster(t, roster_season) for t in nba_stats.TEAM_IDS]
    reqs.append(nba_stats.draft_history())
    return reqs


def run(
    store: SnapshotStore,
    client: Fetcher,
    reqs: list[StatsRequest],
    clock: Clock,
    refresh: frozenset[str] = frozenset(),
) -> RunReport:
    """`refresh` lists endpoints to fetch again even when stored (a new snapshot is added;
    bronze stays immutable). Used for draft-week roster updates (DRAFT-006)."""
    fetched = skipped = 0
    for i, req in enumerate(reqs, 1):
        if req.endpoint not in refresh and store.has(SOURCE, req.endpoint, req.key):
            skipped += 1
            continue
        payload = client.get(req.url, req.params)
        rows = nba_stats.row_count(payload)
        store.write(
            SOURCE, req.endpoint, req.key, payload, clock.now(), rows=rows, params=req.params
        )
        fetched += 1
        log.info(
            "snapshot_stored", endpoint=req.endpoint, key=req.key, rows=rows, n=i, of=len(reqs)
        )
    return RunReport(fetched, skipped)


def _ids(store: SnapshotStore, req: StatsRequest, column: str) -> set[object]:
    payload = store.latest(SOURCE, req.endpoint, req.key)
    return {r[column] for r in nba_stats.result_set(payload)} if payload else set()


def coverage(store: SnapshotStore, history: list[str], roster_season: str) -> Coverage:
    """Rostered players with neither NBA game logs in `history` nor a draft record (AC2)."""
    rostered: dict[object, dict[str, object]] = {}
    for team in nba_stats.TEAM_IDS:
        req = nba_stats.common_team_roster(team, roster_season)
        payload = store.latest(SOURCE, req.endpoint, req.key)
        for row in nba_stats.result_set(payload) if payload else []:
            rostered[row["PLAYER_ID"]] = row
    known = _ids(store, nba_stats.draft_history(), "PERSON_ID")
    for season in history:
        known |= _ids(store, nba_stats.league_game_log(season, "P"), "PLAYER_ID")
    missing = [
        {k: row.get(k) for k in ("PLAYER_ID", "PLAYER", "TeamID", "EXP", "HOW_ACQUIRED")}
        for pid, row in rostered.items()
        if pid not in known
    ]
    return Coverage(len(rostered), missing)
