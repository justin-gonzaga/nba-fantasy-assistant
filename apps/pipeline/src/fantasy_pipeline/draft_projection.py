"""DRAFT-002 jobs: the preseason backtest (report + gate) and the draft-pool projections."""

from __future__ import annotations

from datetime import date

import polars as pl

from dikit.methods import regression as rg
from dikit.time.clock import Clock, SystemClock
from fantasy_evaluation import preseason_backtest as bt
from fantasy_evaluation.preseason_report import render_report
from fantasy_models.preseason import breakouts as b
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.project import project_pool, with_uncertainty
from fantasy_models.preseason.schema import season_of, start_year, validate_seasons
from fantasy_pipeline import overrides
from fantasy_pipeline.warehouse import DRAFT_SQL, PRESEASON_SQL, PROFILE_SQL, SEASONS_SQL, Warehouse

METHODS: dict[str, bt.Method] = {
    "B0": m.last_season,
    "B1": m.marcel,
    "C1": m.empirical_bayes,
    "H1": m.hybrid,
    "H1+aging": m.hybrid_aging,
}
MODEL_VERSION = "draft-v0"
DRAFT_AS_OF = date(2026, 10, 18)  # the draft; override sources must be dated on or before it
M1_METHOD = "H1+aging+M1"  # D-55: H1+aging with the shipped M1 (ridge) minutes
M1_PRE_METHOD = "H1+aging+M1pre"  # D-57: M1 with pre-season role; needs the target's pre-season
# Production opening roster = the current roster (latest capture). Backtests use each player's
# first team of the historical season instead (U10); both stand in for the opening-night roster.
ROSTER_SQL = "select nba_player_id, nba_team_id as team from intermediate.int_player_profile"
FIRST_M1_TRAIN = "2016-17"


ROBUST = "+robust"  # DRAFT-012 (G-26 B): injury-robust minutes input + three-season games
RETURN = "+return"  # DRAFT-022 (G-32): games floor for players back after a lost season


def m1_minutes(
    wh: Warehouse,
    seasons: pl.DataFrame,
    target: str,
    preseason: pl.DataFrame | None = None,
    *,
    robust: bool = False,
) -> pl.DataFrame:
    """Production M1: ridge trained on every past season; opening rosters from the profile."""
    rosters = wh.read(ROSTER_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("team").cast(pl.Int64)
    )
    targets = [season_of(y) for y in range(start_year(FIRST_M1_TRAIN), start_year(target))]
    feats = b.features(
        seasons.filter(pl.col("season") < target), rosters, target, injury_robust=robust
    )
    if preseason is None:
        train = b.training_rows(seasons, targets, injury_robust=robust)
        return b.predict_mpg(rg.Ridge(), train, feats)
    # DRAFT-008: M1 with pre-season role (ships per G-24 / D-57)
    feats = b.add_preseason(feats, preseason.filter(pl.col("season") == target))
    train = b.training_rows(seasons, targets, preseason=preseason, injury_robust=robust)
    return b.predict_mpg(rg.Ridge(), train, feats, b.M1_PRE_FEATURES)


def adjustments(wh: Warehouse) -> pl.DataFrame:
    """DATA-036: the owner-reviewed raises, as a note per player for the values file."""
    rows = overrides.load(overrides.DEFAULT_PATH, DRAFT_AS_OF)
    if rows.height == 0 or not (rows["status"] == "cleared").any():
        return pl.DataFrame(schema={"nba_player_id": pl.Int64, "adjusted": pl.String})
    profile = wh.read(PROFILE_SQL).select(pl.col("nba_player_id").cast(pl.Int64), "player_name")
    return overrides.adjustments(overrides.resolve(rows, profile))


def with_overrides(wh: Warehouse, proj: pl.DataFrame) -> pl.DataFrame:
    rows = overrides.load(overrides.DEFAULT_PATH, DRAFT_AS_OF)
    if rows.height == 0:
        return proj
    profile = wh.read(PROFILE_SQL).select(pl.col("nba_player_id").cast(pl.Int64), "player_name")
    return overrides.apply(proj, overrides.resolve(rows, profile))


