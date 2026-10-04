import polars as pl
import pytest

from dikit.errors import LeakageError
from fantasy_models.preseason import methods as m
from fantasy_models.preseason import returners as r
from fantasy_models.preseason.schema import history_before, season_of
from fantasy_models.preseason.synthetic import make_league

TEAM_GAMES = 80


def rows(*specs: tuple[int, str, int, float]) -> pl.DataFrame:
    """History rows from (player, season, games played, minutes per game)."""
    return pl.DataFrame(
        {
            "nba_player_id": [s[0] for s in specs],
            "season": [s[1] for s in specs],
            "games_played": [s[2] for s in specs],
            "season_team_games": [TEAM_GAMES] * len(specs),
            "minutes": [s[2] * s[3] for s in specs],
        },
        schema_overrides={"minutes": pl.Float64},
    )


def ids(df: pl.DataFrame) -> list[int]:
    return sorted(df.get_column("nba_player_id").to_list())


# ---------------------------------------------------------------- cohort (AC1)
def test_cohort_is_a_rotation_season_then_an_essentially_absent_one() -> None:
    h = rows(
        (1, "2023-24", 70, 33.0),  # healthy, then no row at all (Lillard-like)
        (2, "2023-24", 70, 30.0),  # 16 of 80 games last season
        (2, "2024-25", 16, 30.0),
        (3, "2023-24", 70, 30.0),  # 48 of 80: not essentially absent
        (3, "2024-25", 48, 30.0),
        (4, "2024-25", 10, 25.0),  # rookie-like: nothing two seasons back
        (5, "2022-23", 70, 30.0),  # two lost seasons in a row
        (6, "2023-24", 70, 30.0),  # healthy last season too
        (6, "2024-25", 70, 30.0),
    )
    got = r.cohort(h, "2025-26")
    assert ids(got) == [1, 2]
    assert got.filter(pl.col("nba_player_id") == 1)["gp_frac_1"].item() == 0.0


@pytest.mark.parametrize(
    ("last_gp", "before_gp", "before_mpg", "inside"),
    [
        (20, 48, 22.0, False),  # 20/80 = 0.25 exactly: not below
        (19, 48, 22.0, True),  # just below 0.25; 48/80 = 0.6 and 22 mpg exactly: both inclusive
        (19, 47, 22.0, False),  # just below 0.6
        (19, 48, 21.9, False),  # just below 22 mpg
    ],
)
def test_cohort_boundaries(last_gp: int, before_gp: int, before_mpg: float, inside: bool) -> None:
    h = rows((1, "2023-24", before_gp, before_mpg), (1, "2024-25", last_gp, 20.0))
    assert (ids(r.cohort(h, "2025-26")) == [1]) is inside


def test_cohort_refuses_future_seasons() -> None:
    with pytest.raises(LeakageError, match="2025-26"):
        r.cohort(rows((1, "2025-26", 70, 30.0)), "2025-26")


# ---------------------------------------------------------------- base rate (AC2)
def returners_history(
    n_per_year: int, years: range, back_gp: dict[int, int] | int = 40
) -> pl.DataFrame:
    """Per year y: `n_per_year` new cohort players (healthy in y-2, no row in y-1) who come
    back in y for `back_gp` games at 20 mpg (so they are not cohort again two years later)."""
    specs: list[tuple[int, str, int, float]] = []
    pid = 0
    for y in years:
        gp = back_gp if isinstance(back_gp, int) else back_gp[y]
        for _ in range(n_per_year):
            pid += 1
            specs.append((pid, season_of(y - 2), 70, 30.0))
            specs.append((pid, season_of(y), gp, 20.0))
    return rows(*specs)


def test_base_rate_is_the_mean_realised_fraction_of_returners_in_earlier_seasons() -> None:
    h = returners_history(10, range(2016, 2022))  # 60 rows, all 40 / 80 = 0.5
    got = r.base_rate(history_before(h, "2022-23"), "2022-23")
    assert got is not None
    assert got.n == 60
    assert got.rate == pytest.approx(0.5)


def test_base_rate_needs_thirty_rows() -> None:
    enough = returners_history(5, range(2016, 2022))  # 30 rows
    assert r.base_rate(enough, "2023-24") is not None
    assert r.base_rate(enough.filter(pl.col("nba_player_id") != 1), "2023-24") is None


