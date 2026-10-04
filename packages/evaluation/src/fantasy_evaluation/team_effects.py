"""ANL-010: are team and coach effects real, and does the projection miss them?

Pure estimators over polars/numpy:
- `context_flags`: per player and target season, the context changes known at the draft
  (moved, new coach, pace change, usage freed), from last season's data and the opening-day
  team only.
- `ols` / `holm` / `decide`: the pre-registered test of whether those flags explain the
  model's errors.
- `group_share`: how much of a season-to-season change a grouping (the new team) explains, against a
  permutation null.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import polars as pl
from scipy import stats

GO_SHARE = (
    0.02  # pre-registered (ANL-010 AC2): a flag must explain ≥ 2 % of the value-residual variance
)
GO_ALPHA = 0.05  # … with a Holm-adjusted p below this


def _prev(target: str) -> str:
    y = int(target[:4]) - 1
    return f"{y}-{str(y + 1)[2:]}"


def context_flags(seasons: pl.DataFrame, context: pl.DataFrame, target: str) -> pl.DataFrame:
    """moved, new_coach, pace_change and usage_freed for every player in `target`.

    `seasons`: season, nba_player_id, first_nba_team_id, last_nba_team_id, fga.
    `context`: season, nba_team_id, new_coach, pace (int_team_season_context).
    moved, pace_change and usage_freed use only last season's numbers and the opening-day team.
    new_coach is the exception: the source records the end-of-season coach, so a coach fired
    during `target` makes the flag true (not draft-time knowledge; ANL-010 reports a sensitivity
    run without it).
    """
    prev = _prev(target)
    now = seasons.filter(pl.col("season") == target).select(
        "nba_player_id", pl.col("first_nba_team_id").alias("team")
    )
    before = seasons.filter(pl.col("season") == prev).select(
        "nba_player_id",
        pl.col("last_nba_team_id").alias("prev_team"),
        pl.col("fga").alias("prev_fga"),
    )
    pace_prev = context.filter(pl.col("season") == prev).select("nba_team_id", "pace")
    coach = context.filter(pl.col("season") == target).select(
        pl.col("nba_team_id").alias("team"), "new_coach"
    )
    # usage freed: last season's shots at each team by players not on its opening-day roster now
    stayed = before.join(now, on="nba_player_id", how="left").with_columns(
        (pl.col("team") == pl.col("prev_team")).fill_null(False).alias("kept")
    )
    freed = stayed.group_by("prev_team").agg(
        (pl.col("prev_fga").filter(~pl.col("kept")).sum() / pl.col("prev_fga").sum()).alias(
            "usage_freed"
        )
    )
    out = (
        now.join(before.select("nba_player_id", "prev_team"), on="nba_player_id", how="left")
        .join(coach, on="team", how="left")
        .join(pace_prev.rename({"nba_team_id": "team", "pace": "pace_new"}), on="team", how="left")
        .join(
            pace_prev.rename({"nba_team_id": "prev_team", "pace": "pace_old"}),
            on="prev_team",
            how="left",
        )
        .join(freed.rename({"prev_team": "team"}), on="team", how="left")
    )
    return out.select(
        "nba_player_id",
        "team",
        "prev_team",
        (pl.col("prev_team").is_not_null() & (pl.col("team") != pl.col("prev_team"))).alias(
            "moved"
        ),
        pl.col("new_coach").fill_null(False).alias("new_coach"),
        pl.col("new_coach").is_null().alias("coach_unknown"),
        pl.when(pl.col("team") == pl.col("prev_team"))
        .then(0.0)
        .otherwise(pl.col("pace_new") - pl.col("pace_old"))
        .alias("pace_change"),
        pl.col("usage_freed").fill_null(0.0).alias("usage_freed"),
    )


@dataclass(frozen=True)
class Term:
    coef: float
    se: float
    ci: tuple[float, float]
    p: float
    share: float  # drop-one R² loss: the share of variance this term alone accounts for


def ols(y: np.ndarray, columns: dict[str, np.ndarray]) -> dict[str, Term]:
    """OLS with an intercept; per term: coefficient, SE, 95 % CI, two-sided p, drop-one R² share."""
    names = list(columns)
    x = np.column_stack([np.ones(len(y)), *[columns[n] for n in names]])
    n, k = x.shape
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    sse = float(resid @ resid)
    sst = float(((y - y.mean()) ** 2).sum())
    sigma2 = sse / (n - k)
    cov = sigma2 * np.linalg.pinv(x.T @ x)
    tcrit = float(stats.t.ppf(0.975, n - k))
    out: dict[str, Term] = {}
    for j, name in enumerate(names, start=1):
        se = float(np.sqrt(cov[j, j]))
        b = float(beta[j])
        p = float(2 * stats.t.sf(abs(b / se), n - k)) if se > 0 else 1.0
        reduced = np.delete(x, j, axis=1)
        rb, *_ = np.linalg.lstsq(reduced, y, rcond=None)
        rr = y - reduced @ rb
        share = (float(rr @ rr) - sse) / sst if sst > 0 else 0.0
        out[name] = Term(b, se, (b - tcrit * se, b + tcrit * se), p, max(0.0, share))
    return out


def holm(pvals: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvals[i]))
        adj[i] = running
    return adj


@dataclass(frozen=True)
class Decision:
    go: bool
    reasons: list[str] = field(default_factory=list)
    adjusted: dict[str, float] = field(default_factory=dict)


def decide(terms: dict[str, Term]) -> Decision:
    """The pre-registered rule: go if any flag explains ≥ 2 % with a Holm-adjusted p < 0.05."""
    names = list(terms)
    adj = dict(zip(names, holm([terms[n].p for n in names]), strict=True))
    reasons = [n for n in names if terms[n].share >= GO_SHARE and adj[n] < GO_ALPHA]
    return Decision(bool(reasons), reasons, adj)


def group_share(
    values: np.ndarray, groups: np.ndarray, n_perm: int = 200, seed: int = 0
) -> tuple[float, float]:
    """R² of group means on `values`, and the mean R² with shuffled labels (the chance level)."""

    def r2(g: np.ndarray) -> float:
        total = float(((values - values.mean()) ** 2).sum())
        if total <= 0:
            return 0.0
        _, inv = np.unique(g, return_inverse=True)
        means = np.bincount(inv, weights=values) / np.bincount(inv)
        within = float(((values - means[inv]) ** 2).sum())
        return 1 - within / total

    rng = np.random.default_rng(seed)
    null = float(np.mean([r2(rng.permutation(groups)) for _ in range(n_perm)]))
    return r2(groups), null


def mean_diff(values: np.ndarray, flag: np.ndarray, n_boot: int = 2000, seed: int = 0) -> Term:
    """Mean of `values` where the flag is set minus where it isn't, with a bootstrap 95 % CI."""
    a, b = values[flag], values[~flag]
    rng = np.random.default_rng(seed)
    boots = (
        [rng.choice(a, len(a)).mean() - rng.choice(b, len(b)).mean() for _ in range(n_boot)]
        if len(a) and len(b)
        else [0.0]
    )
    d = float(a.mean() - b.mean()) if len(a) and len(b) else 0.0
    lo, hi = np.percentile(boots, [2.5, 97.5])
    se = float(np.std(boots))
    p = float(2 * stats.norm.sf(abs(d / se))) if se > 0 else 1.0
    return Term(d, se, (float(lo), float(hi)), p, 0.0)
