"""ANL-010: team and coach effects study (report + the pre-registered go/no-go for EXP-004).

Residuals come from the shipped pre-season method (H1+aging+M1pre), built leak-free per target
season exactly as the DRAFT-009 replay does; context flags come from
`fantasy_evaluation.team_effects`, using only what was known at each draft.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import polars as pl

from fantasy_evaluation import preseason_backtest as bt
from fantasy_evaluation import team_effects as te
from fantasy_models.preseason.project import project_pool
from fantasy_models.preseason.schema import season_of, start_year
from fantasy_pipeline.draft_projection import _inputs
from fantasy_pipeline.draft_replay_run import _ours_method
from fantasy_pipeline.warehouse import Warehouse

CONTEXT_SQL = "select * from intermediate.int_team_season_context"
TARGETS = ("2023-24", "2024-25", "2025-26")  # pre-registered (ANL-010 AC2)
Q1_FIRST = "2016-17"
Q1_MIN_MINUTES = 500
Q1_STATS = ("pts", "reb", "ast", "fg3m")
FLAGS = ("moved", "new_coach", "pace_change", "usage_freed")


def residuals(
    seasons: pl.DataFrame, draft: pl.DataFrame, wh: Warehouse, target: str
) -> pl.DataFrame:
    """Actual minus projected, per game and in fantasy value, for players with ≥ 20 games."""
    last = season_of(start_year(target) - 1)
    pool = (
        pl.concat(
            [
                seasons.filter(pl.col("season") == last).select(
                    pl.col("nba_player_id").cast(pl.Int64)
                ),
                draft.filter(pl.col("draft_year") == start_year(target)).select("nba_player_id"),
            ]
        )
        .unique()
        .with_columns(pl.lit(None, pl.Int64).alias("overall_pick"))
    )
    proj = project_pool(seasons, draft, pool, target, _ours_method(wh, seasons, target))
    actual = bt.actual_per_game(seasons, target)
    both = actual.join(proj, on="nba_player_id", how="inner", suffix="_proj").sort("nba_player_id")
    cols = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta")
    act = both.select("nba_player_id", *cols)
    pred = both.select("nba_player_id", *[pl.col(f"{c}_proj").alias(c) for c in cols])
    value_res = bt.value_score(act, act) - bt.value_score(pred, act)
    return both.select(
        "nba_player_id",
        pl.lit(target).alias("season"),
        *[
            (pl.col(c) - pl.col(f"{c}_proj")).alias(f"res_{c}")
            for c in ("pts", "reb", "ast", "fg3m")
        ],
        (pl.col("mpg") - pl.col("mpg_proj")).alias("res_mpg"),
    ).with_columns(pl.Series("res_value", value_res))


def q1_team_shares(seasons: pl.DataFrame, n_perm: int = 200) -> dict[str, tuple[float, float, int]]:
    """Share of the season-to-season per-36 change explained by the new team-season, vs chance."""
    s = seasons.filter(pl.col("minutes") >= Q1_MIN_MINUTES).select(
        "season",
        "nba_player_id",
        "first_nba_team_id",
        "minutes",
        "games_played",
        *[(pl.col(c) * 36 / pl.col("minutes")).alias(c) for c in Q1_STATS],
        (pl.col("minutes") / pl.col("games_played")).alias("mpg"),
    )
    prev = s.with_columns(
        pl.col("season").map_elements(
            lambda x: season_of(start_year(x) + 1), return_dtype=pl.String
        )
    )
    pairs = s.filter(pl.col("season") >= Q1_FIRST).join(
        prev, on=["season", "nba_player_id"], suffix="_prev"
    )
    groups = (pairs["season"] + ":" + pairs["first_nba_team_id"].cast(pl.String)).to_numpy()
    out = {}
    for c in (*Q1_STATS, "mpg"):
        change = (pairs[c] - pairs[f"{c}_prev"]).to_numpy()
        share, null = te.group_share(change, groups, n_perm=n_perm, seed=0)
        out[c] = (share, null, len(change))
    return out


def run(wh: Warehouse, generated: datetime, n_perm: int = 200) -> tuple[str, te.Decision]:
    seasons, draft = _inputs(wh)
    context = wh.read(CONTEXT_SQL)
    frames = []
    for target in TARGETS:
        flags = te.context_flags(seasons, context, target)
        frames.append(
            residuals(seasons, draft, wh, target).join(flags, on="nba_player_id", how="inner")
        )
    data = pl.concat(frames)
    cols = {
        "moved": data["moved"].cast(pl.Float64).to_numpy(),
        "new_coach": data["new_coach"].cast(pl.Float64).to_numpy(),
        "pace_change": data["pace_change"].fill_null(0.0).to_numpy(),
        "usage_freed": data["usage_freed"].to_numpy(),
    }
    q5 = te.ols(data["res_value"].to_numpy(), cols)
    decision = te.decide(q5)
    # Sensitivity (added after review): `new_coach` uses the end-of-season coach of t, so a
    # mid-season firing during t leaks in. Without it the three other flags are draft-time only.
    no_coach = te.ols(
        data["res_value"].to_numpy(), {k: v for k, v in cols.items() if k != "new_coach"}
    )
    sensitivity = te.decide(no_coach)
    stayers = data.filter(~pl.col("moved") & ~pl.col("coach_unknown"))
    q2 = te.mean_diff(data["res_value"].to_numpy(), data["moved"].to_numpy())
    q3 = te.mean_diff(stayers["res_value"].to_numpy(), stayers["new_coach"].to_numpy())
    movers = data.filter(pl.col("moved") & pl.col("pace_change").is_not_null())
    q4 = te.ols(movers["res_pts"].to_numpy(), {"pace_change": movers["pace_change"].to_numpy()})
    q1 = q1_team_shares(seasons, n_perm=n_perm)
    md = render(
        data=data,
        q1=q1,
        q2=q2,
        q3=q3,
        q4=q4,
        q5=q5,
        decision=decision,
        no_coach=no_coach,
        sensitivity=sensitivity,
        generated=generated,
    )
    return md, decision


def _ci(t: te.Term, digits: int = 3) -> str:
    return f"{t.coef:+.{digits}f} [{t.ci[0]:+.{digits}f}, {t.ci[1]:+.{digits}f}]"


def render(  # noqa: PLR0913 - the report's parts
    *,
    data: pl.DataFrame,
    q1: dict[str, tuple[float, float, int]],
    q2: te.Term,
    q3: te.Term,
    q4: dict[str, te.Term],
    q5: dict[str, te.Term],
    decision: te.Decision,
    no_coach: dict[str, te.Term],
    sensitivity: te.Decision,
    generated: datetime,
) -> str:
    n = data.height

    def mean(s: pl.Series) -> float:
        return float(np.nanmean(s.cast(pl.Float64).to_numpy())) if s.len() else 0.0

    moved, coach = mean(data["moved"]), mean(data["new_coach"])
    pace = mean(data.filter(pl.col("moved"))["pace_change"].abs())
    freed = mean(data["usage_freed"])
    lines = [
        "# ANL-010 — Team and coach effects",
        "",
        f"Generated {generated:%Y-%m-%d %H:%M UTC}. Residuals: the shipped pre-season method",
        f"(H1+aging+M1pre), leak-free, targets {', '.join(TARGETS)}; {n} player-seasons with",
        "≥ 20 games. Value = the 9-cat z-sum of per-game stats",
        "(`preseason_backtest.value_score`), actual minus projected.",
        "",
        f"Flags (share of player-seasons): moved {moved:.1%}, new coach {coach:.1%}, mean",
        f"|pace change| among movers {pace:.2f}, mean usage freed {freed:.1%}.",
        "",
        "## Decision",
        "",
        "Pre-registered: a flag explains ≥ 2 % of the value-residual variance, Holm p < 0.05.",
        "",
        f"**{'GO' if decision.go else 'NO-GO'}**"
        + (
            f": {', '.join(decision.reasons)}."
            if decision.go
            else ": no context flag meets the rule."
        ),
        "",
        "## Q5 — Do the model's errors line up with context changes? (OLS on the value residual)",
        "",
        "| Flag | Effect on value residual [95 % CI] | Share of variance | p | Holm p |",
        "|---|---|---|---|---|",
    ]
    for name in FLAGS:
        t = q5[name]
        lines.append(
            f"| {name} | {_ci(t)} | {t.share:.2%} | {t.p:.3g} | {decision.adjusted[name]:.3g} |"
        )
    lines += [
        "",
        "",
        "### Sensitivity: without `new_coach` (added after review, not pre-registered)",
        "",
        "`new_coach` compares end-of-season coaches, so a coach fired during t counts as new",
        "for t: information from after the draft. Those firings follow bad seasons, so the leak",
        "can only make the flag look more predictive. Refitting with the three draft-time flags",
        "only:",
        "",
        "| Flag | Effect [95 % CI] | Share of variance | p | Holm p |",
        "|---|---|---|---|---|",
        *[
            f"| {k} | {_ci(t)} | {t.share:.2%} | {t.p:.3g} | {sensitivity.adjusted[k]:.3g} |"
            for k, t in no_coach.items()
        ],
        "",
        f"Decision without `new_coach`: **{'GO' if sensitivity.go else 'NO-GO'}**.",
        "",
        "## Q1 — How much of the season-to-season per-36 change does the new team explain?",
        "",
        "R² of team-season means on the change, against shuffled team labels (chance).",
        "",
        "| Stat | R² | Chance | Excess | Player pairs |",
        "|---|---|---|---|---|",
    ]
    for c, (share, null, k) in q1.items():
        lines.append(f"| {c} | {share:.3f} | {null:.3f} | {share - null:+.3f} | {k} |")
    lines += [
        "",
        "## Q2 — Movers vs stayers (value residual, mean difference [95 % bootstrap CI])",
        "",
        f"{_ci(q2)}, p = {q2.p:.3g}.",
        "",
        "## Q3 — New head coach, players who stayed (value residual, mean difference)",
        "",
        f"{_ci(q3)}, p = {q3.p:.3g}.",
        "",
        "## Q4 — Pace change for movers (points-per-game residual per unit of pace change)",
        "",
        f"{_ci(q4['pace_change'])} PTS per game per possession of pace,",
        f"p = {q4['pace_change'].p:.3g}.",
        "",
        "## Caveats",
        "",
        "- One head coach per team-season, the end-of-season one (DATA-038). A coach fired during",
        "  season t therefore counts as a new coach for t, which was not known at the draft",
        "  (see the sensitivity run); a summer change followed by a mid-season one is still",
        "  flagged correctly. The 10 team-seasons whose coach was fired after the season have no",
        "  coach and count as no change.",
        "- Usage freed attributes a traded player's shots to his last team; contract-year",
        "  effort (R-116-R-118) is not controlled.",
        "- Three target seasons; small effects can hide in the noise. The rule above was fixed",
        "  before running.",
    ]
    return "\n".join(lines) + "\n"
