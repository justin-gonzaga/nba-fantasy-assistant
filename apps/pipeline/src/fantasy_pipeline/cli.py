"""Pipeline CLI: `uv run python -m fantasy_pipeline <command>`."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl
import typer

from dikit import jobs
from dikit.logging import configure_logging
from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import FrozenClock, SystemClock
from fantasy_core.gamedate import game_date
from fantasy_core.settings import get_settings
from fantasy_evaluation import (
    distribution_backtest,
    draft_replay,
    inseason_backtest,
    lineup_replay,
    moves_replay,
    simulation_backtest,
)
from fantasy_ingest import (
    daily,
    draft_pool,
    injury_report,
    nba_cdn,
    nba_stats,
    preseason,
    team_context,
)
from fantasy_ingest.http import PacedClient
from fantasy_ingest.yahoo_import import parse_league_settings
from fantasy_models.valuation import eligibility
from fantasy_pipeline import (
    availability_study,
    daily_brief,
    dist_backtest,
    draft_breakouts,
    draft_mock,
    draft_preseason,
    draft_projection,
    draft_replay_run,
    draft_sheet,
    draft_values,
    inseason_run,
    jobs_nba,
    lineup_replay_report,
    moves_replay_run,
    returners_report,
    sim_backtest,
    team_effects_study,
    telegram,
    week_projection,
    workspace,
)
from fantasy_pipeline.warehouse import BigQueryWarehouse, Warehouse

app = typer.Typer(no_args_is_help=True, add_completion=False)

ROOT = typer.Option(None, help="Local path or gs:// URI (default: settings DATA_ROOT)")
FIRST = typer.Option("2015-16", help="First history season")
LAST = typer.Option("2025-26", help="Last history season")
ROSTER = typer.Option("2026-27", help="Season for current rosters")
TEAM_EFFECTS_OUT = typer.Option(
    Path("docs/evaluation/reports/ANL-010-team-coach-effects.md"), help="Report path"
)
REFRESH = typer.Option([], help="Endpoints to fetch again, e.g. --refresh commonteamroster")


def make_client() -> PacedClient:  # pragma: no cover - real network
    return PacedClient(nba_stats.SOURCE, min_interval=1.0)


def make_cdn_client() -> PacedClient:  # pragma: no cover - real network
    return PacedClient(nba_cdn.SOURCE, min_interval=0.6)


def make_injury_client() -> PacedClient:  # pragma: no cover - real network
    return PacedClient(injury_report.SOURCE, min_interval=0.6)


def make_warehouse(project: str) -> Warehouse:  # pragma: no cover - real BigQuery
    return BigQueryWarehouse(project)


PROJECT = typer.Option("nbafa-hdfo-dev", help="GCP project holding the warehouse")
REPORT_OUT = typer.Option(Path("docs/evaluation/reports/DRAFT-002-backtest.md"), help="Report path")
SETTINGS_PATH = Path("data/samples/yahoo/league_settings.txt")
SETTINGS = typer.Option(SETTINGS_PATH, help="Pasted Yahoo settings")
VALUES_OUT = typer.Option(Path("data/predictions/auction_values.parquet"), help="Local copy")
BREAKOUT_OUT = typer.Option(
    Path("docs/evaluation/reports/DRAFT-007-backtest.md"), help="Report path"
)
SHEET_DIR = typer.Option(Path("data/draft"), help="Output folder for the board")
PRESEASON_OUT = typer.Option(
    Path("docs/evaluation/reports/DRAFT-008-backtest.md"), help="Report path"
)
PARQUET_OUT = typer.Option(Path("data/predictions/preseason_projection.parquet"), help="Local copy")

STUDY_SEASONS = typer.Option(["2024-25", "2025-26"], help="Seasons to study")
BRIEF_SETTINGS = typer.Option(None, help="Pasted Yahoo settings (default: workspace)")
LEAGUE_FILE = typer.Option(None, help="League file (default: the workspace's league/league.json)")
BRIEF_FILE = typer.Option(None, help="Brief file (default: today's)")
RUN_JOBS = typer.Argument(..., help="Job names, or `daily`")
WEEK_PROJ_IN = typer.Option(None, help="Per-game projections (default: workspace)")
WEEK_PROJ_OUT = typer.Option(None, help="Output parquet (default: workspace)")


def _root(root: str | None) -> str:
    return root or get_settings().data_root


@app.command("draft-pool")
def draft_pool_cmd(
    root: str | None = ROOT,
    first: str = FIRST,
    last: str = LAST,
    roster_season: str = ROSTER,
    refresh: list[str] = REFRESH,
) -> None:
    """Backfill draft-pool raw snapshots from stats.nba.com (home IP; resumable)."""
    configure_logging()
    reqs = draft_pool.plan(nba_stats.seasons(first, last), roster_season)
    client = make_client()
    try:
        report = draft_pool.run(
            SnapshotStore(_root(root)), client, reqs, SystemClock(), frozenset(refresh)
        )
    finally:
        client.close()
    typer.echo(f"fetched={report.fetched} skipped={report.skipped}")


@app.command("team-context-backfill")
def team_context_cmd(root: str | None = ROOT, first: str = FIRST, last: str = LAST) -> None:
    """Head coaches (team rosters) and team pace/ratings per season, DATA-038; home IP only."""
    configure_logging()
    client = make_client()
    try:
        report = draft_pool.run(
            SnapshotStore(_root(root)),
            client,
            team_context.plan(nba_stats.seasons(first, last)),
            SystemClock(),
        )
    finally:
        client.close()
    typer.echo(f"fetched={report.fetched} skipped={report.skipped}")


@app.command("team-effects-study")
def team_effects_cmd(
    project: str = PROJECT,
    out: Path = TEAM_EFFECTS_OUT,
) -> None:
    """ANL-010: team/coach effects on the projection's errors; the EXP-004 go/no-go."""
    md, decision = team_effects_study.run(make_warehouse(project), SystemClock().now())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    typer.echo(f"decision={'GO' if decision.go else 'NO-GO'} report={out}")


