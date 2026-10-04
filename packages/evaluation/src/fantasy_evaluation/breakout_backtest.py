"""DRAFT-007 backtests: the minutes model (M1) and the breakout probability (M2).

Pre-registered in docs/architecture/ml-methodology-plan.md Part 1b (§7, §8, §10a; D-54):
- M1: ridge vs LightGBM, selected on SELECT_FOLDS by pooled mpg MAE. The winner ships only if,
  on HOLDOUT_FOLDS, (a) its mpg MAE beats last-season mpg (95 % CI < 0) and (b) H1+aging with its
  minutes beats H1+aging on season-total value rank (pooled 95 % CI > 0).
- M2: logistic regression; shown only if pooled precision@20 beats the base rate (95 % CI > 0)
  and its Brier score beats the base-rate forecast.
Rolling origin [R-50, R-51]; bootstrap stratified by fold [R-54]; rare-event metrics [R-89, R-90].
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from dikit.methods import regression as rg
from fantasy_evaluation import preseason_backtest as bt
from fantasy_models.preseason import breakouts as b
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.schema import history_before, season_of, start_year

SELECT_FOLDS = ("2018-19", "2019-20", "2020-21", "2021-22")
HOLDOUT_FOLDS = ("2022-23", "2023-24", "2024-25", "2025-26")
FIRST_TRAIN = "2016-17"  # the first target with a previous season in the data (2015-16)
TOP_K = (20, 50)
GROWTH_MIN_GP = 0.6  # D-55: growth population = played >= 60 % of games last season


def _verdict(ok: bool) -> str:
    return "PASS" if ok else "fail"


def _mean(s: pl.Series) -> float:
    v = s.mean()
    return float(v) if isinstance(v, int | float) else 0.0


def _targets_between(first: str, before: str) -> list[str]:
    return [season_of(y) for y in range(start_year(first), start_year(before))]


def _stratified_mean_ci(
    per_fold: list[np.ndarray], n_boot: int, seed: int
) -> tuple[float, float, float]:
    """Mean over folds of per-player values; CI by resampling players within each fold."""
    rng = np.random.default_rng(seed)
    point = float(np.mean([a.mean() for a in per_fold]))
    boots = np.mean(
        [a[bs.resample_idx(len(a), n_boot, rng)].mean(axis=1) for a in per_fold], axis=0
    )
    lo, hi = bs.ci(boots)
    return point, lo, hi


# ---------------------------------------------------------------- M1 minutes
@dataclass
class MinutesResult:
    fold_mae: pl.DataFrame  # target, model, mae, n
    winner: str
    mae_diff: tuple[float, float, float]  # winner - last on holdout: point, lo, hi
    rank_diff: dict[str, float]  # pooled H1+aging+M1 vs H1+aging on holdout
    ships: bool
    reasons: list[str] = field(default_factory=list)


def _m1_predictions(
    seasons: pl.DataFrame, target: str, model: str
) -> tuple[pl.DataFrame, pl.DataFrame]:
    train = b.training_rows(seasons, _targets_between(FIRST_TRAIN, target))
    feats = b.features(
        history_before(seasons, target), b.rosters_from_season(seasons, target), target
    )
    reg: rg.Regressor = rg.Ridge() if model == "ridge" else b.GBM()
    return b.predict_mpg(reg, train, feats), feats


def minutes_backtest(
    seasons: pl.DataFrame, draft: pl.DataFrame, n_boot: int = 2000, seed: int = 0
) -> MinutesResult:
    rows, errs = [], {}
    preds: dict[tuple[str, str], pl.DataFrame] = {}
    for target in (*SELECT_FOLDS, *HOLDOUT_FOLDS):
        actual = seasons.filter(
            (pl.col("season") == target) & (pl.col("games_played") >= bt.MIN_GAMES)
        ).select("nba_player_id", (pl.col("minutes") / pl.col("games_played")).alias("mpg"))
        for model in ("ridge", "gbm"):
            p, feats = _m1_predictions(seasons, target, model)
            preds[(target, model)] = p
            j = actual.join(p, on="nba_player_id").join(
                feats.select("nba_player_id", "mpg_last"), on="nba_player_id"
            )
            errs[(target, model)] = np.abs(j["mpg_m1"].to_numpy() - j["mpg"].to_numpy())
            errs[(target, "last")] = np.abs(j["mpg_last"].to_numpy() - j["mpg"].to_numpy())
            rows.append(
                {
                    "target": target,
                    "model": model,
                    "mae": float(errs[(target, model)].mean()),
                    "n": j.height,
                }
            )
        rows.append(
            {
                "target": target,
                "model": "last",
                "mae": float(errs[(target, "last")].mean()),
                "n": j.height,
            }
        )
    fold_mae = pl.DataFrame(rows)
    sel = fold_mae.filter(
        pl.col("target").is_in(SELECT_FOLDS) & pl.col("model").is_in(["ridge", "gbm"])
    )
    pooled = sel.group_by("model").agg(pl.col("mae").mean()).sort("mae")
    winner = str(pooled["model"][0])
    diffs = [errs[(t, winner)] - errs[(t, "last")] for t in HOLDOUT_FOLDS]
    mae_diff = _stratified_mean_ci(diffs, n_boot, seed)

    folds = []
    for target in HOLDOUT_FOLDS:
        override = preds[(target, winner)]

        def with_m1(
            history: pl.DataFrame, t: str, override: pl.DataFrame = override
        ) -> pl.DataFrame:
            return m.hybrid(history, t, aging=True, mpg_override=override)

        methods: dict[str, bt.Method] = {
            "B0": m.last_season,
            "H1+aging": m.hybrid_aging,
            "H1+aging+M1": with_m1,
        }
        fold, _ = bt.run_fold(seasons, draft, target, methods=methods, n_boot=n_boot, seed=seed)
        folds.append(fold)
    rank_diff = bt.pooled_rank_diff(folds, "H1+aging+M1 vs H1+aging")
    ok_a, ok_b = mae_diff[2] < 0, rank_diff["lo"] > 0
    reasons = [
        f"selection ({SELECT_FOLDS[0]}..{SELECT_FOLDS[-1]}): pooled mpg MAE "
        + ", ".join(f"{r['model']} {r['mae']:.3f}" for r in pooled.iter_rows(named=True))
        + f" -> {winner}",
        f"(a) holdout mpg MAE {winner} - last season: {mae_diff[0]:+.3f} "
        f"(95 % CI {mae_diff[1]:+.3f} to {mae_diff[2]:+.3f}) -> {_verdict(ok_a)}",
        f"(b) holdout season-total rank H1+aging+M1 - H1+aging: {rank_diff['diff']:+.3f} "
        f"(95 % CI {rank_diff['lo']:+.3f} to {rank_diff['hi']:+.3f}), positive in "
        f"{int(rank_diff['folds_positive'])}/{int(rank_diff['folds'])} folds -> {_verdict(ok_b)}",
    ]
    return MinutesResult(fold_mae, winner, mae_diff, rank_diff, ok_a and ok_b, reasons)


# ---------------------------------------------------------------- M2 breakouts
@dataclass
class BreakoutResult:
    folds: pl.DataFrame  # target, base_rate, p_at_20, p_at_50, brier, brier_base, ndcg20, n
    lift20: tuple[float, float, float]  # pooled precision@20 - base rate: point, lo, hi
    brier: tuple[float, float]  # pooled model, base-rate forecast
    reliability: pl.DataFrame  # bin, mean_p, observed, n
    sensitivity: pl.DataFrame  # jump, base_rate, p_at_20
    hindsight: pl.DataFrame  # 2025-26 top-20 flags + actual breakouts
    ships: bool
    reasons: list[str] = field(default_factory=list)
    model: rg.Logistic | None = None


def _m2_frame(  # noqa: PLR0913, PLR0917
    seasons: pl.DataFrame,
    target: str,
    jump: int,
    top: int,
    min_gp: float = 0.0,
    pre: pl.DataFrame | None = None,
) -> pl.DataFrame:
    """`min_gp` > 0 restricts the population to players who played that share of games (D-55)."""
    feats = b.features(
        history_before(seasons, target), b.rosters_from_season(seasons, target), target
    )
    feats = feats.filter(pl.col("gp_frac_last") >= min_gp)
    if pre is not None:  # DRAFT-008 pre-season features
        feats = b.add_preseason(feats, pre.filter(pl.col("season") == target))
    return feats.join(
        b.breakout_labels(seasons, target, jump, top), on="nba_player_id", how="inner"
    )


def _fit_m2(  # noqa: PLR0913, PLR0917
    seasons: pl.DataFrame,
    target: str,
    jump: int,
    top: int,
    min_gp: float = 0.0,
    pre: pl.DataFrame | None = None,
) -> rg.Logistic:
    cols = b.M2_PRE_FEATURES if pre is not None else b.M2_FEATURES
    train = pl.concat(
        [
            _m2_frame(seasons, s, jump, top, min_gp, pre)
            for s in _targets_between(FIRST_TRAIN, target)
        ]
    )
    return rg.Logistic().fit(b.matrix(train, cols), train["breakout"].to_numpy().astype(float))


def _ndcg(gain_sorted_by_pred: np.ndarray, ideal: np.ndarray, k: int) -> float:
    disc = 1 / np.log2(np.arange(2, k + 2))
    idcg = float((np.sort(ideal)[::-1][:k] * disc[: min(k, len(ideal))]).sum())
    return (
        float((gain_sorted_by_pred[:k] * disc[: min(k, len(gain_sorted_by_pred))]).sum() / idcg)
        if idcg
        else 0.0
    )


def breakout_backtest(  # noqa: PLR0913, PLR0917 - knobs mirror the pre-registered rule
    seasons: pl.DataFrame,
    n_boot: int = 2000,
    seed: int = 0,
    jump: int = 50,
    top: int = 150,
    min_gp: float = 0.0,
    pre: pl.DataFrame | None = None,
) -> BreakoutResult:
    cols = b.M2_PRE_FEATURES if pre is not None else b.M2_FEATURES
    rng = np.random.default_rng(seed)
    rows, lifts_boot, all_p, all_y, all_base, briers, briers_base = [], [], [], [], [], [], []
    frames = {}
    for target in (*SELECT_FOLDS, *HOLDOUT_FOLDS):
        model = _fit_m2(seasons, target, jump, top, min_gp, pre)
        test = _m2_frame(seasons, target, jump, top, min_gp, pre)
        p = model.predict_proba(b.matrix(test, cols))
        y = test["breakout"].to_numpy().astype(float)
        order = np.argsort(-p)
        base_train = float(
            np.mean(
                [
                    _m2_frame(seasons, s, jump, top, min_gp, pre)["breakout"].mean()
                    for s in _targets_between(FIRST_TRAIN, target)
                ]
            )
        )
        gain = np.maximum(test["rank_last"].to_numpy() - test["rank"].to_numpy(), 0) * y
        rows.append(
            {
                "target": target,
                "n": len(y),
                "base_rate": float(y.mean()),
                "p_at_20": float(y[order[:20]].mean()),
                "p_at_50": float(y[order[:50]].mean()),
                "brier": float(np.mean((p - y) ** 2)),
                "brier_base": float(np.mean((base_train - y) ** 2)),
                "ndcg20": _ndcg(gain[order], gain, 20),
            }
        )
        idx = bs.resample_idx(len(y), n_boot, rng)
        top20 = np.array([y[i][np.argsort(-p[i])[:20]].mean() - y[i].mean() for i in idx])
        lifts_boot.append(top20)
        all_p.append(p)
        all_y.append(y)
        all_base.append(np.full(len(y), base_train))
        briers.append((p - y) ** 2)
        briers_base.append((base_train - y) ** 2)
        frames[target] = test.with_columns(pl.Series("p_breakout", p))
    folds = pl.DataFrame(rows)
    lift_point = _mean(folds["p_at_20"] - folds["base_rate"])
    lo, hi = bs.ci(np.mean(lifts_boot, axis=0))
    pp, yy = np.concatenate(all_p), np.concatenate(all_y)
    brier = (float(np.concatenate(briers).mean()), float(np.concatenate(briers_base).mean()))
    bins = np.minimum((pp * 10).astype(int), 9)
    reliability = (
        pl.DataFrame({"bin": bins, "p": pp, "y": yy})
        .group_by("bin")
        .agg(
            pl.col("p").mean().alias("mean_p"),
            pl.col("y").mean().alias("observed"),
            pl.len().alias("n"),
        )
        .sort("bin")
    )
    sens = []
    for j in (30, 50, 80):  # every row on the same holdout folds (review finding)
        vals = []
        for target in HOLDOUT_FOLDS:
            mdl = _fit_m2(seasons, target, j, top, min_gp, pre)
            tf = _m2_frame(seasons, target, j, top, min_gp, pre)
            pr = mdl.predict_proba(b.matrix(tf, cols))
            yv = tf["breakout"].to_numpy()
            vals.append((float(yv.mean()), float(yv[np.argsort(-pr)[:20]].mean())))
        sens.append(
            {
                "jump": j,
                "base_rate": float(np.mean([v[0] for v in vals])),
                "p_at_20": float(np.mean([v[1] for v in vals])),
            }
        )
    last = frames[HOLDOUT_FOLDS[-1]].with_columns(
        pl.col("p_breakout").rank("ordinal", descending=True).alias("model_rank")
    )
    hindsight = (
        last.filter((pl.col("model_rank") <= TOP_K[0]) | (pl.col("breakout") == 1))
        .select("nba_player_id", "model_rank", "p_breakout", "rank_last", "rank", "breakout")
        .sort("model_rank")
    )
    ok = lo > 0 and brier[0] < brier[1]
    reasons = [
        f"pooled precision@20 - base rate: {lift_point:+.3f} "
        f"(95 % CI {lo:+.3f} to {hi:+.3f}) -> {_verdict(lo > 0)}",
        f"pooled Brier: model {brier[0]:.4f} vs base-rate forecast {brier[1]:.4f} "
        f"-> {_verdict(brier[0] < brier[1])}",
    ]
    final = _fit_m2(seasons, season_of(start_year(HOLDOUT_FOLDS[-1]) + 1), jump, top, min_gp, pre)
    return BreakoutResult(
        folds,
        (lift_point, lo, hi),
        brier,
        reliability,
        pl.DataFrame(sens),
        hindsight,
        ok,
        reasons,
        final,
    )


# ---------------------------------------------------------------- DRAFT-008 pre-season signal
@dataclass
class PreseasonMinutesResult:
    fold_mae: pl.DataFrame  # target, model (M1, M1pre), mae, n
    mae_diff: tuple[float, float, float]  # M1pre - M1 on holdout
    rank_diff: dict[str, float]  # pooled H1+aging+M1pre vs H1+aging+M1
    ships: bool
    reasons: list[str] = field(default_factory=list)


def preseason_minutes_backtest(
    seasons: pl.DataFrame, draft: pl.DataFrame, pre: pl.DataFrame, n_boot: int = 2000, seed: int = 0
) -> PreseasonMinutesResult:
    """G-24 / D-57 rule (a): does pre-season role improve the shipped ridge M1 on holdout folds?"""
    rows, diffs, folds = [], [], []
    for target in HOLDOUT_FOLDS:
        targets = _targets_between(FIRST_TRAIN, target)
        feats = b.features(
            history_before(seasons, target), b.rosters_from_season(seasons, target), target
        )
        feats_pre = b.add_preseason(feats, pre.filter(pl.col("season") == target))
        base = b.predict_mpg(rg.Ridge(), b.training_rows(seasons, targets), feats)
        with_pre = b.predict_mpg(
            rg.Ridge(),
            b.training_rows(seasons, targets, preseason=pre),
            feats_pre,
            b.M1_PRE_FEATURES,
        )
        actual = seasons.filter(
            (pl.col("season") == target) & (pl.col("games_played") >= bt.MIN_GAMES)
        ).select("nba_player_id", (pl.col("minutes") / pl.col("games_played")).alias("mpg"))
        j = actual.join(base, on="nba_player_id").join(
            with_pre.rename({"mpg_m1": "mpg_pre"}), on="nba_player_id"
        )
        e_base = np.abs(j["mpg_m1"].to_numpy() - j["mpg"].to_numpy())
        e_pre = np.abs(j["mpg_pre"].to_numpy() - j["mpg"].to_numpy())
        diffs.append(e_pre - e_base)
        rows += [
            {"target": target, "model": "M1", "mae": float(e_base.mean()), "n": j.height},
            {"target": target, "model": "M1pre", "mae": float(e_pre.mean()), "n": j.height},
        ]

        def m1(history: pl.DataFrame, t: str, o: pl.DataFrame = base) -> pl.DataFrame:
            return m.hybrid(history, t, aging=True, mpg_override=o)

        def m1pre(history: pl.DataFrame, t: str, o: pl.DataFrame = with_pre) -> pl.DataFrame:
            return m.hybrid(history, t, aging=True, mpg_override=o)

        methods: dict[str, bt.Method] = {
            "B0": m.last_season,
            "H1+aging+M1": m1,
            "H1+aging+M1pre": m1pre,
        }
        fold, _ = bt.run_fold(seasons, draft, target, methods=methods, n_boot=n_boot, seed=seed)
        folds.append(fold)
    mae_diff = _stratified_mean_ci(diffs, n_boot, seed)
    rank_diff = bt.pooled_rank_diff(folds, "H1+aging+M1pre vs H1+aging+M1")
    ok_a, ok_b = mae_diff[2] < 0, rank_diff["lo"] > 0
    reasons = [
        f"(a) holdout mpg MAE M1+pre-season - M1: {mae_diff[0]:+.3f} "
        f"(95 % CI {mae_diff[1]:+.3f} to {mae_diff[2]:+.3f}) -> {_verdict(ok_a)}",
        f"(b) holdout season-total rank H1+aging+M1pre - H1+aging+M1: {rank_diff['diff']:+.3f} "
        f"(95 % CI {rank_diff['lo']:+.3f} to {rank_diff['hi']:+.3f}), positive in "
        f"{int(rank_diff['folds_positive'])}/{int(rank_diff['folds'])} folds -> {_verdict(ok_b)}",
    ]
    return PreseasonMinutesResult(pl.DataFrame(rows), mae_diff, rank_diff, ok_a and ok_b, reasons)