def test_base_rate_ignores_the_target_and_later_seasons() -> None:
    gp_by_year = {**dict.fromkeys(range(2016, 2019), 40), **dict.fromkeys(range(2019, 2022), 60)}
    low = returners_history(10, range(2016, 2022), back_gp=40)
    high = returners_history(10, range(2016, 2022), back_gp=gp_by_year)
    a = r.base_rate(history_before(low, "2019-20"), "2019-20")
    b = r.base_rate(history_before(high, "2019-20"), "2019-20")
    assert a is not None
    assert b is not None
    assert a.rate == pytest.approx(b.rate) == pytest.approx(0.5)  # 2019+ cannot move it
    later = r.base_rate(history_before(high, "2022-23"), "2022-23")
    assert later is not None
    assert later.rate == pytest.approx(0.625)  # 30 rows at 0.5, 30 at 0.75
    with pytest.raises(LeakageError):
        r.base_rate(high, "2019-20")  # a frame that still holds 2019-20 and later is refused


def test_base_rate_counts_only_players_who_played_that_season() -> None:
    h = returners_history(10, range(2016, 2022))
    never_back = rows(*[(900 + i, "2018-19", 70, 30.0) for i in range(5)])  # cohort in 2020-21
    zero_games = rows((990, "2019-20", 70, 30.0), (990, "2021-22", 0, 20.0))
    got = r.base_rate(pl.concat([h, never_back, zero_games]), "2022-23")
    assert got is not None
    assert got.n == 60  # five who never returned and one with 0 games are not rows


def test_realised_rows_pair_cohort_with_what_they_played() -> None:
    h = returners_history(2, range(2016, 2019), back_gp=60)
    got = r.realised(h, "2018-19")
    assert ids(got) == [5, 6]
    assert got["games_frac"].to_list() == [0.75, 0.75]


# ---------------------------------------------------------------- engine (AC3)
SEASONS, _ = make_league()
TARGET = "2025-26"


def lost_season_history() -> pl.DataFrame:
    hist = history_before(SEASONS, TARGET)
    two_back = hist.filter(pl.col("season") == season_of(2023)).with_columns(
        (pl.col("minutes") / pl.col("games_played")).alias("mpg")
    )
    eligible = two_back.filter(
        (pl.col("games_played") / pl.col("season_team_games") >= r.ROTATION_AT_LEAST)
        & (pl.col("mpg") >= r.ROTATION_MPG)
    )
    assert eligible.height > 0
    gone = eligible.get_column("nba_player_id").to_list()[0]
    return hist.filter(~((pl.col("nba_player_id") == gone) & (pl.col("season") == season_of(2024))))


@pytest.mark.parametrize(("rate", "raised"), [(0.8, True), (0.05, False)])
def test_hybrid_returners_only_raises_cohort_games(
    monkeypatch: pytest.MonkeyPatch, rate: float, raised: bool
) -> None:
    monkeypatch.setattr(r, "base_rate", lambda *_a, **_k: r.BaseRate(rate=rate, n=99))
    h = lost_season_history()
    in_cohort = ids(r.cohort(h, TARGET))
    assert in_cohort
    base = m.hybrid(h, TARGET).sort("nba_player_id")
    ret = m.hybrid(h, TARGET, returners=True).sort("nba_player_id")
    others = ~pl.col("nba_player_id").is_in(in_cohort)
    assert base.filter(others).equals(ret.filter(others))
    mine = base.filter(~others).join(ret.filter(~others), on="nba_player_id", suffix="_r")
    assert (mine["games_r"] >= mine["games"]).all()
    if raised:
        assert mine["games_r"].to_list() == pytest.approx([0.8 * 82] * mine.height)
    else:
        assert mine["games_r"].to_list() == pytest.approx(mine["games"].to_list())
    assert mine["mpg_r"].to_list() == pytest.approx(mine["mpg"].to_list())
    assert mine["pts_r"].to_list() == pytest.approx(mine["pts"].to_list())


def test_hybrid_returners_does_nothing_without_enough_evidence() -> None:
    h = lost_season_history()  # a handful of cohort rows, far below 30
    on = m.hybrid(h, TARGET, returners=True).sort("nba_player_id")
    assert on.equals(m.hybrid(h, TARGET).sort("nba_player_id"))