@app.command("draft-pool-coverage")
def coverage_cmd(
    root: str | None = ROOT, first: str = FIRST, last: str = LAST, roster_season: str = ROSTER
) -> None:
    """Report rostered players with no NBA history and no draft record."""
    cov = draft_pool.coverage(
        SnapshotStore(_root(root)), nba_stats.seasons(first, last), roster_season
    )
    typer.echo(f"rostered={cov.rostered} missing={len(cov.missing)} coverage={cov.pct:.1f}%")
    for m in cov.missing:
        typer.echo(json.dumps(m))


@app.command("draft-backtest")
def draft_backtest_cmd(
    project: str = PROJECT,
    first_target: str = typer.Option("2018-19", help="First backtest target season"),
    last_target: str = typer.Option("2025-26", help="Primary (last) target season"),
    n_boot: int = typer.Option(2000, help="Bootstrap resamples"),
    out: Path = REPORT_OUT,
) -> None:
    """Rolling-origin backtest of B0/B1/C1 preseason projections; writes the report (AC2)."""
    md, decision, folds = draft_projection.run_backtest(
        make_warehouse(project), first_target, last_target, n_boot
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    typer.echo(f"folds={len(folds)} decision={decision.method} report={out}")


@app.command("draft-projections")
def draft_projections_cmd(
    project: str = PROJECT,
    target: str = typer.Option("2026-27", help="Season to project"),
    method: str = typer.Option("H1+aging+M1", help="B0, B1, C1, H1, H1+aging or H1+aging+M1"),
    parquet: Path = PARQUET_OUT,
) -> None:
    """Project the draft pool and write predictions.preseason_projection (AC1)."""
    wh = make_warehouse(project)
    long, (projected, pool) = draft_projection.build_projections(wh, target, method)
    wh.write(long, "predictions.preseason_projection")
    parquet.parent.mkdir(parents=True, exist_ok=True)
    long.write_parquet(parquet)
    pct = 100 * projected / pool
    typer.echo(f"players={projected}/{pool} coverage={pct:.1f}% rows={long.height} method={method}")


@app.command("draft-values")
def draft_values_cmd(  # noqa: PLR0913, PLR0917 - CLI options
    project: str = PROJECT,
    settings: Path = SETTINGS,
    target: str = typer.Option("2026-27", help="Season to value"),
    method: str = typer.Option("H1+aging+M1", help="Projection method (the backtest decision)"),
    parquet: Path = VALUES_OUT,
    fill: bool = typer.Option(False, help="Missed games at replacement level (DRAFT-011)"),
) -> None:
    """League-aware values ($ for auctions) for every punt variant (DRAFT-003)."""
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    wh = make_warehouse(project)
    values = draft_values.build_values(wh, rules, target, method, fill=fill)
    wh.write(values, "predictions.auction_values")
    parquet.parent.mkdir(parents=True, exist_ok=True)
    values.write_parquet(parquet)
    top = values.filter(values["variant"] == "all").sort("overall_rank").head(10)
    typer.echo(
        f"format={rules.scoring} teams={rules.teams} pool={rules.pool_size} rows={values.height}"
    )
    for r in top.iter_rows(named=True):
        money = f"${r['dollars']:.0f}" if r["dollars"] is not None else "-"
        typer.echo(f"{r['overall_rank']:>3} {r['player_name']:<28} {money:>5}  tier {r['tier']}")


@app.command("draft-breakouts")
def draft_breakouts_cmd(
    project: str = PROJECT,
    target: str = typer.Option("2026-27", help="Season to predict"),
    n_boot: int = typer.Option(2000, help="Bootstrap resamples"),
    out: Path = BREAKOUT_OUT,
) -> None:
    """Minutes-model + breakout backtests (DRAFT-007); writes breakout probabilities if M2 ships."""
    wh = make_warehouse(project)
    md, mins, brk, growth, probs = draft_breakouts.run(wh, target, n_boot)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    if probs is not None:
        wh.write(probs, "predictions.breakout_probability")
    typer.echo(
        f"M1 winner={mins.winner} ships={mins.ships} | bounce-back ships={brk.ships} "
        f"| growth ships={growth.ships} lift20={growth.lift20[0]:+.3f} "
        f"[{growth.lift20[1]:+.3f},{growth.lift20[2]:+.3f}] | report={out}"
    )


@app.command("draft-sheet")
def draft_sheet_cmd(
    project: str = PROJECT,
    settings: Path = SETTINGS,
    out_dir: Path = SHEET_DIR,
) -> None:
    """Auction board (phone-first HTML + CSV) from the latest predictions (DRAFT-004)."""
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    wh = make_warehouse(project)
    meta = draft_sheet.SheetMeta(
        teams=rules.teams,
        budget=rules.auction_budget or 0,
        pool=rules.pool_size,
        scoring=str(rules.scoring).replace("_", " ").replace("h2h", "H2H"),
        method="H1+aging+M1",
        generated=SystemClock().now().strftime("%d %b %Y %H:%M UTC"),
        draft_year=2026,
        slots=rules.drafted_per_team,
    )
    data = draft_sheet.load(wh, meta)
    out_dir.mkdir(parents=True, exist_ok=True)
    html, csv = out_dir / "auction_board.html", out_dir / "auction_board.csv"
    html.write_text(draft_sheet.render_html(data), encoding="utf-8")
    draft_sheet.to_csv(data).write_csv(csv)
    typer.echo(f"{html}\n{csv}")


@app.command("draft-mock")
def draft_mock_cmd(
    project: str = PROJECT,
    settings: Path = SETTINGS,
    seed: int = typer.Option(1, help="Random seed for the simulated bidders"),
) -> None:
    """Full mock auction on the live values; every helper update is timed (DRAFT-005)."""
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    budget = rules.auction_budget or 0
    meta = draft_sheet.SheetMeta(
        rules.teams, budget, rules.pool_size, "", "", "", 2026, rules.drafted_per_team
    )
    rows = draft_sheet.load(make_warehouse(project), meta)["variants"][0]["rows"]
    players = [{"id": r[0], "usd": float(r[2] or 1), "z": r[4]} for r in rows]
    teams = [f"Team {i + 1}" for i in range(rules.teams)]
    res = draft_mock.run_mock(players, teams, budget, rules.drafted_per_team, seed)
    typer.echo(
        f"picks={res.picks} rosters_full={res.rosters_full} spent=${res.spent:.0f} "
        f"advise_ms p50={res.p50_ms:.1f} max={res.max_ms:.1f} (target < 2000)"
    )


@app.command("preseason-backfill")
def preseason_backfill_cmd(root: str | None = ROOT, first: str = FIRST, last: str = LAST) -> None:
    """Pre-season game logs + per-game box scores (starts), DATA-030; home IP only."""
    configure_logging()
    client = make_client()
    try:
        logs, boxes = preseason.backfill(
            SnapshotStore(_root(root)), client, nba_stats.seasons(first, last), SystemClock()
        )
    finally:
        client.close()
    log_line = f"logs fetched={logs.fetched} skipped={logs.skipped}"
    box_line = f"box scores fetched={boxes.fetched} skipped={boxes.skipped}"
    typer.echo(f"{log_line} | {box_line}")


@app.command("draft-preseason")
def draft_preseason_cmd(
    project: str = PROJECT,
    n_boot: int = typer.Option(2000, help="Bootstrap resamples"),
    out: Path = PRESEASON_OUT,
) -> None:
    """Pre-registered tests of the pre-season role signal (DRAFT-008); writes the report."""
    wh = make_warehouse(project)
    md, m1_ships, growth_ships, probs = draft_preseason.run(wh, n_boot)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    if probs is not None:
        wh.write(probs, "predictions.growth_probability")
    pending = "written" if probs is not None else "pending the 2026-27 pre-season"
    status = f"growth flags ship={growth_ships} ({pending})"
    typer.echo(f"M1+pre-season ships={m1_ships} | {status} | report={out}")


@app.command("nba-daily")
def nba_daily_cmd(
    root: str | None = ROOT,
    season: str = typer.Option("2026-27", help="Current season"),
    day: str | None = typer.Option(None, help="US/Eastern game date (default: yesterday)"),
) -> None:
    """Daily refresh: schedule + final box scores (cdn.nba.com) and current game logs (DATA-006)."""
    configure_logging()
    cdn, stats, injuries = make_cdn_client(), make_client(), make_injury_client()
    try:
        rep = daily.refresh(
            SnapshotStore(_root(root)),
            cdn,
            stats,
            SystemClock(),
            season=season,
            day=date.fromisoformat(day) if day else None,
            injuries=injuries,
        )
    finally:
        cdn.close()
        stats.close()
        injuries.close()
    typer.echo(
        f"day={rep.day} schedule_games={rep.cdn.schedule_games} "
        f"box_scores fetched={rep.cdn.box_scores_fetched} skipped={rep.cdn.box_scores_skipped} "
        f"game_logs fetched={rep.game_logs_fetched} "
        f"injury_rows={'no new report' if rep.injury_rows is None else rep.injury_rows}"
    )


@app.command("week-projection")
def week_projection_cmd(
    root: str | None = ROOT,
    projections: Path | None = WEEK_PROJ_IN,
    out: Path | None = WEEK_PROJ_OUT,
    at: str | None = typer.Option(None, help="Pretend it is this UTC time (ISO), for checks"),
) -> None:
    """Rest-of-week projections for the daily brief (MVP-001)."""
    configure_logging()
    clock = FrozenClock(datetime.fromisoformat(at)) if at else SystemClock()
    w = workspace.get()
    proj = (
        pl.read_parquet(projections) if projections else w.read_parquet(week_projection.PROJECTIONS)
    )
    res = week_projection.run(SnapshotStore(_root(root)), clock, proj)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        res.table.write_parquet(out)
    else:
        w.write_parquet(week_projection.OUT, res.table)
    t = res.table
    typer.echo(
        f"week={res.week.start}..{res.week.end} today={res.today} players={t.height} "
        f"with_games={t.filter(pl.col('games_left') > 0).height} "
        f"playing_today={t.filter(pl.col('plays_today')).height} "
        f"injury_report={res.injury_report or 'none'} unmatched_injury_names={len(res.unmatched)}"
    )


@app.command("availability-study")
def availability_study_cmd(
    root: str | None = ROOT,
    seasons: list[str] = STUDY_SEASONS,
) -> None:
    """Measure play rates by injury-report status (MVP-002); fetches reports into bronze."""
    configure_logging()
    client = make_injury_client()
    try:
        study = availability_study.run(SnapshotStore(_root(root)), client, SystemClock(), seasons)
    finally:
        client.close()
    availability_study.REPORT_OUT.write_text(
        availability_study.report(study, SystemClock().now()), encoding="utf-8"
    )
    availability_study.RATES_OUT.parent.mkdir(parents=True, exist_ok=True)
    availability_study.RATES_OUT.write_text(availability_study.rates_json(study), encoding="utf-8")
    typer.echo(
        f"days={study.days} reports={study.reports} missing={study.missing} "
        f"unknown_layout={study.unknown_layout} unmatched={study.unmatched}"
    )
    for r in study.overall.iter_rows(named=True):
        typer.echo(
            f"{r['status']}: n={r['n']} played={r['rate']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]"
        )


@app.command("brief")
def brief_cmd(
    league: Path | None = LEAGUE_FILE,
    settings: Path | None = BRIEF_SETTINGS,
    sample: bool = typer.Option(False, help="Write a snake-draft sample league first (dry run)"),
    at: str | None = typer.Option(None, help="Pretend it is this UTC time (ISO)"),
) -> None:
    """The daily brief as Telegram markdown (MVP-003); also saved in the workspace's briefs/."""
    configure_logging()
    clock = FrozenClock(datetime.fromisoformat(at)) if at else SystemClock()
    w = workspace.get()
    week = w.read_parquet(daily_brief.WEEK)
    values = w.read_parquet(daily_brief.VALUES)
    if sample:
        lg = json.dumps(daily_brief.sample_league(values.filter(pl.col("variant") == "all")))
        if league:
            league.parent.mkdir(parents=True, exist_ok=True)
            league.write_text(lg, encoding="utf-8")
        else:
            w.write_text(daily_brief.LEAGUE, lg)
    league_text = league.read_text(encoding="utf-8") if league else w.read_text(daily_brief.LEAGUE)
    settings_text = (
        settings.read_text(encoding="utf-8") if settings else w.read_text(jobs_nba.LEAGUE_SETTINGS)
    )
    rules = parse_league_settings(settings_text)
    day = game_date(clock.now())
    out = daily_brief.compose(
        week,
        values,
        daily_brief.league_from_text(league_text, week),
        rules.roster_slots,
        day,
        daily_brief.next_week_table(w),
    )
    daily_brief.publish(out, day, clock.now(), w)
    typer.echo(out.markdown)


def make_telegram() -> telegram.Telegram:  # pragma: no cover - needs the real token
    token = get_settings().telegram_bot_token
    if token is None:
        msg = "TELEGRAM_BOT_TOKEN is not set in .env"
        raise typer.BadParameter(msg)
    return telegram.Telegram(token)


@app.command("telegram-setup")
def telegram_setup_cmd() -> None:
    """Find the owner's chat id from a message sent to the bot and save it (MVP-004)."""
    bot = make_telegram()
    try:
        ids = bot.chat_ids()
    finally:
        bot.close()
    if len(ids) != 1:
        typer.echo(f"found {len(ids)} chats: send your bot one message on Telegram, then re-run")
        raise typer.Exit(1)
    telegram.save_chat(ids[0])
    typer.echo("chat saved to data/telegram_chat.json")


@app.command("send-brief")
def send_brief_cmd(
    path: Path | None = BRIEF_FILE,
    text: str | None = typer.Option(None, help="Send this text instead (e.g. a test)"),
) -> None:
    """Send the brief (or a test text) to the owner's Telegram chat (MVP-004)."""
    chat = telegram.load_chat()
    if chat is None:
        typer.echo("no chat saved: run `telegram-setup` first")
        raise typer.Exit(1)
    if text is None:
        day = game_date(SystemClock().now())
        text = (
            path.read_text(encoding="utf-8")
            if path
            else workspace.get().read_text(daily_brief.brief_path(day, "md"))
        )
    bot = make_telegram()
    try:
        bot.send(chat, text)
    finally:
        bot.close()
    typer.echo(f"sent {len(text)} characters")


def _alert(text: str) -> None:
    """Best effort: tell the owner on Telegram that the morning run failed (no secrets in text)."""
    send = jobs_nba.telegram_sender()
    if send is None:
        return
    try:
        send(text)
    except Exception:  # the alert must never hide the original failure
        return


def _runner_context(root: str | None, clock: SystemClock) -> jobs_nba.Context:  # pragma: no cover
    return jobs_nba.Context(
        SnapshotStore(_root(root)),
        clock,
        week_projection.SEASON,
        make_cdn_client,
        make_client,
        make_injury_client,
        jobs_nba.telegram_sender(),
        jobs_nba.LEAGUE_SETTINGS,
        get_settings().serve_root,
        workspace.get(),
        _warehouse_factory(),
    )


def _warehouse_factory() -> Callable[[], Warehouse] | None:
    """BigQuery for the draft-values job, only when GCP_PROJECT is set (never guess a project)."""
    project = get_settings().gcp_project
    return (lambda: make_warehouse(project)) if project else None


def _run_jobs(
    targets: list[str], partitions: list[date], root: str | None, *, include_fetch: bool = True
) -> None:
    """Run jobs under the lock, log to the workspace's run log; on failure alert and exit 1."""
    configure_logging()
    clock = SystemClock()
    ctx = _runner_context(root, clock)
    try:
        with jobs.RunLock(jobs_nba.LOCK, clock):
            runner = jobs.Runner(
                jobs_nba.registry(ctx, include_fetch=include_fetch),
                workspace.RunLogSink(workspace.get(), jobs_nba.RUNS),
                clock,
            )
            results = runner.run(targets, partitions=partitions)
    finally:
        ctx.close()
    for r in results:
        part = f" {r.partition}" if r.partition else ""
        typer.echo(
            f"{r.job}{part}: {r.status} rows={r.rows} {r.seconds:.1f}s {r.error or ''}".rstrip()
        )
    status = jobs.overall(results)
    if status == "failed":
        bad = ", ".join(sorted({r.job for r in results if r.status == "failed"}))
        _alert(
            f"Daily run failed ({bad}). "
            "Logs: data/logs/daily-run.log on the PC, or the Cloud Run job."
        )
        raise typer.Exit(1)


@app.command("run")
def run_cmd(
    job: list[str] = RUN_JOBS,
    start: str | None = typer.Option(None, help="First game date (ISO) for daily partitions"),
    end: str | None = typer.Option(None, help="Last game date (ISO); default = start"),
    root: str | None = ROOT,
) -> None:
    """Run jobs with their dependencies (FND-011). Shortcuts: `run daily` = the whole morning chain
    with catch-up on one machine; `run fetch` = only the NBA fetch with catch-up (the owner's PC);
    `run cloud` = everything else, without the fetch (the Cloud Run job; D-63)."""
    clock = SystemClock()
    include_fetch = True
    if job in (["daily"], ["fetch"]):
        partitions = jobs.missing_partitions(
            workspace.RunLogSink(workspace.get(), jobs_nba.RUNS),
            "cdn-day",
            through=daily.default_day(clock.now()),
            max_days=jobs_nba.CATCH_UP_DAYS,
        )
        targets = list(jobs_nba.DAILY_TARGETS if job == ["daily"] else jobs_nba.FETCH_TARGETS)
    elif job == ["cloud"]:
        partitions, targets, include_fetch = [], list(jobs_nba.CLOUD_TARGETS), False
    else:
        first = date.fromisoformat(start) if start else daily.default_day(clock.now())
        last = date.fromisoformat(end) if end else first
        partitions = [first + timedelta(days=i) for i in range((last - first).days + 1)]
        targets = job
    _run_jobs(targets, partitions, root, include_fetch=include_fetch)


@app.command("watchdog")
def watchdog_cmd(
    mode: str = typer.Option(
        "daily", help="daily (09:00: missed run, stale data) or uptime (15 min)"
    ),
) -> None:  # pragma: no cover - wiring; the checks are unit-tested in test_watchdog.py
    """INFRA-005: alert on Telegram about what the daily job can't report itself."""
    import urllib.request  # noqa: PLC0415

    from fantasy_core.settings import get_settings  # noqa: PLC0415
    from fantasy_pipeline import watchdog  # noqa: PLC0415

    configure_logging()
    s = get_settings()
    send = jobs_nba.telegram_sender() or (lambda _text: None)
    now = SystemClock().now()
    work = workspace.get()
    if mode == "daily":
        watchdog.daily_checks(work, now, send, muted=s.watchdog_muted)
        return

    def status(url: str) -> int:
        with urllib.request.urlopen(url, timeout=20) as r:  # noqa: S310 - fixed https URLs
            return int(r.status)

    urls = {"site": s.site_url, "api": s.api_url.rstrip("/") + "/system/health"}
    watchdog.uptime_checks(
        work, now, watchdog.http_probe(urls, status), send, muted=s.watchdog_muted
    )


@app.command("daily-run")
def daily_run_cmd(root: str | None = ROOT) -> None:
    """The morning chain (MVP-005, now on the FND-011 runner): catch-up of missed game days,
    refresh, week projection, brief and Telegram; a failure alerts and exits non-zero."""
    run_cmd(job=["daily"], start=None, end=None, root=root)


@app.command("dist-backtest")
def dist_backtest_cmd(root: str | None = ROOT) -> None:
    """DEC-002: the pre-registered negative-binomial vs Poisson test; writes the report."""
    configure_logging()
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), dist_backtest.SEASONS)
    res = distribution_backtest.run(logs)
    dist_backtest.REPORT.write_text(
        dist_backtest.report(res, SystemClock().now()), encoding="utf-8"
    )
    wins = int((res.table["ci_hi"] < 0).sum())
    typer.echo(f"ships={res.ships} categories_better={wins}/9 rows={res.rows}")


