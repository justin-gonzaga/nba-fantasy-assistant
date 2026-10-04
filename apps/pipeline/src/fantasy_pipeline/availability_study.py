"""MVP-002: measure play rates by injury-report status from our own history.

For every regular-season game day of the chosen seasons: the latest official report published by
5:35 PM ET (the slot every season has) is fetched once into bronze, then its rows for that day are
joined to the season's game logs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path

import polars as pl

from dikit.errors import SourceUnavailable
from dikit.logging import get_logger
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_core.gamedate import NBA_TZ
from fantasy_evaluation import availability as av
from fantasy_ingest import injury_report as ir
from fantasy_ingest import nba_stats

log = get_logger(__name__)

REPORT_TIME = time(17, 35)  # ET
REPORT_OUT = Path("docs/evaluation/reports/MVP-002-availability.md")
RATES_OUT = Path("data/predictions/availability_rates.json")


@dataclass(frozen=True)
class Study:
    days: int
    reports: int
    missing: int
    unknown_layout: int
    unmatched: int
    rows: pl.DataFrame  # scored rows with a season column
    overall: pl.DataFrame
    by_season: dict[str, pl.DataFrame]


def _logs(store: SnapshotStore, season: str) -> pl.DataFrame:
    req = nba_stats.league_game_log(season, "P")
    payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
    if payload is None:
        msg = f"no {season} game logs stored: run `draft-pool` first"
        raise SourceUnavailable(nba_stats.SOURCE, msg)
    return pl.DataFrame(nba_stats.result_set(payload)).select(
        "PLAYER_ID", "PLAYER_NAME", "TEAM_NAME", "GAME_DATE"
    )


def run(
    store: SnapshotStore,
    client: ir.OptionalFetcher,
    clock: Clock,
    seasons: list[str],
    *,
    n_boot: int = 2000,
) -> Study:
    scored: list[pl.DataFrame] = []
    days = reports = missing = bad = unmatched = 0
    for season in seasons:
        logs = _logs(store, season)
        for day in sorted({date.fromisoformat(d) for d in logs["GAME_DATE"].to_list()}):
            days += 1
            rows = ir.stored_rows(store, day)
            if not rows:
                bound = datetime.combine(day, REPORT_TIME, tzinfo=NBA_TZ)
                try:
                    ir.fetch_latest(store, client, clock, day, latest=bound)
                except ir.UnknownLayout:
                    bad += 1
                    continue
                rows = ir.stored_rows(store, day)
            if not rows:
                missing += 1
                continue
            reports += 1
            rep = pl.DataFrame(rows).with_columns(pl.col("game_date").str.to_date())
            rep = rep.filter(pl.col("game_date") == day).select(
                "game_date", "team", "player", "status"
            )
            out = av.outcomes(rep, logs)
            unmatched += out.unmatched
            scored.append(out.rows.with_columns(pl.lit(season).alias("season")))
    allrows = pl.concat(scored) if scored else pl.DataFrame()
    overall = av.rates(allrows, n_boot=n_boot) if scored else pl.DataFrame()
    by_season = {
        s: av.rates(allrows.filter(pl.col("season") == s), n_boot=n_boot)
        for s in seasons
        if scored and allrows.filter(pl.col("season") == s).height
    }
    log.info("availability_study", days=days, reports=reports, missing=missing, unmatched=unmatched)
    return Study(days, reports, missing, bad, unmatched, allrows, overall, by_season)


def _table(df: pl.DataFrame) -> str:
    lines = ["| status | n | played | 95 % CI |", "|---|---|---|---|"]
    lines += [
        f"| {r['status']} | {r['n']:,} | {r['rate']:.1%} | {r['lo']:.1%} to {r['hi']:.1%} |"
        for r in df.iter_rows(named=True)
    ]
    return "\n".join(lines)


def report(study: Study, generated: datetime) -> str:
    seasons = "\n\n".join(f"### {s}\n\n{_table(df)}" for s, df in study.by_season.items())
    return f"""# MVP-002: how often listed players actually play

Generated {generated:%Y-%m-%d %H:%M} UTC by `python -m fantasy_pipeline availability-study`.
Replaces the placeholder status probabilities (A-30) used by the rest-of-week projections.

**Method**: for each regular-season game day, the latest official injury report published by
5:35 PM ET (stored in bronze), joined to that season's game logs: a listed player "played" if he
has a game-log row that day. Players who never appear in the season's logs can't be scored
(e.g. two-way players who never played) and are excluded. 95 % intervals: bootstrap over game
days (2,000 resamples) [R-54].

**Coverage**: {study.days} game days; {study.reports} reports used; {study.missing} days with no
report found at that slot; {study.unknown_layout} unparseable; {study.unmatched:,} rows unmatched.

## Pooled

{_table(study.overall)}

## By season

{seasons}

## Caveats

- One snapshot per day at ~5:30 PM ET. Earlier reports (the Sydney-morning brief runs around
  3:30-4:30 PM ET) carry more uncertainty: a later downgrade or upgrade isn't seen here.
- "Played" means any minutes; a return on a minutes restriction counts as played.
"""


def rates_json(study: Study) -> str:
    return json.dumps(
        {
            "source": f"MVP-002 availability study ({REPORT_OUT.as_posix()})",
            "rates": {
                r["status"]: round(r["rate"], 3) for r in study.overall.iter_rows(named=True)
            },
        },
        indent=2,
    )
