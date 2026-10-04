"""Team and head-coach context by season (DATA-038).

Head coach per team-season from `commonteamroster`'s Coaches result set. The endpoint lists the
end-of-season staff, so a mid-season change shows only the final coach (verified live 2026-10-03:
MIL 2023-24 lists Doc Rivers, who replaced Adrian Griffin). Team pace and offensive/defensive
rating come from `leaguedashteamstats` (Advanced). Fetching reuses the draft-pool backfill loop:
resumable, raw is write-once, home IP only (D-63).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from dikit.store.snapshot import SnapshotStore
from fantasy_ingest import nba_stats
from fantasy_ingest.nba_stats import SOURCE, StatsRequest


@dataclass(frozen=True)
class HeadCoach:
    team_id: int
    coach_id: int
    name: str


def plan(seasons: list[str]) -> list[StatsRequest]:
    """Every team's roster (for its coaches) and the league's team advanced stats, per season."""
    reqs: list[StatsRequest] = []
    for season in seasons:
        reqs += [nba_stats.common_team_roster(t, season) for t in nba_stats.TEAM_IDS]
        reqs.append(nba_stats.league_dash_team_stats_advanced(season))
    return reqs


def head_coach(payload: bytes) -> HeadCoach | None:
    """The head coach listed in a roster payload (None when the staff list has none)."""
    for row in nba_stats.result_set(payload, "Coaches"):
        if row.get("COACH_TYPE") == "Head Coach":
            team, coach = int(str(row["TEAM_ID"])), int(str(row["COACH_ID"]))
            return HeadCoach(team, coach, str(row["COACH_NAME"]))
    return None


def head_coach_as_of(
    store: SnapshotStore, team_id: int, season: str, t: datetime
) -> HeadCoach | None:
    """The head coach as known at time t: the latest roster snapshot observed at or before t."""
    req = nba_stats.common_team_roster(team_id, season)
    payload = store.as_of(SOURCE, req.endpoint, req.key, t)
    return head_coach(payload) if payload else None


def team_advanced(payload: bytes) -> dict[int, dict[str, float]]:
    """Pace and offensive/defensive rating per team id."""
    out: dict[int, dict[str, float]] = {}
    for row in nba_stats.result_set(payload):
        out[int(str(row["TEAM_ID"]))] = {
            "pace": float(str(row["PACE"])),
            "off_rating": float(str(row["OFF_RATING"])),
            "def_rating": float(str(row["DEF_RATING"])),
        }
    return out