@app.command("sim-backtest")
def sim_backtest_cmd(root: str | None = ROOT) -> None:
    """DEC-003: the pre-registered simulation vs normal-approximation test; writes the report."""
    configure_logging()
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), ["2025-26"])
    res = simulation_backtest.run(logs)
    sim_backtest.REPORT.write_text(sim_backtest.report(res, SystemClock().now()), encoding="utf-8")
    typer.echo(
        f"ships={res.ships} pooled={res.pooled_diff:+.4f} "
        f"ci=({res.ci[0]:+.4f}, {res.ci[1]:+.4f}) matchups={res.matchups}"
    )


@app.command("lineup-replay")
def lineup_replay_cmd(root: str | None = ROOT) -> None:
    """DEC-007: the pre-registered optimiser-vs-greedy replay over 2025-26; writes the report."""
    configure_logging()
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), ["2025-26"])
    values = workspace.get().read_parquet(daily_brief.VALUES).filter(pl.col("variant") == "all")
    res = lineup_replay.run(logs, values)
    lineup_replay_report.REPORT.write_text(
        lineup_replay_report.report(res, values, SystemClock().now()), encoding="utf-8"
    )
    typer.echo(
        f"ships={res.ships} lineups={res.lineups} more_active={res.better_count} "
        f"more_value={res.better_value} worse={res.worse} illegal={res.illegal} "
        f"max_ms={res.max_seconds * 1000:.0f}"
    )


