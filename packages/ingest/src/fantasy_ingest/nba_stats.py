"""stats.nba.com request specs (DISC-003). Home IP only; paced at 1.0 s (PacedClient).

Parameters mirror the verified fixture captures so the payloads match what the spikes saw.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from dikit.errors import ContractViolation

BASE = "https://stats.nba.com/stats"
SOURCE = "nba_stats"

# The 30 franchise IDs are the contiguous block 1610612737 (ATL) … 1610612766 (CHA).
TEAM_IDS: tuple[int, ...] = tuple(range(1610612737, 1610612767))

_SEASON = re.compile(r"^(\d{4})-(\d{2})$")


@dataclass(frozen=True)
class StatsRequest:
    endpoint: str
    key: str
    params: dict[str, str] = field(hash=False)

    @property
    def url(self) -> str:
        return f"{BASE}/{self.endpoint}"


def seasons(first: str, last: str) -> list[str]:
    """Inclusive range of NBA season strings, e.g. 2015-16 … 2025-26."""
    starts = []
    for s in (first, last):
        m = _SEASON.match(s)
        if not m or (int(m.group(1)) + 1) % 100 != int(m.group(2)):
            msg = f"invalid season {s!r}, expected e.g. 2015-16"
            raise ValueError(msg)
        starts.append(int(m.group(1)))
    return [f"{y}-{(y + 1) % 100:02d}" for y in range(starts[0], starts[1] + 1)]


PRE_SEASON = "Pre Season"
REGULAR_SEASON = "Regular Season"


def league_game_log(
    season: str, player_or_team: str, season_type: str = REGULAR_SEASON
) -> StatsRequest:
    # Regular-season keys stay unchanged; other season types get a suffix (DATA-030).
    suffix = (
        ""
        if season_type == REGULAR_SEASON
        else "/season_type=" + season_type.lower().replace(" ", "_")
    )
    return StatsRequest(
        "leaguegamelog",
        f"season={season}/player_or_team={player_or_team}{suffix}",
        {
            "LeagueID": "00",
            "Season": season,
            "SeasonType": season_type,
            "PlayerOrTeam": player_or_team,
            "Counter": "0",
            "Sorter": "DATE",
            "Direction": "ASC",
            "DateFrom": "",
            "DateTo": "",
        },
    )


_DASH_NONE = [
    "PORound",
    "Outcome",
    "Location",
    "SeasonSegment",
    "VsConference",
    "VsDivision",
    "TeamID",
    "Conference",
    "Division",
    "GameSegment",
    "ShotClockRange",
    "GameScope",
    "PlayerExperience",
    "PlayerPosition",
    "StarterBench",
    "DraftYear",
    "DraftPick",
    "College",
    "Country",
    "Height",
    "Weight",
    "TwoWay",
    "GameSubtype",
    "ISTRound",
]


def league_dash_player_stats(season: str) -> StatsRequest:
    params = {
        "MeasureType": "Base",
        "PerMode": "Totals",
        "PlusMinus": "N",
        "PaceAdjust": "N",
        "Rank": "N",
        "LeagueID": "00",
        "Season": season,
        "SeasonType": "Regular Season",
        "Month": "0",
        "DateFrom": "",
        "DateTo": "",
        "OpponentTeamID": "0",
        "Period": "0",
        "LastNGames": "0",
        "ActiveRoster": "0",
    }
    # Unset filters go as empty strings. The API echoes them back as "None", but a literal
    # "None" in the request gets HTTP 500 (verified live 2026-09-25).
    params.update(dict.fromkeys(_DASH_NONE, ""))
    return StatsRequest("leaguedashplayerstats", f"season={season}/per_mode=totals", params)


def league_dash_team_stats_advanced(season: str) -> StatsRequest:
    """Team pace and offensive/defensive rating per season (DATA-038; checked live 2026-10-03)."""
    params = {
        "MeasureType": "Advanced",
        "PerMode": "PerGame",
        "PlusMinus": "N",
        "PaceAdjust": "N",
        "Rank": "N",
        "LeagueID": "00",
        "Season": season,
        "SeasonType": "Regular Season",
        "Month": "0",
        "OpponentTeamID": "0",
        "Period": "0",
        "LastNGames": "0",
        "TeamID": "0",
        "DateFrom": "",
        "DateTo": "",
    }
    params.update(dict.fromkeys(_TEAM_DASH_EMPTY, ""))
    return StatsRequest("leaguedashteamstats", f"season={season}/measure=advanced", params)


_TEAM_DASH_EMPTY = [
    "Conference",
    "Division",
    "GameScope",
    "GameSegment",
    "Location",
    "Outcome",
    "PORound",
    "PlayerExperience",
    "PlayerPosition",
    "SeasonSegment",
    "ShotClockRange",
    "StarterBench",
    "TwoWay",
    "VsConference",
    "VsDivision",
]


def common_team_roster(team_id: int, season: str) -> StatsRequest:
    return StatsRequest(
        "commonteamroster",
        f"season={season}/team_id={team_id}",
        {"TeamID": str(team_id), "LeagueID": "00", "Season": season},
    )


def box_score_traditional(game_id: str) -> StatsRequest:
    """Per-game box score (v3 format: boxScoreTraditional.homeTeam/awayTeam.players; a non-empty
    `position` marks a starter). Used for pre-season starts (DATA-030)."""
    return StatsRequest(
        "boxscoretraditionalv3",
        f"game_id={game_id}",
        {
            "GameID": game_id,
            "LeagueID": "00",
            "StartPeriod": "0",
            "EndPeriod": "10",
            "StartRange": "0",
            "EndRange": "28800",
            "RangeType": "0",
        },
    )


def draft_history() -> StatsRequest:
    return StatsRequest("drafthistory", "league=00", {"LeagueID": "00"})


def result_set(payload: bytes, index: int | str = 0) -> list[dict[str, object]]:
    """Rows of one result set as dicts, by position or by name (e.g. "Coaches")."""
    data = json.loads(payload)
    sets = data.get("resultSets") if isinstance(data, dict) else None
    if not isinstance(sets, list) or not sets:
        msg = "stats.nba.com payload has no resultSets"
        raise ContractViolation(msg)
    if isinstance(index, str):
        named = [s for s in sets if s.get("name") == index]
        if not named:
            msg = f"stats.nba.com payload has no result set named {index!r}"
            raise ContractViolation(msg)
        rs = named[0]
    else:
        rs = sets[index]
    return [dict(zip(rs["headers"], row, strict=True)) for row in rs["rowSet"]]


def row_count(payload: bytes) -> int:
    """Rows in a payload: resultSets[0] for classic endpoints, players for v3 box scores."""
    data = json.loads(payload)
    box = data.get("boxScoreTraditional") if isinstance(data, dict) else None
    if isinstance(box, dict):
        return sum(len(box.get(side, {}).get("players", [])) for side in ("homeTeam", "awayTeam"))
    return len(result_set(payload))
