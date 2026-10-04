"""Daily in-season refresh (MVP piece 1): the schedule + yesterday's final box scores (cdn.nba.com)
and a fresh snapshot of the current season's game logs (stats.nba.com; the existing staging models
read the latest snapshot) and today's latest official injury report. Run each Sydney morning:
the US night's games are final and today's pre-game injury reports are out.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_core.gamedate import game_date
from fantasy_ingest import injury_report, nba_cdn, nba_stats
from fantasy_ingest.draft_pool import Fetcher, run


@dataclass(frozen=True)
class RefreshReport:
    day: date
    cdn: nba_cdn.DailyReport
    game_logs_fetched: int
    injury_rows: int | None = None  # None: no new report since the last run


def default_day(now: datetime) -> date:
    """Yesterday on the NBA (US/Eastern) calendar: the last game day that is fully final."""
    return game_date(now) - timedelta(days=1)


def refresh(  # noqa: PLR0913 - two sources, a clock and the run parameters
    store: SnapshotStore,
    cdn: Fetcher,
    stats: Fetcher,
    clock: Clock,
    *,
    season: str,
    day: date | None = None,
    injuries: injury_report.OptionalFetcher | None = None,
) -> RefreshReport:
    d = day or default_day(clock.now())
    cdn_rep = nba_cdn.daily(store, cdn, clock, d)
    logs = [nba_stats.league_game_log(season, pt) for pt in ("P", "T")]
    stats_rep = run(store, stats, logs, clock, refresh=frozenset({"leaguegamelog"}))
    rep = None
    if injuries is not None:
        rep = injury_report.fetch_latest(store, injuries, clock, game_date(clock.now()))
    return RefreshReport(d, cdn_rep, stats_rep.fetched, len(rep.rows) if rep else None)