@app.command("repl-fill-replay")
def repl_fill_replay_cmd(  # noqa: PLR0913, PLR0917 - CLI options
    root: str | None = ROOT,
    project: str = PROJECT,
    settings: Path = SETTINGS,
    drafts: int = 40,
    il_slots: int = typer.Option(
        3, help="IL slots per team in the decisive replay (pre-registered)"
    ),
    target: str = typer.Option("2026-27", help="Season for the before/after table"),
    method: str = typer.Option("H1+aging+M1", help="The shipped projection method"),
) -> None:
    """DRAFT-011: replay missed-games-at-zero vs replacement fill; writes the report."""
    configure_logging()
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    wh = make_warehouse(project)
    values = draft_replay_run.fill_values(wh, rules)
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), [draft_replay_run.TARGET])
    vals = {
        s: dict(zip(v["nba_player_id"].to_list(), v["value"].to_list(), strict=True))
        for s, v in values.items()
    }
    any_v = next(iter(values.values()))
    elig = {
        p: eligibility(pos)
        for p, pos in zip(
            any_v["nba_player_id"].to_list(), any_v["nba_position"].to_list(), strict=True
        )
    }
    days = draft_replay_run.days_from_logs(logs)
    with_il = draft_replay.run(vals, elig, days, drafts=drafts, il_slots=il_slots)
    without_il = draft_replay.run(vals, elig, days, drafts=drafts)
    before = draft_values.build_values(wh, rules, target, method)
    after = draft_values.build_values(wh, rules, target, method, fill=True)
    draft_replay_run.FILL_REPORT.write_text(
        draft_replay_run.fill_report(
            with_il, without_il, before, after, il_slots, SystemClock().now()
        ),
        encoding="utf-8",
    )
    for name, r in (("with IL", with_il), ("without", without_il)):
        typer.echo(f"{name}: diff={r.diff:+.4f} ci=({r.ci[0]:+.4f}, {r.ci[1]:+.4f})")


