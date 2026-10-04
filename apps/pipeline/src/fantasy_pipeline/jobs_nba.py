"""The NBA jobs on the generic runner (FND-011): the morning chain as a dependency graph.

cdn-day (per missed game day) ─┐
game-logs ─────────────────────┼─> week-projection -> brief -> send-brief
injury-report ─────────────────┘
`publish` (after `brief`) copies the day's outputs to the API's bucket when SERVE_ROOT is set.
`draft-values` (independent, optional; DATA-035) rebuilds the draft values and badge inputs from the
warehouse and writes them only when they pass the publish guard.
`brief` and `send-brief` do nothing (0 rows) before the league file exists or without a Telegram
chat; that's by design, not a failure.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from dikit import jobs
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import Clock
from fantasy_core.gamedate import game_date
from fantasy_ingest import draft_pool, injury_report, nba_cdn, nba_stats
from fantasy_pipeline import daily_brief, publish, telegram, week_projection, workspace

LOCK = Path("data/ops/run.lock")  # machine-local: one run at a time on this machine
RUNS = "ops/job_runs.jsonl"  # relative to the workspace root (INFRA-006)
LEAGUE_SETTINGS = "samples/yahoo/league_settings.txt"  # relative to the workspace root
CATCH_UP_DAYS = 14
DAILY_TARGETS = (
    "send-brief",
    "publish",
    "draft-values",
    "season-replay",
)  # everything, one machine (`daily-run`)
# D-63: the NBA hosts block cloud IPs, so the PC runs the fetch and Cloud Run runs the rest.
FETCH_TARGETS = ("cdn-day", "game-logs")
CLOUD_TARGETS = ("send-brief", "publish", "draft-values", "season-replay")


@dataclass
class Context:
    store: SnapshotStore
    clock: Clock
    season: str
    make_cdn: Callable[[], Any]
    make_stats: Callable[[], Any]
    make_injury: Callable[[], Any]
    send: Callable[[str], None] | None  # None: no Telegram chat saved
    settings: str  # league settings, relative to the workspace
    serve_root: str | None = None  # gs://…-serve: where the API reads (D-62)
    work: workspace.Workspace = field(default_factory=workspace.get)
    make_warehouse: Callable[[], Any] | None = None  # BigQuery for `draft-values`; None: skip it
    _clients: dict[str, Any] = field(default_factory=dict)

    def client(self, name: str) -> Any:
        if name not in self._clients:
            make = {"cdn": self.make_cdn, "stats": self.make_stats, "injury": self.make_injury}[
                name
            ]
            self._clients[name] = make()
        return self._clients[name]

    def close(self) -> None:
        for c in self._clients.values():
            c.close()
        self._clients.clear()


def publish_serve(ctx: Context) -> int:
    """Copy today's outputs to the API's bucket (0 when there is none, or the workspace is it)."""
    if ctx.serve_root is None or ctx.serve_root.rstrip("/") == ctx.work.root.rstrip("/"):
        return 0
    return publish.publish(ctx.work, ctx.serve_root, game_date(ctx.clock.now()))


def draft_values(ctx: Context) -> int:
    """DATA-035: rebuild and publish the draft values and badge inputs (0 without a warehouse)."""
    if ctx.make_warehouse is None:
        return 0
    from fantasy_ingest.yahoo_import import parse_league_settings  # noqa: PLC0415
    from fantasy_pipeline import draft_publish  # noqa: PLC0415 - heavy model imports

    rules = parse_league_settings(ctx.work.read_text(ctx.settings))
    return draft_publish.run_job(ctx.work, ctx.make_warehouse(), rules)


def season_replay(ctx: Context) -> int:
    """SIM-001: publish any replay season that isn't published yet (0 without a warehouse)."""
    if ctx.make_warehouse is None:
        return 0
    from fantasy_ingest.yahoo_import import parse_league_settings  # noqa: PLC0415
    from fantasy_pipeline import season_replay as sr  # noqa: PLC0415 - heavy model imports

    if all(ctx.work.exists(sr.path(s)) for s in sr.SEASONS):
        return 0  # nothing to build: no warehouse call
    wh = ctx.make_warehouse()
    rules = parse_league_settings(ctx.work.read_text(ctx.settings))
    return sr.run_job(ctx.work, lambda season: sr.build(wh, rules, season))


