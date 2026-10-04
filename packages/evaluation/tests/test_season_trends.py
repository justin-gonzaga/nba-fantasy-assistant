from datetime import date, timedelta

import numpy as np
import polars as pl
import pytest

from fantasy_evaluation import season_trends as st


def _logs(
    season: str,
    players: dict[int, tuple[float, float]],
    *,
    year: int = 2025,
    gap: tuple[int, int] = (14, 20),
) -> pl.DataFrame:
    """Games every other day from 20 Oct to 10 Apr, skipping a mid-February gap (the ASB).
    `players`: id -> (points per game before the break, after)."""
    start, end = date(year - 1, 10, 20), date(year, 4, 10)
    asb0, asb1 = date(year, 2, gap[0]), date(year, 2, gap[1])
    rows = []
    d, g = start, 0
    while d <= end:
        if not (asb0 <= d < asb1):
            g += 1
            for pid, (before, after) in players.items():
                pts = before if d < asb1 else after
                rows.append(
                    {
                        "SEASON": season,
                        "PLAYER_ID": pid,
                        "TEAM_ID": 100 + pid % 2,
                        "GAME_ID": f"{season}-{g}-{pid % 2}",
                        "GAME_DATE": d.isoformat(),
                        "WL": "W" if pid % 2 else "L",
                        "MIN": 30.0,
                        "PTS": pts,
                        "REB": 5.0,
                        "AST": 3.0,
                        "STL": 1.0,
                        "BLK": 0.5,
                        "FG3M": 1.0,
                        "TOV": 2.0,
                        "FGM": 7.0,
                        "FGA": 15.0,
                        "FTM": 3.0,
                        "FTA": 4.0,
                    }
                )
        d += timedelta(days=2)
    return pl.DataFrame(rows)


def test_the_all_star_break_is_the_longest_february_gap() -> None:
    logs = st.tidy(_logs("2024-25", {1: (20, 20)}))
    asb = st.all_star_break(logs)
    assert date(2025, 2, 13) <= asb <= date(2025, 2, 20)


def test_half_values_capture_a_second_half_jump() -> None:
    logs = st.tidy(_logs("2024-25", {1: (10, 30), 2: (20, 20), 3: (25, 15), 4: (18, 18)}))
    v = st.half_values(logs).sort("player")
    deltas = dict(zip(v["player"].to_list(), v["delta"].to_list(), strict=True))
    assert deltas[1] > deltas[2] > deltas[3]


def test_persistence_detects_a_repeatable_trait_and_no_trait() -> None:
    rng = np.random.default_rng(1)
    ids = list(range(1, 60))
    trait = {p: float(rng.normal()) for p in ids}

    def season(s: str, year: int, noise: float) -> pl.DataFrame:
        return st.tidy(
            _logs(
                s,
                {p: (20.0, 20.0 + 4 * trait[p] + noise * float(rng.normal())) for p in ids},
                year=year,
            )
        )

    real = {s: st.half_values(season(s, y, 0.5)) for s, y in (("2023-24", 2024), ("2024-25", 2025))}
    res = st.persistence(st.pair_up(real), n_boot=300)
    assert res.r > 0.5
    assert res.ci[0] > 0

    trait = dict.fromkeys(ids, 0.0)  # no trait: changes are pure noise
    noise = {s: st.half_values(season(s, y, 4)) for s, y in (("2023-24", 2024), ("2024-25", 2025))}
    assert abs(st.persistence(st.pair_up(noise), n_boot=300).r) < 0.4


def test_team_context_groups_by_win_pct() -> None:
    rows = []
    for t in range(30):
        for g in range(20):
            rows.append(
                {
                    "team": t,
                    "game": f"{t}-{g}",
                    "day": date(2025, 1, 1),
                    "wl": "W" if g < 20 - t * 0.6 else "L",
                }
            )
    ctx = st.team_context(pl.DataFrame(rows), date(2025, 3, 1))
    by = dict(zip(ctx["team"].to_list(), ctx["context"].to_list(), strict=True))
    assert by[0] == "contender"
    assert by[29] == "bottom-6"
    assert by[15] == "mid-race"


def test_material_rule() -> None:
    assert st.material(
        {"games_missed_extra": 2.5, "games_missed_extra_lo": 1.0, "games_missed_extra_hi": 4.0}
    )
    assert not st.material(
        {"games_missed_extra": 2.5, "games_missed_extra_lo": -1.0, "games_missed_extra_hi": 4.0}
    )
    assert st.material({"mpg_change": -3.5, "mpg_change_lo": -5.0, "mpg_change_hi": -2.0})
    assert not st.material({"mpg_change": -1.0, "mpg_change_lo": -2.0, "mpg_change_hi": -0.5})


def test_playoff_weight_one_reproduces_the_current_ranks() -> None:
    values = pl.DataFrame({"player": [1, 2, 3], "team": [10, 11, 12], "value": [3.0, 2.9, 1.0]})
    same = st.playoff_weighted_ranks(values, {10: 9, 11: 12, 12: 10}, 82, 1.0)
    assert same["rank"].to_list() == same["rank_w"].to_list()
    heavy = st.playoff_weighted_ranks(values, {10: 6, 11: 12, 12: 10}, 82, 3.0)
    assert heavy.filter(pl.col("player") == 2)["rank_w"][0] == 1  # more playoff games overtakes


@pytest.mark.parametrize("cutoff", [date(2025, 3, 1)])
def test_late_season_measures_missed_games(cutoff: date) -> None:
    logs = st.tidy(_logs("2024-25", {1: (20, 20), 2: (20, 20), 3: (20, 20)}))  # 1 and 3: teammates
    # player 1 stops playing after the cutoff (rest), player 2 keeps playing
    logs = logs.filter(~((pl.col("player") == 1) & (pl.col("day") >= cutoff)))
    roles = pl.DataFrame({"player": [1, 2, 3], "role": ["star", "star", "star"]})
    rows = st.late_season(logs, cutoff, roles)
    missed = dict(zip(rows["player"].to_list(), rows["games_missed_extra"].to_list(), strict=True))
    assert missed[1] > 10
    assert abs(missed[2]) < 1


def test_pairs_skip_non_consecutive_seasons() -> None:
    d = pl.DataFrame({"player": [1], "delta": [1.0], "delta_per36": [1.0]})
    pairs = st.pair_up({"2018-19": d, "2021-22": d, "2022-23": d})
    assert pairs.height == 1  # only 2021-22 -> 2022-23; the COVID gap breaks the chain


def test_rank_changes_are_signed() -> None:
    values = pl.DataFrame({"player": [1, 2], "team": [10, 11], "value": [3.0, 2.9]})
    r = st.playoff_weighted_ranks(values, {10: 6, 11: 12}, 82, 3.0)
    change = r.select((pl.col("rank") - pl.col("rank_w")).alias("gain"))["gain"].to_list()
    assert sorted(change) == [-1, 1]  # one rises, one falls; no wrap-around