@app.command("robust-replay")
def robust_replay_cmd(  # noqa: PLR0913, PLR0917 - CLI options
    root: str | None = ROOT,
    project: str = PROJECT,
    settings: Path = SETTINGS,
    drafts: int = 40,
    il_slots: int = typer.Option(
        3, help="IL slots per team in the decisive replay (pre-registered)"
    ),
    target: str = typer.Option("2026-27", help="Season for the before/after table"),
    method: str = typer.Option("H1+aging+M1", help="The shipped projection method"),
) -> None:
    """DRAFT-012: replay injury-robust minutes/games vs the current method; writes the report."""
    configure_logging()
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    wh = make_warehouse(project)
    values = draft_replay_run.robust_values(wh, rules)
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), [draft_replay_run.TARGET])
    vals = {
        s: dict(zip(v["nba_player_id"].to_list(), v["value"].to_list(), strict=True))
        for s, v in values.items()
    }
    any_v = next(iter(values.values()))
    elig = {
        p: eligibility(pos)
        for p, pos in zip(
            any_v["nba_player_id"].to_list(), any_v["nba_position"].to_list(), strict=True
        )
    }
    days = draft_replay_run.days_from_logs(logs)
    with_il = draft_replay.run(vals, elig, days, drafts=drafts, il_slots=il_slots)
    without_il = draft_replay.run(vals, elig, days, drafts=drafts)
    before = draft_values.build_values(wh, rules, target, method)
    after = draft_values.build_values(wh, rules, target, method + draft_projection.ROBUST)
    draft_replay_run.ROBUST_REPORT.write_text(
        draft_replay_run.fill_report(
            with_il,
            without_il,
            before,
            after,
            il_slots,
            SystemClock().now(),
            draft_replay_run.ROBUST_CMP,
        ),
        encoding="utf-8",
    )
    for name, r in (("with IL", with_il), ("without", without_il)):
        typer.echo(f"{name}: diff={r.diff:+.4f} ci=({r.ci[0]:+.4f}, {r.ci[1]:+.4f})")


