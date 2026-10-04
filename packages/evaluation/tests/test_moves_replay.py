from datetime import date, timedelta

import numpy as np
import polars as pl

from fantasy_evaluation import moves_replay as mr

LEVEL = {"PTS": 15, "REB": 6, "AST": 4, "STL": 1, "BLK": 0.8, "FG3M": 1.5, "TOV": 2}


def test_categories_scores_ties_half_and_reverses_turnovers() -> None:
    a = np.array([10, 5, 5, 1, 1, 1, 2, 5, 10, 3, 4], dtype=float)
    b = np.array([9, 5, 6, 1, 1, 1, 3, 4, 10, 3, 4], dtype=float)
    # pts win, reb tie, ast loss, stl/blk/3pm ties, tov win, fg% win, ft% tie
    assert mr.categories(a, b) == 1 + 0.5 + 0 + 1.5 + 1 + 1 + 0.5


def test_realised_gain_swaps_the_players_actual_stats() -> None:
    z = np.zeros(11)
    star = np.array([50, 20, 20, 5, 5, 5, 0, 20, 30, 10, 10], dtype=float)
    weak = np.array([1, 1, 1, 0, 0, 0, 3, 1, 5, 1, 2], dtype=float)
    opp = np.array([20, 10, 10, 2, 2, 2, 2, 8, 16, 4, 5], dtype=float)
    now = {1: weak, 2: z, 9: star, 5: opp}
    gain = mr.realised((9, 1), [1, 2], [5], [5], now, now)
    assert gain == (mr.categories(star, opp) - mr.categories(weak, opp)) * 1.5
    assert mr.realised(None, [1, 2], [5], [5], now, now) == 0.0


def test_schedule_pairs_every_team_with_one_other() -> None:
    for opp in mr.schedule(16, 5, seed=1):
        assert all(opp[opp[t]] == t and opp[t] != t for t in range(16))


def _logs_priors(players: int = 60) -> tuple[pl.DataFrame, pl.DataFrame]:
    rng = np.random.default_rng(4)
    rows, priors = [], []
    start = date(2025, 12, 1)
    for p in range(players):
        talent = 3.0 if p == players - 1 else rng.uniform(0.3, 1.5)  # the last player is a star
        team = p % 6
        priors.append(
            {"PLAYER_ID": p}
            | {c.lower(): v * talent for c, v in LEVEL.items()}
            | {"fgm": 5.6 * talent, "fga": 12 * talent, "ftm": 3 * talent, "fta": 4 * talent}
        )
        for d in range(0, 84, 2):
            row = {
                "PLAYER_ID": p,
                "TEAM_ID": team,
                "GAME_DATE": (start + timedelta(days=d)).isoformat(),
            }
            row |= {c: int(rng.poisson(v * talent)) for c, v in LEVEL.items()}
            fga, fta = int(rng.poisson(12 * talent)), int(rng.poisson(4 * talent))
            row |= {
                "FGA": fga,
                "FGM": int(rng.binomial(fga, 0.47)),
                "FTA": fta,
                "FTM": int(rng.binomial(fta, 0.78)),
            }
            rows.append(row)
    return pl.DataFrame(rows), pl.DataFrame(priors)


def test_week_inputs_use_only_games_before_monday_for_projections() -> None:
    logs, priors = _logs_priors()
    m = date(2026, 1, 19)
    week = mr.week_inputs(logs, priors, m)
    changed = logs.with_columns(
        pl.when(pl.col("GAME_DATE") >= m.isoformat())
        .then(pl.lit(99))
        .otherwise(pl.col("PTS"))
        .alias("PTS")
    )
    assert mr.week_inputs(changed, priors, m).proj == week.proj
    assert week.actual[0][0] > 0


def test_replay_finds_the_star_free_agent() -> None:
    logs, priors = _logs_priors()
    weeks = {m: mr.week_inputs(logs, priors, m) for m in mr.weeks_of(logs)}
    assert weeks
    squads = [list(range(t * 5, t * 5 + 5)) for t in range(4)]  # players 20.. are free agents
    value = dict.fromkeys(range(60), 1.0) | {59: 5.0}
    res = mr.run(squads, weeks, value, draws=300, n_boot=100)
    b = res.summary.filter(pl.col("method") == "B0.5")
    assert b["mean_gain"][0] > 0
    assert res.rows.height == 4 * (len(weeks) - 1)
