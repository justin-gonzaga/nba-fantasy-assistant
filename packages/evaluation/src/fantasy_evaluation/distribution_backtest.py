"""DEC-002: do negative-binomial weekly totals beat Poisson? (pre-registered in the task file.)

Unit: player-week (Mon-Sun). Both models share the mean: the player's season-to-date per-game
average before the week starts, times the games he played that week. Dispersions are estimated on
the selection weeks only; the holdout weeks score both models (CRPS, randomized PIT), and the
difference is bootstrapped over whole weeks [R-55].
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import polars as pl

from dikit.evaluate import bootstrap as bs
from dikit.evaluate import scoring as sc
from dikit.methods import counts as cnt

COUNTS = {
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "fg3m": "FG3M",
    "tov": "TOV",
}
PCTS = {"fg_pct": ("FGM", "FGA"), "ft_pct": ("FTM", "FTA")}
HOLDOUT_START = date(2026, 1, 19)
MIN_PRIOR_GAMES = 5
MC_DRAWS = 1000
SHIP_MIN_CATEGORIES = 6  # of 9, pre-registered


@dataclass(frozen=True)
class Result:
    table: pl.DataFrame  # one row per category
    dispersion: dict[str, float]
    rows: dict[str, int]  # selection / holdout player-weeks
    ships: bool


def player_weeks(logs: pl.DataFrame, min_prior: int = MIN_PRIOR_GAMES) -> pl.DataFrame:
    """Weekly totals plus the season-to-date per-game means before each week."""
    raw = sorted({*COUNTS.values(), "FGM", "FGA", "FTM", "FTA"})
    g = logs.with_columns(pl.col("GAME_DATE").str.to_date().alias("day")).with_columns(
        (pl.col("day") - pl.duration(days=pl.col("day").dt.weekday() - 1)).alias("week")
    )
    wk = (
        g.group_by("SEASON", "PLAYER_ID", "week")
        .agg(pl.len().alias("n"), *[pl.col(c).sum() for c in raw])
        .sort("SEASON", "PLAYER_ID", "week")
    )
    prior = [
        (pl.col(c).cum_sum() - pl.col(c)).over("SEASON", "PLAYER_ID").alias(f"prior_{c}")
        for c in [*raw, "n"]
    ]
    wk = wk.with_columns(prior)
    return wk.filter(pl.col("prior_n") >= min_prior)


def _mean(df: pl.DataFrame, col: str) -> np.ndarray:
    return (df[f"prior_{col}"] / df["prior_n"] * df["n"]).to_numpy()


def _parts(
    df: pl.DataFrame, m_col: str, a_col: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Expected attempts, prior make rate, and the week's makes and attempts."""
    att_mu = (df[f"prior_{a_col}"] / df["prior_n"] * df["n"]).to_numpy()
    p = (df[f"prior_{m_col}"] / df[f"prior_{a_col}"]).fill_nan(0.0).to_numpy()
    return att_mu, np.clip(p, 0.01, 0.99), df[m_col].to_numpy(), df[a_col].to_numpy()


def run(logs: pl.DataFrame, *, n_boot: int = 2000, seed: int = 0) -> Result:
    rng = np.random.default_rng(seed)
    pw = player_weeks(logs)
    sel = pw.filter(pl.col("week") < HOLDOUT_START)
    hold = pw.filter(pl.col("week") >= HOLDOUT_START)
    disp: dict[str, float] = {}
    rows = []
    weeks = np.array([w.toordinal() for w in hold["week"].to_list()])
    for cat, col in COUNTS.items():
        r = cnt.nb_size(sel[col].to_numpy(), _mean(sel, col), sel["n"].to_numpy())
        disp[cat] = r
        y, mu, n = hold[col].to_numpy(), _mean(hold, col), hold["n"].to_numpy()
        kmax = int(max(y.max(), mu.max() * 4)) + 50
        base_cdf = cnt.count_cdf(mu, size=np.inf, kmax=kmax)
        nb_cdf = cnt.count_cdf(mu, size=np.where(np.isfinite(r), r * n, np.inf), kmax=kmax)
        cb, cn = sc.crps_counts(base_cdf, y), sc.crps_counts(nb_cdf, y)
        pb, pn = sc.pit_counts(base_cdf, y, rng), sc.pit_counts(nb_cdf, y, rng)
        rows.append(_row(cat, cb=cb, cn=cn, pb=pb, pn=pn, weeks=weeks, n_boot=n_boot, rng=rng))
    for cat, (m_col, a_col) in PCTS.items():
        s_mu, s_p, s_m, s_a = _parts(sel, m_col, a_col)
        r_att = cnt.nb_size(s_a, s_mu, sel["n"].to_numpy())
        rho = cnt.betabin_rho(s_m, s_a, s_p)
        disp[f"{cat}_attempts"], disp[f"{cat}_rho"] = r_att, rho
        att_mu, p, m, a = _parts(hold, m_col, a_col)
        keep = a > 0
        y = m[keep] / a[keep]
        n = hold["n"].to_numpy()[keep]
        att_mu, p = att_mu[keep], p[keep]
        base = _pct_samples(att_mu, np.inf, p, 0.0, rng)
        size = np.where(np.isfinite(r_att), r_att * n, np.inf)
        cand = _pct_samples(att_mu, size, p, rho, rng)
        cb, cn = sc.crps_samples(base, y), sc.crps_samples(cand, y)
        pb, pn = _pit_samples(base, y, rng), _pit_samples(cand, y, rng)
        rows.append(
            _row(cat, cb=cb, cn=cn, pb=pb, pn=pn, weeks=weeks[keep], n_boot=n_boot, rng=rng)
        )
    table = pl.DataFrame(rows)
    wins = table.filter(pl.col("ci_hi") < 0).height
    pit_ok = float(table["pit_nb"].mean()) <= float(table["pit_poisson"].mean())  # type: ignore[arg-type]
    return Result(
        table,
        disp,
        {"selection": sel.height, "holdout": hold.height},
        wins >= SHIP_MIN_CATEGORIES and pit_ok,
    )


def _pct_samples(
    att_mu: np.ndarray,
    size: float | np.ndarray,
    p: np.ndarray,
    rho: float,
    rng: np.random.Generator,
) -> np.ndarray:
    att = cnt.sample_counts(att_mu, size, MC_DRAWS, rng)
    makes = cnt.sample_makes(att, np.broadcast_to(p[:, None], att.shape), rho, rng)
    with np.errstate(divide="ignore", invalid="ignore"):
        pct = np.where(att > 0, makes / np.maximum(att, 1), p[:, None])
    return pct.astype(float)


def _pit_samples(samples: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    below = (samples < y[:, None]).mean(axis=1)
    equal = (samples == y[:, None]).mean(axis=1)
    out: np.ndarray = below + rng.uniform(size=len(y)) * equal
    return out


def _row(  # noqa: PLR0913 - one table row from the paired scores
    cat: str,
    *,
    cb: np.ndarray,
    cn: np.ndarray,
    pb: np.ndarray,
    pn: np.ndarray,
    weeks: np.ndarray,
    n_boot: int,
    rng: np.random.Generator,
) -> dict[str, object]:
    lo, hi = bs.clustered_mean_ci(cn - cb, weeks, n_boot, rng)
    return {
        "category": cat,
        "n": len(cb),
        "crps_poisson": float(cb.mean()),
        "crps_nb": float(cn.mean()),
        "diff": float((cn - cb).mean()),
        "ci_lo": lo,
        "ci_hi": hi,
        "pit_poisson": sc.pit_deviation(pb),
        "pit_nb": sc.pit_deviation(pn),
    }