@app.command("returners-eval")
def returners_eval_cmd(  # noqa: PLR0913, PLR0917 - CLI options
    root: str | None = ROOT,
    project: str = PROJECT,
    settings: Path = SETTINGS,
    drafts: int = 40,
    il_slots: int = typer.Option(
        3, help="IL slots per team in the decisive replay (pre-registered)"
    ),
    target: str = typer.Option("2026-27", help="Season for the before/after table"),
    method: str = typer.Option("H1+aging+M1", help="The shipped projection method"),
) -> None:
    """DRAFT-022: the three pre-registered returners checks; writes the report."""
    configure_logging()
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    wh = make_warehouse(project)
    seasons, _ = draft_projection._inputs(wh)
    rows = returners_report.fold_rows(seasons, draft_replay_run.TARGET)
    acc = returners_report.accuracy(rows)
    gap = returners_report.calibration_gap(rows)
    values = draft_replay_run.returners_values(wh, rules)
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), [draft_replay_run.TARGET])
    vals = {
        s: dict(zip(v["nba_player_id"].to_list(), v["value"].to_list(), strict=True))
        for s, v in values.items()
    }
    any_v = next(iter(values.values()))
    elig = {
        p: eligibility(pos)
        for p, pos in zip(
            any_v["nba_player_id"].to_list(), any_v["nba_position"].to_list(), strict=True
        )
    }
    days = draft_replay_run.days_from_logs(logs)
    with_il = draft_replay.run(vals, elig, days, drafts=drafts, il_slots=il_slots)
    without_il = draft_replay.run(vals, elig, days, drafts=drafts)
    before = draft_values.build_values(wh, rules, target, method)
    after = draft_values.build_values(wh, rules, target, method + draft_projection.RETURN)
    now = SystemClock().now()
    replay_text = draft_replay_run.fill_report(
        with_il, without_il, before, after, il_slots, now, draft_replay_run.RETURN_CMP
    )
    lillard = returners_report.lillard_line(before, after)
    decision = returners_report.decide(acc, gap, with_il.ci[0])
    returners_report.REPORT.write_text(
        returners_report.render(rows, acc, gap, with_il.ci[0], decision, replay_text, lillard, now),
        encoding="utf-8",
    )
    typer.echo(
        f"accuracy ci={acc.ci}, calibration gap={gap:.3f}, replay ci_low={with_il.ci[0]:+.4f}"
    )
    typer.echo("decision: " + ("SHIP R" if decision.ship else "KEEP current"))


