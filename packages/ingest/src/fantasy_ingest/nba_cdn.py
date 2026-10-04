"""cdn.nba.com static JSON: the season schedule and final box scores (DATA-006; DISC-004 findings).

Daily job: store a fresh schedule snapshot (game times, postponements and statuses change),
then store the box score of every game that is final on the given US/Eastern game date.
A box score is fetched once: a stored game id is skipped, so re-runs are idempotent. Only
final games are requested, because the CDN answers 403 (not 404) for files that don't exist yet.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from dikit.errors import ContractViolation
from dikit.logging import get_logger
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_ingest.draft_pool import Fetcher

log = get_logger(__name__)

SOURCE = "nba_cdn"
SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"
BOX_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
FINAL = 3
REGULAR_SEASON_PREFIX = "002"


@dataclass(frozen=True)
class Game:
    game_id: str
    game_date: date  # the NBA game date (US/Eastern)
    tipoff_utc: datetime
    away: str
    home: str
    status: int

    @property
    def final(self) -> bool:
        return self.status == FINAL

    @property
    def regular_season(self) -> bool:
        return self.game_id.startswith(REGULAR_SEASON_PREFIX)


@dataclass(frozen=True)
class DailyReport:
    schedule_games: int
    box_scores_fetched: int
    box_scores_skipped: int


def _season(payload: dict[str, Any]) -> str:
    return str(payload["leagueSchedule"]["seasonYear"])


def parse_schedule(payload: bytes) -> list[Game]:
    try:
        doc = json.loads(payload)
        games = [
            Game(
                game_id=str(g["gameId"]),
                game_date=date.fromisoformat(str(g["gameDateEst"])[:10]),
                tipoff_utc=datetime.fromisoformat(
                    str(g["gameDateTimeUTC"]).replace("Z", "+00:00")
                ).astimezone(UTC),
                away=str(g["awayTeam"]["teamTricode"]),
                home=str(g["homeTeam"]["teamTricode"]),
                status=int(g["gameStatus"]),
            )
            for d in doc["leagueSchedule"]["gameDates"]
            for g in d["games"]
        ]
    except (KeyError, TypeError, ValueError) as err:
        msg = f"unexpected cdn schedule shape: {err!r}"
        raise ContractViolation(msg) from err
    return games


@dataclass(frozen=True)
class Team:
    team_id: int
    tricode: str
    full_name: str  # "LA Clippers", as printed on the injury report


def teams(payload: bytes) -> list[Team]:
    """The league's teams, from the schedule (placeholder games with blank teams are skipped)."""
    found: dict[int, Team] = {}
    for d in json.loads(payload)["leagueSchedule"]["gameDates"]:
        for g in d["games"]:
            for side in ("homeTeam", "awayTeam"):
                t = g[side]
                if t.get("teamTricode"):
                    name = f"{t['teamCity']} {t['teamName']}"
                    found[int(t["teamId"])] = Team(int(t["teamId"]), t["teamTricode"], name)
    return sorted(found.values(), key=lambda t: t.tricode)


def final_game_ids(games: list[Game], day: date) -> list[str]:
    return sorted(g.game_id for g in games if g.game_date == day and g.final)


def box_score_players(payload: bytes) -> int:
    game = json.loads(payload)["game"]
    return sum(len(game[side]["players"]) for side in ("homeTeam", "awayTeam"))


def daily(store: SnapshotStore, client: Fetcher, clock: Clock, day: date) -> DailyReport:
    raw = client.get(SCHEDULE_URL)
    games = parse_schedule(raw)
    season = _season(json.loads(raw))
    store.write(SOURCE, "schedule", f"season={season}", raw, clock.now(), rows=len(games))
    fetched = skipped = 0
    for gid in final_game_ids(games, day):
        key = f"game_id={gid}"
        if store.has(SOURCE, "boxscore", key):
            skipped += 1
            continue
        box = client.get(BOX_URL.format(game_id=gid))
        store.write(SOURCE, "boxscore", key, box, clock.now(), rows=box_score_players(box))
        fetched += 1
    log.info("cdn_daily", day=day.isoformat(), games=len(games), fetched=fetched, skipped=skipped)
    return DailyReport(len(games), fetched, skipped)
