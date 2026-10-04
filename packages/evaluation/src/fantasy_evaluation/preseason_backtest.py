"""Preseason projection backtest (ml-methodology-plan §4; DRAFT-002 AC2).

Rolling origin [R-50, R-51]: for each target season, every method sees only earlier seasons.
Metrics:
- per-stat MAE of per-game values (players with >= MIN_GAMES realised games)
- rank correlation of a 9-cat value (volume-weighted FG%/FT% impact, TO negative)
- 95 % CIs by a paired bootstrap over players [R-54]
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from dikit.evaluate import scoring as sc
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.project import project_pool, residual_sds
from fantasy_models.preseason.schema import PER_GAME_STATS, history_before

MIN_GAMES = 20
TOP_N = 224  # 16 teams x 14 drafted slots
GATE_STATS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta")
CATEGORY_STATS = ("pts", "reb", "ast", "stl", "blk", "fg3m")
Z80 = 1.2816

Method = Callable[[pl.DataFrame, str], pl.DataFrame]


def default_methods() -> dict[str, Method]:
    def eb_aging(history: pl.DataFrame, target: str) -> pl.DataFrame:
        return m.empirical_bayes(history, target, priors=m.fit_eb(history, target, aging=True))

    return {
        "B0": m.last_season,
        "B1": m.marcel,
        "C1": m.empirical_bayes,
        "C1+aging": eb_aging,
        "H1": m.hybrid,
        "H1+aging": m.hybrid_aging,
    }


def _season_games(seasons: pl.DataFrame, target: str) -> int:
    """Scheduled games per team in `target` (known before the season starts)."""
    games = seasons.filter(pl.col("season") == target).get_column("season_team_games").max()
    return int(games) if isinstance(games, int | float) else 82


def actual_per_game(seasons: pl.DataFrame, target: str, min_games: int = MIN_GAMES) -> pl.DataFrame:
    gp = pl.col("games_played")
    return seasons.filter((pl.col("season") == target) & (gp >= min_games)).select(
        "nba_player_id",
        (pl.col("minutes") / gp).alias("mpg"),
        gp.cast(pl.Float64).alias("games"),
        *[(pl.col(s) / gp).alias(s) for s in PER_GAME_STATS],
    )


def value_score(per_game: pl.DataFrame, reference: pl.DataFrame) -> np.ndarray:
    """9-cat z-sum; means/sds (and league %s) come from `reference` so both sides share a scale."""
    fg_lg = float(reference.get_column("fgm").sum()) / float(reference.get_column("fga").sum())
    ft_lg = float(reference.get_column("ftm").sum()) / float(reference.get_column("fta").sum())

    def cats(df: pl.DataFrame) -> dict[str, np.ndarray]:
        out = {c: df.get_column(c).to_numpy() for c in CATEGORY_STATS}
        out["tov"] = -df.get_column("tov").to_numpy()
        out["fg_impact"] = (df.get_column("fgm") - fg_lg * df.get_column("fga")).to_numpy()
        out["ft_impact"] = (df.get_column("ftm") - ft_lg * df.get_column("fta")).to_numpy()
        return out

    ref, cur = cats(reference), cats(per_game)
    # A constant category carries no information about value; it contributes zero.
    return np.sum([(cur[c] - ref[c].mean()) / (ref[c].std() or 1.0) for c in ref], axis=0)


@dataclass
class FoldResult:
    target: str
    n_players: int  # per-game MAE set (>= MIN_GAMES games)
    mae: pl.DataFrame  # method, stat, mae
    mae_diff: pl.DataFrame  # comparison, stat, diff, lo, hi  (negative = first method better)
    rank: pl.DataFrame  # PRIMARY: season-total value; method, spearman, top_overlap
    rank_diff: (
        pl.DataFrame
    )  # season-total value; comparison, diff, lo, hi (positive = first better)
    rookies: pl.DataFrame  # method, stat, mae, n
    n_rank: int = 0  # season-total ranking set (>= 1 game)
    rank_per_game: pl.DataFrame = field(default_factory=pl.DataFrame)  # method, spearman
    rank_oracle_minutes: pl.DataFrame = field(default_factory=pl.DataFrame)  # rates x realised mpg
    coverage80: dict[str, float] = field(default_factory=dict)
    # bootstrap samples of the season-total rank difference per comparison (for pooling folds)
    rank_diff_samples: dict[str, np.ndarray] = field(default_factory=dict)


def _comparisons(methods: dict[str, Method]) -> list[tuple[str, str]]:
    pairs = [(a, "B0") for a in methods if a != "B0"]
    if "B1" in methods:
        pairs += [(a, "B1") for a in methods if a.startswith(("C1", "H1"))]
    if "H1+aging" in methods:
        pairs += [(a, "H1+aging") for a in methods if a.startswith("H1+aging+")]
    if "H1+aging+M1" in methods and "H1+aging+M1pre" in methods:
        pairs.append(("H1+aging+M1pre", "H1+aging+M1"))
    if "H1" in methods and "C1" in methods:
        pairs.append(("H1", "C1"))
    if "H1+aging" in methods and "H1" in methods:
        pairs.append(("H1+aging", "H1"))
    return pairs


def _align(
    preds: dict[str, pl.DataFrame], actual: pl.DataFrame, games: int
) -> tuple[pl.DataFrame, dict[str, pl.DataFrame]]:
    """Players with a realised season and a projection from every method, same order everywhere.

    Projected games are scaled to the target season's schedule (known before it starts).
    """
    ids = actual.select("nba_player_id")
    for pr in preds.values():
        ids = ids.join(pr.select("nba_player_id"), on="nba_player_id", how="semi")
    ids = ids.sort("nba_player_id")
    act = ids.join(actual, on="nba_player_id", how="left")
    aligned = {
        k: ids.join(pr, on="nba_player_id", how="left").with_columns(
            pl.col("games") * (games / 82) if k != "B0" else pl.col("games")
        )
        for k, pr in preds.items()
    }
    return act, aligned


def _totals(per_game: pl.DataFrame) -> pl.DataFrame:
    return per_game.with_columns([pl.col(s) * pl.col("games") for s in PER_GAME_STATS])


def _rank_tables(
    vals: dict[str, np.ndarray],
    truth: np.ndarray,
    comparisons: list[tuple[str, str]],
    idx: np.ndarray,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, np.ndarray]]:
    n = truth.shape[0]
    top_true = set(np.argsort(-truth)[:TOP_N])
    rank = pl.DataFrame(
        [
            {
                "method": k,
                "spearman": float(sc.spearman(v, truth)),
                "top_overlap": len(top_true & set(np.argsort(-v)[:TOP_N])) / min(TOP_N, n),
            }
            for k, v in vals.items()
        ]
    )
    rows = []
    samples: dict[str, np.ndarray] = {}
    for a, b in comparisons:
        d = sc.spearman(vals[a][idx], truth[idx]) - sc.spearman(vals[b][idx], truth[idx])
        samples[f"{a} vs {b}"] = d
        lo, hi = bs.ci(d)
        point = float(sc.spearman(vals[a], truth) - sc.spearman(vals[b], truth))
        rows.append({"comparison": f"{a} vs {b}", "diff": point, "lo": lo, "hi": hi})
    return rank, pl.DataFrame(rows), samples


def run_fold(  # noqa: PLR0913 - keyword-only knobs
    seasons: pl.DataFrame,
    draft: pl.DataFrame,
    target: str,
    *,
    methods: dict[str, Method] | None = None,
    n_boot: int = 2000,
    seed: int = 0,
    prior_sds: pl.DataFrame | None = None,
) -> tuple[FoldResult, dict[str, pl.DataFrame]]:
    methods = methods or default_methods()
    history = history_before(seasons, target)
    games = _season_games(seasons, target)
    preds = {name: fn(history, target) for name, fn in methods.items()}
    comparisons = _comparisons(methods)

    # Per-game accuracy: players with >= MIN_GAMES games (per-game values are stable).
    actual = actual_per_game(seasons, target)
    act, aligned = _align(preds, actual, games)
    idx = bs.idx(act.height, n_boot, seed)
    stats = (*PER_GAME_STATS, "mpg", "games")
    err = {
        k: {s: np.abs(pr.get_column(s).to_numpy() - act.get_column(s).to_numpy()) for s in stats}
        for k, pr in aligned.items()
    }
    mae = pl.DataFrame(
        [
            {"method": k, "stat": s, "mae": float(e.mean())}
            for k, es in err.items()
            for s, e in es.items()
        ]
    )
    diff_rows = []
    for a, b in comparisons:
        for s in stats:
            d = err[a][s] - err[b][s]
            lo, hi = bs.ci(d[idx].mean(axis=1))
            diff_rows.append(
                {
                    "comparison": f"{a} vs {b}",
                    "stat": s,
                    "diff": float(d.mean()),
                    "lo": lo,
                    "hi": hi,
                }
            )

    # Secondary views on the same set: per-game value, and per-minute rates x realised minutes.
    truth_pg = value_score(act, act)
    rank_pg, _, _ = _rank_tables(
        {k: value_score(pr, act) for k, pr in aligned.items()}, truth_pg, [], idx
    )
    oracle = {
        k: value_score(
            pr.with_columns(
                [pl.col(s) / pl.col("mpg") * act.get_column("mpg") for s in PER_GAME_STATS]
            ),
            act,
        )
        for k, pr in aligned.items()
    }
    rank_or, _, _ = _rank_tables(oracle, truth_pg, [], idx)

    # PRIMARY (G-21b / D-51): season-total value over everyone who played (>= 1 game).
    act_all, aligned_all = _align(preds, actual_per_game(seasons, target, min_games=1), games)
    truth_tot = value_score(_totals(act_all), _totals(act_all))
    vals_tot = {k: value_score(_totals(pr), _totals(act_all)) for k, pr in aligned_all.items()}
    rank_tot, rank_tot_diff, rank_tot_samples = _rank_tables(
        vals_tot, truth_tot, comparisons, bs.idx(act_all.height, n_boot, seed)
    )

    fold = FoldResult(
        target=target,
        n_players=act.height,
        mae=mae,
        mae_diff=pl.DataFrame(diff_rows),
        rank=rank_tot,
        rank_diff=rank_tot_diff,
        rookies=_rookie_eval(seasons, draft, target, actual, games),
        n_rank=act_all.height,
        rank_per_game=rank_pg.select("method", "spearman"),
        rank_oracle_minutes=rank_or.select("method", "spearman"),
        rank_diff_samples=rank_tot_samples,
    )
    if prior_sds is not None:
        fold.coverage80 = _coverage(
            seasons, draft, target, actual=actual, sds=prior_sds, games=games
        )
    return fold, aligned


def _rookie_eval(
    seasons: pl.DataFrame, draft: pl.DataFrame, target: str, actual: pl.DataFrame, games: int
) -> pl.DataFrame:
    """U4: rookie prior by draft bucket vs one league-average rookie line."""
    history = history_before(seasons, target)
    seen = history.select("nba_player_id").unique()
    unseen = actual.join(seen, on="nba_player_id", how="anti")
    rookies = unseen.join(m.this_draft_pick(unseen, draft, target), on="nba_player_id", how="left")
    if rookies.height == 0:
        return pl.DataFrame(
            schema={"method": pl.String, "stat": pl.String, "mae": pl.Float64, "n": pl.Int64}
        )
    priors = m.rookie_priors(history, draft, target)
    bucketed = rookies.select("nba_player_id", "overall_pick").pipe(
        partial(m.rookie_projection, priors=priors, season_games=games)
    )
    flat_row = priors.select(
        *[
            ((pl.col(s) * pl.col("n_rookies")).sum() / pl.col("n_rookies").sum()).alias(s)
            for s in PER_GAME_STATS
        ]
    )
    rows = []
    act = rookies.sort("nba_player_id")
    bk = act.select("nba_player_id").join(bucketed, on="nba_player_id", how="left")
    for s in PER_GAME_STATS:
        a = act.get_column(s).to_numpy()
        rows.append(
            {
                "method": "rookie_prior",
                "stat": s,
                "mae": float(np.nanmean(np.abs(bk.get_column(s).to_numpy() - a))),
                "n": act.height,
            }
        )
        rows.append(
            {
                "method": "league_avg_rookie",
                "stat": s,
                "mae": float(np.mean(np.abs(flat_row.get_column(s)[0] - a))),
                "n": act.height,
            }
        )
    return pl.DataFrame(rows)


def _coverage(  # noqa: PLR0913 - keyword-only inputs
    seasons: pl.DataFrame,
    draft: pl.DataFrame,
    target: str,
    *,
    actual: pl.DataFrame,
    sds: pl.DataFrame,
    games: int,
) -> dict[str, float]:
    """Share of realised per-game values inside the 80 % interval, sds from an earlier fold."""
    from fantasy_models.preseason.project import with_uncertainty  # noqa: PLC0415

    pool = actual.select("nba_player_id").join(
        draft.select("nba_player_id", "overall_pick"), on="nba_player_id", how="left"
    )
    proj = project_pool(seasons, draft, pool, target, m.hybrid, season_games=games)
    long = with_uncertainty(proj, sds)
    act = actual.unpivot(index="nba_player_id", variable_name="stat", value_name="actual")
    j = long.join(act, on=["nba_player_id", "stat"])
    inside = j.with_columns(
        ((pl.col("actual") - pl.col("mean")).abs() <= Z80 * pl.col("sd")).alias("in")
    )
    per = inside.group_by("stat").agg(pl.col("in").mean())
    return {r["stat"]: float(r["in"]) for r in per.iter_rows(named=True)}


def fold_sds(seasons: pl.DataFrame, draft: pl.DataFrame, target: str) -> pl.DataFrame:
    """Residual sds of the shipped (H1) projection for `target`; use them for LATER targets only."""
    actual = actual_per_game(seasons, target)
    pool = actual.select("nba_player_id").join(
        draft.select("nba_player_id", "overall_pick"), on="nba_player_id", how="left"
    )
    games = _season_games(seasons, target)
    proj = project_pool(seasons, draft, pool, target, m.hybrid, season_games=games)
    return residual_sds(proj, actual)


@dataclass(frozen=True)
class GateDecision:
    method: str
    reasons: list[str]


GATE_CANDIDATES = ("H1", "C1", "B1")  # preference order (G-21b / D-51)
CHALLENGERS = {"H1": "H1+aging"}  # D-52: pre-registered challenger for the shipped base


def pooled_rank_diff(folds: list[FoldResult], comparison: str) -> dict[str, float]:
    """Mean season-total rank difference over folds, with a CI from a bootstrap stratified by
    fold (players resampled within each fold, the fold means averaged) [R-54]."""
    samples = np.stack([f.rank_diff_samples[comparison] for f in folds])
    points = [
        f.rank_diff.filter(pl.col("comparison") == comparison).get_column("diff")[0] for f in folds
    ]
    lo, hi = bs.ci(samples.mean(axis=0))
    return {
        "diff": float(np.mean(points)),
        "lo": lo,
        "hi": hi,
        "folds_positive": float(sum(p > 0 for p in points)),
        "folds": float(len(folds)),
    }


def pooled_table(folds: list[FoldResult]) -> pl.DataFrame:
    """Pooled season-total rank difference for every comparison in the folds."""
    comps = list(folds[-1].rank_diff_samples)
    return pl.DataFrame([{"comparison": c, **pooled_rank_diff(folds, c)} for c in comps])


def _mae_wins(fold: FoldResult, comparison: str) -> tuple[int, int]:
    d = fold.mae_diff.filter(
        (pl.col("comparison") == comparison) & pl.col("stat").is_in(GATE_STATS)
    )
    return int(d.filter(pl.col("diff") <= 0).height), int(d.height)


def _challenge(
    fold: FoldResult, folds: list[FoldResult] | None, base: str
) -> tuple[str, str | None]:
    """D-52: the challenger replaces `base` only if its pooled season-total rank beats `base`
    (95 % CI above 0) and it is at least as accurate on >= half of the gate stats."""
    challenger = CHALLENGERS.get(base)
    comp = f"{challenger} vs {base}"
    if challenger is None or not folds or comp not in fold.rank_diff_samples:
        return base, None
    pooled = pooled_rank_diff(folds, comp)
    wins, n = _mae_wins(fold, comp)
    ok = pooled["lo"] > 0 and wins * 2 >= n
    reason = (
        f"{comp}: pooled season-total rank {pooled['diff']:+.3f} (95 % CI {pooled['lo']:+.3f} to "
        f"{pooled['hi']:+.3f}), positive in "
        f"{int(pooled['folds_positive'])}/{int(pooled['folds'])} folds; "
        f"MAE as good or better on {wins}/{n} stats (need {-(-n // 2)}) -> "
        f"{'REPLACES ' + base if ok else base + ' stays'}"
    )
    return (challenger if ok else base), reason


def gate(fold: FoldResult, folds: list[FoldResult] | None = None) -> GateDecision:
    """G-21b / D-51: ship the first candidate that beats B0
    - on season-total value rank: the 95 % CI of the difference excludes 0, pooled over all
      `folds` (bootstrap stratified by fold); with no `folds`, the primary fold alone, and
    - on per-game MAE for >= 2/3 of the gate stats in the primary fold.
    If none qualifies, B0 ships. Then D-52: a pre-registered challenger may replace it."""
    need = int(np.ceil(len(GATE_STATS) * 2 / 3))
    reasons = []
    for cand in GATE_CANDIDATES:
        d = fold.mae_diff.filter(
            (pl.col("comparison") == f"{cand} vs B0") & pl.col("stat").is_in(GATE_STATS)
        )
        if d.height == 0:
            continue
        wins = int(d.filter(pl.col("diff") < 0).height)
        r = fold.rank_diff.filter(pl.col("comparison") == f"{cand} vs B0").row(0, named=True)
        pooled = pooled_rank_diff(folds, f"{cand} vs B0") if folds else None
        rank_lo = pooled["lo"] if pooled else r["lo"]
        ok = wins >= need and rank_lo > 0
        reason = (
            f"{cand} vs B0 ({fold.target}): season-total rank {r['diff']:+.3f} "
            f"(95 % CI {r['lo']:+.3f} to {r['hi']:+.3f}); better MAE on {wins}/{len(GATE_STATS)} "
            f"stats (need {need})"
        )
        if pooled:
            reason += (
                f"; pooled over {int(pooled['folds'])} folds {pooled['diff']:+.3f} "
                f"(95 % CI {pooled['lo']:+.3f} to {pooled['hi']:+.3f}), "
                f"positive in {int(pooled['folds_positive'])}/{int(pooled['folds'])} folds"
            )
        reason += f" -> {'PASS' if ok else 'fail'}"
        reasons.append(reason)
        if ok:
            final, challenge = _challenge(fold, folds, cand)
            if challenge:
                reasons.append(challenge)
            return GateDecision(final, reasons)
    return GateDecision("B0", reasons)