@app.command("draft-replay")
def draft_replay_cmd(
    root: str | None = ROOT,
    project: str = PROJECT,
    settings: Path = SETTINGS,
    drafts: int = 40,
    baseline: str = typer.Option("B0", help="Baseline strategy: B0 (last season) or B1 (Marcel)"),
) -> None:
    """DRAFT-009: leak-free draft strategy replay on 2025-26; writes the report."""
    configure_logging()
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    values = draft_replay_run.leak_free_values(make_warehouse(project), rules, baseline=baseline)
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), [draft_replay_run.TARGET])
    vals = {
        s: dict(zip(v["nba_player_id"].to_list(), v["value"].to_list(), strict=True))
        for s, v in values.items()
    }
    any_v = next(iter(values.values()))
    elig = {
        p: eligibility(pos)
        for p, pos in zip(
            any_v["nba_player_id"].to_list(), any_v["nba_position"].to_list(), strict=True
        )
    }
    res = draft_replay.run(vals, elig, draft_replay_run.days_from_logs(logs), drafts=drafts)
    draft_replay_run.REPORTS[baseline].write_text(
        draft_replay_run.report(res, values, SystemClock().now()), encoding="utf-8"
    )
    typer.echo(
        f"diff={res.diff:+.4f} ci=({res.ci[0]:+.4f}, {res.ci[1]:+.4f}) "
        f"better={res.a_better_share:.0%}"
    )


