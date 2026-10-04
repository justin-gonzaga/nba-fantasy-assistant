"""ANL-005: does updating the pre-season projection with the season so far predict weeks better?
(Pre-registered in the task file.)

Player-weeks with a pre-season prior and >= 1 earlier game. Three predictions of each week's
totals, given the games played: the frozen prior (live), season-to-date only, and the blend with
k chosen per stat on selection weeks. Holdout weeks score all three; week-block bootstrap CIs.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from dikit.methods import shrinkage
from fantasy_evaluation.distribution_backtest import HOLDOUT_START, player_weeks

COUNTS = {
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "fg3m": "FG3M",
    "tov": "TOV",
}
PCTS = {"fg_pct": ("fgm", "FGM", "fga", "FGA"), "ft_pct": ("ftm", "FTM", "fta", "FTA")}
SHIP_MIN_CATEGORIES = 6
MAX_WORSE = 0.02


@dataclass(frozen=True)
class Result:
    table: pl.DataFrame  # per category: mae_prior, mae_std, mae_blend, diff (blend - prior), CI, k
    rows: dict[str, int]
    ships: bool


def run(logs: pl.DataFrame, priors: pl.DataFrame, *, n_boot: int = 2000, seed: int = 0) -> Result:
    """`priors`: SEASON, PLAYER_ID and per-game pre-season projections (pts ... fta)."""
    rng = np.random.default_rng(seed)
    pw = player_weeks(logs, min_prior=1).join(priors, on=["SEASON", "PLAYER_ID"], how="inner")
    sel = pw.filter(pl.col("week") < HOLDOUT_START)
    hold = pw.filter(pl.col("week") >= HOLDOUT_START)
    weeks = np.array([w.toordinal() for w in hold["week"].to_list()])
    rows = []
    for cat, raw in COUNTS.items():
        k = shrinkage.choose_k(
            sel[cat].to_numpy(),
            sel[f"prior_{raw}"].to_numpy(),
            sel["prior_n"].to_numpy(),
            sel["n"].to_numpy(),
            sel[raw].to_numpy(),
        )
        n, y = hold["n"].to_numpy(), hold[raw].to_numpy()
        e_prior = np.abs(y - n * hold[cat].to_numpy())
        e_std = np.abs(y - n * hold[f"prior_{raw}"].to_numpy() / hold["prior_n"].to_numpy())
        e_blend = np.abs(
            y
            - n
            * shrinkage.blend(
                hold[cat].to_numpy(), hold[f"prior_{raw}"].to_numpy(), hold["prior_n"].to_numpy(), k
            )
        )
        rows.append(
            _row(
                cat,
                k=k,
                e_prior=e_prior,
                e_std=e_std,
                e_blend=e_blend,
                weeks=weeks,
                n_boot=n_boot,
                rng=rng,
            )
        )
    for cat, (m_pg, m_raw, a_pg, a_raw) in PCTS.items():
        k_m = shrinkage.choose_k(
            sel[m_pg].to_numpy(),
            sel[f"prior_{m_raw}"].to_numpy(),
            sel["prior_n"].to_numpy(),
            sel["n"].to_numpy(),
            sel[m_raw].to_numpy(),
        )
        k_a = shrinkage.choose_k(
            sel[a_pg].to_numpy(),
            sel[f"prior_{a_raw}"].to_numpy(),
            sel["prior_n"].to_numpy(),
            sel["n"].to_numpy(),
            sel[a_raw].to_numpy(),
        )
        keep = hold[a_raw].to_numpy() > 0
        h = hold.filter(pl.Series(keep))
        y = (h[m_raw] / h[a_raw]).to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            p_prior = np.nan_to_num(h[m_pg].to_numpy() / h[a_pg].to_numpy())
            p_std = np.nan_to_num(h[f"prior_{m_raw}"].to_numpy() / h[f"prior_{a_raw}"].to_numpy())
            bm = shrinkage.blend(
                h[m_pg].to_numpy(), h[f"prior_{m_raw}"].to_numpy(), h["prior_n"].to_numpy(), k_m
            )
            ba = shrinkage.blend(
                h[a_pg].to_numpy(), h[f"prior_{a_raw}"].to_numpy(), h["prior_n"].to_numpy(), k_a
            )
            p_blend = np.nan_to_num(bm / ba)
        rows.append(
            _row(
                cat,
                k=(k_m, k_a),
                e_prior=np.abs(y - p_prior),
                e_std=np.abs(y - p_std),
                e_blend=np.abs(y - p_blend),
                weeks=weeks[keep],
                n_boot=n_boot,
                rng=rng,
            )
        )
    table = pl.DataFrame(rows)
    wins = table.filter(pl.col("ci_hi") < 0).height
    worse = table.filter(pl.col("mae_blend") > pl.col("mae_prior") * (1 + MAX_WORSE)).height
    return Result(
        table,
        {"selection": sel.height, "holdout": hold.height},
        wins >= SHIP_MIN_CATEGORIES and worse == 0,
    )


def _row(  # noqa: PLR0913 - one table row from the paired errors
    cat: str,
    *,
    k: float | tuple[float, float],
    e_prior: np.ndarray,
    e_std: np.ndarray,
    e_blend: np.ndarray,
    weeks: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    lo, hi = bs.clustered_mean_ci(e_blend - e_prior, weeks, n_boot, rng)
    return {
        "category": cat,
        "k": str(k),
        "n": len(e_prior),
        "mae_prior": float(e_prior.mean()),
        "mae_std": float(e_std.mean()),
        "mae_blend": float(e_blend.mean()),
        "diff": float((e_blend - e_prior).mean()),
        "ci_lo": lo,
        "ci_hi": hi,
    }
