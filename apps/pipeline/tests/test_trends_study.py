from datetime import UTC, datetime

import polars as pl

from fantasy_evaluation import season_trends as st
from fantasy_pipeline import trends_study as ts

NOW = datetime(2026, 10, 3, tzinfo=UTC)


def _effects(missed: float) -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "context": "bottom-6",
                "role": "star",
                "n": 60,
                "games_missed_extra": missed,
                "games_missed_extra_lo": missed - 1,
                "games_missed_extra_hi": missed + 1,
                "mpg_change": None,
                "mpg_change_lo": None,
                "mpg_change_hi": None,
            }
        ]
    )


def test_report_applies_each_preregistered_rule() -> None:
    noise = st.Persistence(800, 0.08, (0.01, 0.15), 0.02, (-0.05, 0.1))
    text = ts.report(noise, _effects(6.2), None, {}, NOW)
    assert "**noise: don't model individual second-half tendencies.**" in text  # r < 0.15
    assert "| bottom-6 | star | 60 | +6.20 (+5.20 to +7.20) | — | yes |" in text
    assert "Q3 not computed (no guessed games)" in text

    trait = st.Persistence(800, 0.4, (0.3, 0.5), 0.3, (0.2, 0.4))
    assert "**a repeatable trait" in ts.report(trait, _effects(0.5), None, {}, NOW)


def test_q3_decision_uses_signed_rank_changes() -> None:
    base = pl.DataFrame(
        {
            "player": [1, 2, 3],
            "team": [0, 1, 2],
            "value": [3.0, 2.0, 1.0],
            "player_name": ["A", "B", "C"],
        }
    )
    tab = pl.concat(
        [
            st.playoff_weighted_ranks(base, {0: 9, 1: 12, 2: 10}, 82, w).with_columns(
                pl.lit(w).alias("w")
            )
            for w in ts.WEIGHTS
        ]
    )
    text = ts.report(
        st.Persistence(1, 0.0, (-0.1, 0.1), 0.0, (-0.1, 0.1)),
        _effects(0),
        tab,
        {"A": 9, "B": 12},
        NOW,
    )
    assert "**0 move: not material; no model change.**" in text
    assert "4294967295" not in text


def test_roles_follow_the_preregistered_precedence() -> None:
    def games(player: int, n: int, minutes: float, pts: float) -> list[dict[str, object]]:
        return [
            {
                "player": player,
                "min": minutes,
                "pts": pts,
                **{c: 1.0 for c in st.STATS if c != "pts"},
            }
            for _ in range(n)
        ]

    pre = pl.DataFrame(
        games(1, 30, 36, 30)  # the best: a star even though young
        + games(2, 30, 15, 8)  # young bench player
        + games(3, 30, 25, 10)  # veteran rotation
        + games(4, 30, 10, 4)  # veteran bench: no role
    )
    age = pl.DataFrame({"player": [1, 2, 3, 4], "age": [21.0, 22.0, 29.0, 31.0]})
    roles = dict(ts.assign_roles(pre, age, stars=1).iter_rows())
    assert roles == {1: "star", 2: "young", 3: "rotation"}