@app.command("inseason-backtest")
def inseason_backtest_cmd(root: str | None = ROOT, project: str = PROJECT) -> None:
    """ANL-005: the pre-registered in-season update test; writes the report."""
    configure_logging()
    priors = inseason_run.leak_free_priors(make_warehouse(project), inseason_run.SEASONS)
    logs = dist_backtest.load_logs(SnapshotStore(_root(root)), inseason_run.SEASONS)
    res = inseason_backtest.run(logs.with_columns(pl.col("PLAYER_ID").cast(pl.Int64)), priors)
    inseason_run.REPORT.write_text(inseason_run.report(res, SystemClock().now()), encoding="utf-8")
    wins = int((res.table["ci_hi"] < 0).sum())
    typer.echo(f"ships={res.ships} categories_better={wins}/9 rows={res.rows}")


@app.command("moves-replay")
def moves_replay_cmd(
    root: str | None = ROOT, project: str = PROJECT, settings: Path = SETTINGS, draws: int = 1000
) -> None:
    """DEC-008: the pre-registered add/drop replay on the 2025-26 holdout; writes the report."""
    configure_logging()
    rules = parse_league_settings(settings.read_text(encoding="utf-8"))
    squads, weeks, value = moves_replay_run.inputs(
        make_warehouse(project), SnapshotStore(_root(root)), rules
    )
    res = moves_replay.run(squads, weeks, value, draws=draws)
    decided = res.rows["week"].n_unique()
    moves_replay_run.REPORT.write_text(
        moves_replay_run.report(res, decided, SystemClock().now()), encoding="utf-8"
    )
    diff, lo, hi = res.b_minus_a
    typer.echo(f"ships={res.ships} B-A={diff:+.4f} ci=({lo:+.4f}, {hi:+.4f})")
    typer.echo(str(res.summary))
