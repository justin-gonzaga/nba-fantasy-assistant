"""RSCH-008 runner: the pre-registered in-season trend questions on our game logs."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from pathlib import Path

import polars as pl

from dikit.store.snapshot import SnapshotStore
from dikit.time.clock import SystemClock
from fantasy_evaluation import season_trends as st
from fantasy_ingest import nba_cdn, nba_stats
from fantasy_pipeline.warehouse import SEASONS_SQL, Warehouse

REPORT = Path("docs/evaluation/reports/RSCH-008-in-season-trends.md")
SEASONS = [f"{y}-{str(y + 1)[2:]}" for y in range(2015, 2026)]
EXCLUDED = {"2019-20", "2020-21"}  # COVID suspension / 72-game season (pre-registered)
STARS = 60
YOUNG = 23
ROTATION_MPG = 20
PLAYOFF_WEEKS = (date(2027, 3, 1), date(2027, 3, 21))  # league weeks 18-20 (settings)
SEASON_GAMES = 82
WEIGHTS = (1.0, 2.0, 3.0)
TOP = 150
MOVE = 10
Q3_RULE = 15  # w = 2 moving >= 15 of the top 150 by >= 10 ranks -> a DRAFT task
DECISION_W = 2.0
Q1_MIN_R = 0.15


def load_logs(store: SnapshotStore, seasons: list[str]) -> pl.DataFrame:
    frames = []
    for s in seasons:
        req = nba_stats.league_game_log(s, "P")
        payload = store.latest(nba_stats.SOURCE, req.endpoint, req.key)
        if payload is None:
            continue
        frames.append(
            pl.DataFrame(nba_stats.result_set(payload)).with_columns(pl.lit(s).alias("SEASON"))
        )
    return st.tidy(pl.concat(frames, how="diagonal_relaxed"))


def q1(logs: pl.DataFrame) -> st.Persistence:
    deltas = {
        s: st.half_values(logs.filter(pl.col("season") == s))
        for s in SEASONS
        if s not in EXCLUDED and logs.filter(pl.col("season") == s).height
    }
    return st.persistence(st.pair_up(deltas))


def q2(logs: pl.DataFrame, ages: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for s in SEASONS:
        if s in EXCLUDED:
            continue
        season = logs.filter(pl.col("season") == s)
        if not season.height:
            continue
        cutoff = date(int(s[:4]) + 1, 3, 1)
        age = ages.filter(pl.col("season") == s).select("player", "age")
        roles = assign_roles(season.filter(pl.col("day") < cutoff), age)
        rows.append(st.late_season(season, cutoff, roles).with_columns(pl.lit(s).alias("season")))
    return pl.concat(rows)


def assign_roles(pre: pl.DataFrame, age: pl.DataFrame, stars: int = STARS) -> pl.DataFrame:
    """Roles from pre-cutoff games only: top-`stars` by value > age <= 23 > >= 20 mpg rotation."""
    agg = pre.group_by("player").agg(
        pl.len().alias("games"), pl.col("min").sum(), *[pl.col(c).sum() for c in st.STATS]
    )
    agg = agg.with_columns(pl.Series("value", st.value_of(agg)))
    top = agg.sort("value", descending=True).head(stars)["player"].to_list()
    return (
        agg.join(age, on="player", how="left")
        .with_columns(
            pl.when(pl.col("player").is_in(top))
            .then(pl.lit("star"))
            .when(pl.col("age") <= YOUNG)
            .then(pl.lit("young"))
            .when(pl.col("min") / pl.col("games") >= ROTATION_MPG)
            .then(pl.lit("rotation"))
            .otherwise(None)
            .alias("role")
        )
        .filter(pl.col("role").is_not_null())
        .select("player", "role")
    )


def q3(
    values: pl.DataFrame, teams: pl.DataFrame, schedule: bytes
) -> tuple[pl.DataFrame, dict[str, int]]:
    games = nba_cdn.parse_schedule(schedule)
    a, b = PLAYOFF_WEEKS
    count: Counter[str] = Counter()
    for g in games:
        if g.regular_season and a <= g.game_date <= b:
            count[g.away] += 1
            count[g.home] += 1
    codes = sorted(count)
    ids = {c: i for i, c in enumerate(codes)}
    v = values.join(teams, on="nba_player_id", how="left").with_columns(
        pl.col("team").replace_strict(ids, default=-1).alias("team_id")
    )
    base = v.select(
        pl.col("nba_player_id").alias("player"),
        pl.col("team_id").alias("team"),
        "value",
        "player_name",
    )
    out = []
    for w in WEIGHTS:
        r = st.playoff_weighted_ranks(base, {ids[c]: n for c, n in count.items()}, SEASON_GAMES, w)
        out.append(r.with_columns(pl.lit(w).alias("w")))
    return pl.concat(out), dict(count)


def run(store: SnapshotStore, wh: Warehouse, values: pl.DataFrame, teams: pl.DataFrame) -> str:
    logs = load_logs(store, SEASONS)
    res = q1(logs)
    ages = wh.read(SEASONS_SQL).select(
        "season",
        pl.col("nba_player_id").cast(pl.Int64).alias("player"),
        pl.col("age").cast(pl.Float64),
    )
    late = q2(logs, ages)
    effects = st.effect_table(late)
    schedule = store.latest(nba_cdn.SOURCE, "schedule", "season=2026-27")
    q3_tab, counts = q3(values, teams, schedule) if schedule else (None, {})
    return report(res, effects, q3_tab, counts, SystemClock().now())


def _ci(value: float | None, lo: float | None, hi: float | None) -> str:
    if value is None or lo is None or hi is None:
        return "—"
    return f"{value:+.2f} ({lo:+.2f} to {hi:+.2f})"


def _effect_rows(effects: pl.DataFrame) -> list[str]:
    rows = []
    for r in effects.iter_rows(named=True):
        games = _ci(r["games_missed_extra"], r["games_missed_extra_lo"], r["games_missed_extra_hi"])
        mpg = _ci(r["mpg_change"], r["mpg_change_lo"], r["mpg_change_hi"])
        flag = "yes" if st.material(r) else "no"
        rows.append(f"| {r['context']} | {r['role']} | {r['n']} | {games} | {mpg} | {flag} |")
    return rows


def _moved(q3_tab: pl.DataFrame, w: float) -> pl.DataFrame:
    return q3_tab.filter((pl.col("w") == w) & (pl.col("rank") <= TOP)).with_columns(
        (pl.col("rank") - pl.col("rank_w")).alias("gain")
    )


def _q3_lines(q3_tab: pl.DataFrame | None, counts: dict[str, int]) -> list[str]:
    if q3_tab is None:
        return ["No 2026-27 schedule snapshot stored: Q3 not computed (no guessed games)."]
    mean = sum(counts.values()) / len(counts)
    lines = [
        f"Team games in those weeks: {min(counts.values())} to {max(counts.values())} "
        f"(mean {mean:.1f}).",
        "",
        "| Playoff-week weight w | Top-150 players moving >= 10 ranks | Biggest risers |",
        "|---|---|---|",
    ]
    for w in WEIGHTS:
        t = _moved(q3_tab, w)
        moved = t.filter(pl.col("gain").abs() >= MOVE).height
        top = t.sort("gain", descending=True).head(3).select("player_name", "gain").iter_rows()
        risers = ", ".join(f"{n} {g:+d}" for n, g in top)
        lines.append(f"| {w:g} | {moved} | {risers} |")
    moved2 = _moved(q3_tab, DECISION_W).filter(pl.col("gain").abs() >= MOVE).height
    verdict = (
        f"**{moved2} move: a pre-registered DRAFT task evaluates playoff weighting.**"
        if moved2 >= Q3_RULE
        else f"**{moved2} move: not material; no model change.**"
    )
    rule = f"w = 2 moving >= {Q3_RULE} of the top 150 by >= {MOVE} ranks"
    return [*lines, "", f"**Decision by the rule** ({rule}): {verdict}"]


def report(
    res: st.Persistence,
    effects: pl.DataFrame,
    q3_tab: pl.DataFrame | None,
    counts: dict[str, int],
    generated: datetime,
) -> str:
    noise = res.ci[0] <= 0 <= res.ci[1] or res.r < Q1_MIN_R
    q1_verdict = (
        "**noise: don't model individual second-half tendencies.**"
        if noise
        else "**a repeatable trait: a model task follows.**"
    )
    task = "`docs/project/tasks/RSCH-008-in-season-trends-and-playoff-schedule.md`"
    lines = [
        "# In-season trends and the fantasy-playoff schedule (RSCH-008)",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M} UTC. Pre-registered in {task}",
        "(with the pre-run amendments). Seasons 2015-16 to 2025-26; "
        f"{', '.join(sorted(EXCLUDED))} excluded from pooled estimates.",
        "",
        '## Q1: is a "second-half player" a repeatable trait?',
        f"Consecutive-season pairs (>= {st.MIN_HALF_GAMES} games each half): "
        f"**{res.n}** player-pairs.",
        "",
        "| Change measured | r (season s vs s+1) | 95 % CI |",
        "|---|---|---|",
        f"| per-game 9-cat value (after minus before the break) | {res.r:+.3f} | "
        f"{res.ci[0]:+.3f} to {res.ci[1]:+.3f} |",
        f"| per-36 value (skill, not role) | {res.r_per36:+.3f} | "
        f"{res.ci_per36[0]:+.3f} to {res.ci_per36[1]:+.3f} |",
        "",
        f"**Decision by the rule** (noise if the CI includes 0 or r < {Q1_MIN_R}): {q1_verdict}",
        "",
        "## Q2: late-season rest and tanking (after 1 Mar)",
        "Extra games missed after 1 Mar relative to the player's own earlier share, and the mpg",
        "change; bootstrap 95 % CIs. Material = >= 2 extra games or >= 3 mpg, CI excluding 0.",
        "",
        "| Context on 1 Mar | Role | n | Extra games missed (95 % CI) | mpg change (95 % CI) "
        "| Material |",
        "|---|---|---|---|---|---|",
        *_effect_rows(effects),
        "",
        "## Q3: fantasy-playoff schedule (league weeks 18-20: 1-21 Mar 2027)",
        *_q3_lines(q3_tab, counts),
        "",
        "## Literature",
        "First/second-half splits regress strongly to the mean in baseball [R-106, R-107];",
        "eliminated NBA teams rest healthy players more [R-108]. No peer-reviewed work on",
        "fantasy-playoff schedule weighting exists (a gap; this report is the evidence).",
        "See `docs/research/lit-in-season-trends.md`.",
        "",
    ]
    return "\n".join(lines)