def resolve_method(wh: Warehouse, seasons: pl.DataFrame, method: str, target: str) -> bt.Method:
    returners = method.endswith(RETURN)
    method = method.removesuffix(RETURN)
    robust = method.endswith(ROBUST)
    method = method.removesuffix(ROBUST)
    if method == M1_PRE_METHOD:
        pre = wh.read(PRESEASON_SQL).with_columns(pl.col("nba_player_id").cast(pl.Int64))
        if pre.filter(pl.col("season") == target).height == 0:
            msg = (
                f"no {target} pre-season games in int_preseason_role yet: run "
                f"`preseason-backfill --first {target} --last {target}` in draft week, "
                "then dbt build"
            )
            raise ValueError(msg)
        override = m1_minutes(wh, seasons, target, pre, robust=robust)
    elif method == M1_METHOD:
        override = m1_minutes(wh, seasons, target, robust=robust)
    elif method in METHODS and not (robust or returners):
        return METHODS[method]
    else:
        known = sorted([*METHODS, M1_METHOD, M1_PRE_METHOD, M1_METHOD + ROBUST])
        msg = f"unknown method {method!r}; expected one of {known}"
        raise ValueError(msg)

    def with_m1(history: pl.DataFrame, t: str) -> pl.DataFrame:
        return m.hybrid(
            history,
            t,
            aging=True,
            mpg_override=override,
            three_season_games=robust,
            returners=returners,
        )

    return with_m1


def _inputs(wh: Warehouse) -> tuple[pl.DataFrame, pl.DataFrame]:
    seasons = validate_seasons(wh.read(SEASONS_SQL))
    draft = wh.read(DRAFT_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64),
        pl.col("draft_year").cast(pl.Int64),
        pl.col("overall_pick").cast(pl.Int64),
    )
    return seasons, draft


def run_backtest(
    wh: Warehouse,
    first_target: str,
    last_target: str,
    n_boot: int = 2000,
    clock: Clock | None = None,
) -> tuple[str, bt.GateDecision, list[bt.FoldResult]]:
    seasons, draft = _inputs(wh)
    folds: list[bt.FoldResult] = []
    for y in range(start_year(first_target), start_year(last_target) + 1):
        target = season_of(y)
        prev = season_of(y - 1)
        sds = (
            bt.fold_sds(seasons, draft, prev)
            if (seasons.get_column("season") == prev).any()
            else None
        )
        fold, _ = bt.run_fold(seasons, draft, target, n_boot=n_boot, prior_sds=sds)
        folds.append(fold)
    primary = folds[-1]
    decision = bt.gate(primary, folds)
    md = render_report(
        folds, primary, decision, (clock or SystemClock()).now().strftime("%Y-%m-%d %H:%M UTC")
    )
    return md, decision, folds


def build_projections(
    wh: Warehouse, target: str, method: str, clock: Clock | None = None
) -> tuple[pl.DataFrame, tuple[int, int]]:
    """Long table for predictions.preseason_projection plus (projected, pool) counts (AC1)."""
    seasons, draft = _inputs(wh)
    fn = resolve_method(wh, seasons, method, target)
    pool = wh.read(PROFILE_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("overall_pick").cast(pl.Int64)
    )
    proj = project_pool(seasons, draft, pool, target, fn)
    proj = with_overrides(wh, proj)  # D-47 Q2: owner-reviewed absences cap expected games
    last = season_of(start_year(target) - 1)
    sds = bt.fold_sds(seasons, draft, last)  # residual sds of the latest completed season
    long = with_uncertainty(proj, sds).with_columns(
        pl.lit(target).alias("season"),
        pl.lit(method).alias("method"),
        pl.lit(MODEL_VERSION).alias("model_version"),
        pl.lit((clock or SystemClock()).now()).alias("created_at"),
    )
    coverage = (
        long.get_column("nba_player_id").n_unique(),
        pool.get_column("nba_player_id").n_unique(),
    )
    return long.select(
        "season",
        "nba_player_id",
        "stat",
        "mean",
        "sd",
        "source",
        "method",
        "model_version",
        "created_at",
    ), coverage
