"""Pre-season backfill (DATA-030, G-24 / D-57).

Exhibition game logs first, then per-game box scores for starts.
"""

from __future__ import annotations

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_ingest import nba_stats
from fantasy_ingest.draft_pool import Fetcher, RunReport, run
from fantasy_ingest.nba_stats import SOURCE, StatsRequest


def plan_logs(seasons: list[str]) -> list[StatsRequest]:
    return [
        nba_stats.league_game_log(s, pt, nba_stats.PRE_SEASON) for s in seasons for pt in ("P", "T")
    ]


def game_ids(store: SnapshotStore, seasons: list[str]) -> list[str]:
    """Pre-season game ids from the stored team logs (each game appears once per team)."""
    ids: set[str] = set()
    for s in seasons:
        req = nba_stats.league_game_log(s, "T", nba_stats.PRE_SEASON)
        payload = store.latest(SOURCE, req.endpoint, req.key)
        if payload:
            ids |= {str(r["GAME_ID"]) for r in nba_stats.result_set(payload)}
    return sorted(ids)


def backfill(
    store: SnapshotStore, client: Fetcher, seasons: list[str], clock: Clock
) -> tuple[RunReport, RunReport]:
    logs = run(store, client, plan_logs(seasons), clock)
    boxes = run(
        store, client, [nba_stats.box_score_traditional(g) for g in game_ids(store, seasons)], clock
    )
    return logs, boxes