def registry(ctx: Context, *, include_fetch: bool = True) -> jobs.Registry:
    """The morning chain; `include_fetch=False` (the cloud job) leaves out the NBA fetch jobs."""

    def cdn_day(day: date | None) -> int:
        assert day is not None  # noqa: S101 - partitioned job
        return nba_cdn.daily(ctx.store, ctx.client("cdn"), ctx.clock, day).box_scores_fetched

    def game_logs(_: date | None) -> int:
        logs = [nba_stats.league_game_log(ctx.season, pt) for pt in ("P", "T")]
        rep = draft_pool.run(
            ctx.store, ctx.client("stats"), logs, ctx.clock, refresh=frozenset({"leaguegamelog"})
        )
        return rep.fetched

    def injuries(_: date | None) -> int:
        today = game_date(ctx.clock.now())
        rep = injury_report.fetch_latest(ctx.store, ctx.client("injury"), ctx.clock, today)
        return len(rep.rows) if rep else 0

    w = ctx.work

    def project(_: date | None) -> int:
        projections = w.read_parquet(week_projection.PROJECTIONS)
        res = week_projection.run(ctx.store, ctx.clock, projections, season=ctx.season)
        w.write_parquet(week_projection.OUT, res.table)
        nxt = week_projection.run_next(ctx.store, ctx.clock, projections, season=ctx.season)
        w.write_parquet(week_projection.NEXT_OUT, nxt.table)
        return res.table.height

    def brief(_: date | None) -> int:
        if not w.exists(daily_brief.LEAGUE):
            return 0
        from fantasy_ingest.yahoo_import import parse_league_settings  # noqa: PLC0415

        week = w.read_parquet(week_projection.OUT)
        values = w.read_parquet(daily_brief.VALUES)
        rules = parse_league_settings(w.read_text(ctx.settings))
        day = game_date(ctx.clock.now())
        out = daily_brief.compose(
            week,
            values,
            daily_brief.league_from_text(w.read_text(daily_brief.LEAGUE), week),
            rules.roster_slots,
            day,
            daily_brief.next_week_table(w),
        )
        daily_brief.publish(out, day, ctx.clock.now(), w)
        return len(out.markdown.splitlines())

    def send(_: date | None) -> int:
        path = daily_brief.brief_path(game_date(ctx.clock.now()), "md")
        if ctx.send is None or not w.exists(path):
            return 0
        ctx.send(w.read_text(path))
        return 1

    reg = jobs.Registry()
    if include_fetch:
        reg.add(jobs.Job("cdn-day", cdn_day, partitioned=True))
        reg.add(jobs.Job("game-logs", game_logs))
    # A missing injury report shouldn't stop the brief: availability falls back to base rates.
    reg.add(jobs.Job("injury-report", injuries, optional=True))
    fetched = FETCH_TARGETS if include_fetch else ()
    reg.add(jobs.Job("week-projection", project, deps=(*fetched, "injury-report")))
    reg.add(jobs.Job("brief", brief, deps=("week-projection",)))
    reg.add(jobs.Job("send-brief", send, deps=("brief",)))
    # Publishing for the web API must never block the Telegram brief: optional, after `brief`.
    reg.add(jobs.Job("publish", lambda _: publish_serve(ctx), deps=("brief",), optional=True))
    # DATA-035: the website's draft data, rebuilt daily; never blocks the brief.
    reg.add(jobs.Job("draft-values", lambda _: draft_values(ctx), optional=True))
    # SIM-001: the season replay files, built once per season; never blocks the brief.
    reg.add(jobs.Job("season-replay", lambda _: season_replay(ctx), optional=True))
    return reg


def telegram_sender(chat_path: Path = telegram.CHAT_FILE) -> Callable[[str], None] | None:
    """A send function for the saved chat, or None when there's no chat or token yet."""
    from fantasy_core.settings import get_settings  # noqa: PLC0415

    s = get_settings()
    # The cloud job has no local chat file: it gets the chat id from TELEGRAM_CHAT_ID (INFRA-006).
    chat = s.telegram_chat_id if s.telegram_chat_id is not None else telegram.load_chat(chat_path)
    token = s.telegram_bot_token
    if chat is None or token is None:
        return None

    def send(text: str) -> None:
        bot = telegram.Telegram(token)
        try:
            bot.send(chat, text)
        finally:
            bot.close()

    return send
