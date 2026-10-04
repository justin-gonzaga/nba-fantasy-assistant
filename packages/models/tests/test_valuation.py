import numpy as np
import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fantasy_core.league import Category, LeagueRules, ScoringFormat
from fantasy_models import valuation as v
from fantasy_models.preseason import methods as m
from fantasy_models.preseason.project import project_pool
from fantasy_models.preseason.synthetic import make_league

NINE = (
    Category("fg_pct", "fgm", "fga"),
    Category("ft_pct", "ftm", "fta"),
    Category("fg3m", "fg3m"),
    Category("pts", "pts"),
    Category("reb", "reb"),
    Category("ast", "ast"),
    Category("stl", "stl"),
    Category("blk", "blk"),
    Category("tov", "tov", negative=True),
)
SLOTS = {"G": 3, "F": 3, "C": 1, "Util": 3, "BN": 4, "IL": 3}


def rules(
    fmt: ScoringFormat = ScoringFormat.H2H_CATEGORIES, teams: int = 8, budget: int | None = 200
) -> LeagueRules:
    if fmt.uses_categories:
        return LeagueRules(fmt, teams, SLOTS, NINE, auction_budget=budget)
    return LeagueRules(
        fmt,
        teams,
        SLOTS,
        modifiers={"pts": 1, "reb": 1.2, "ast": 1.5, "stl": 3, "blk": 3, "tov": -1},
    )


SEASONS, DRAFT = make_league(seed=3, n_players=260)
POOL = SEASONS.filter(pl.col("season") == "2025-26").select(
    "nba_player_id", pl.lit(None, pl.Int64).alias("overall_pick")
)
PROJ = project_pool(SEASONS, DRAFT, POOL, "2026-27", m.hybrid).drop("source", "mpg_band")
POS_CYCLE = ["G", "F", "C", "G-F", "F-C"]
POSITIONS = PROJ.select(
    "nba_player_id",
    pl.Series("nba_position", [POS_CYCLE[i % len(POS_CYCLE)] for i in range(PROJ.height)]),
)
WITHIN = {c.code: 1.0 for c in NINE}


def test_valuation_formats_all_five() -> None:
    """AC1: every format produces a valuation through LeagueRules alone."""
    for fmt in ScoringFormat:
        r = rules(fmt, budget=200 if fmt.uses_categories else None)
        out = v.value_all(PROJ, POSITIONS, r, WITHIN)
        allv = out.filter(pl.col("variant") == "all")
        assert allv.height == PROJ.height
        assert allv.filter(pl.col("drafted")).height == r.pool_size
        if fmt.uses_categories:
            assert set(out.get_column("variant")) == {"all", *(f"punt_{c.code}" for c in NINE)}
        else:
            assert "s_fpts" in out.columns
            assert set(out.get_column("variant")) == {"all"}


def test_roto_ignores_weekly_variance_h2h_uses_it() -> None:
    big = {c.code: 1e6 for c in NINE}
    ids = PROJ.get_column("nba_player_id").to_numpy()
    roto = v.category_scores(PROJ, rules(ScoringFormat.ROTISSERIE), big, ids)
    roto0 = v.category_scores(PROJ, rules(ScoringFormat.ROTISSERIE), {}, ids)
    h2h = v.category_scores(PROJ, rules(ScoringFormat.H2H_CATEGORIES), big, ids)
    assert np.allclose(roto["s_pts"].to_numpy(), roto0["s_pts"].to_numpy())
    assert np.abs(h2h["s_pts"].to_numpy()).max() < np.abs(roto["s_pts"].to_numpy()).max()


@settings(max_examples=40, deadline=None)
@given(extra_fga=st.floats(0.5, 10), pct_above=st.floats(0.02, 0.2), extra_tov=st.floats(0.5, 5))
def test_ratio_and_negative_categories(
    extra_fga: float, pct_above: float, extra_tov: float
) -> None:
    """AC2: more volume at an above-league % raises the FG% score; more turnovers lower TO's."""
    ids = PROJ.get_column("nba_player_id").to_numpy()
    base = PROJ.row(0, named=True)
    lg = float(PROJ["fgm"].sum()) / float(PROJ["fga"].sum())
    pct = min(lg + pct_above, 0.95)

    def with_player(fga: float, tov: float) -> dict[str, float]:
        row = {**base, "nba_player_id": -1, "fga": fga, "fgm": fga * pct, "tov": tov}
        df = pl.concat([PROJ, pl.DataFrame([row], schema=PROJ.schema)])
        s = (
            v.category_scores(df, rules(), WITHIN, ids)
            .filter(pl.col("nba_player_id") == -1)
            .row(0, named=True)
        )
        return {"fg": s["s_fg_pct"], "tov": s["s_tov"]}

    lo, hi = with_player(5.0, 1.0), with_player(5.0 + extra_fga, 1.0 + extra_tov)
    assert hi["fg"] > lo["fg"]
    assert hi["tov"] < lo["tov"]


def test_punt_variant_invariants() -> None:
    """AC3: punting c drops exactly c's contribution; every other category score is unchanged."""
    r = rules()
    out = v.value_all(PROJ, POSITIONS, r, WITHIN)
    allv = out.filter(pl.col("variant") == "all").sort("nba_player_id")
    for cat in NINE:
        punt = out.filter(pl.col("variant") == f"punt_{cat.code}").sort("nba_player_id")
        for other in NINE:
            assert np.allclose(
                allv[f"s_{other.code}"].to_numpy(), punt[f"s_{other.code}"].to_numpy()
            )
        assert np.allclose(
            (allv["value"] - allv[f"s_{cat.code}"]).to_numpy(), punt["value"].to_numpy()
        )


def test_auction_dollars_add_up() -> None:
    r = rules()
    out = v.value_all(PROJ, POSITIONS, r, WITHIN).filter(pl.col("variant") == "all")
    drafted = out.filter(pl.col("drafted"))
    assert drafted.get_column("dollars").sum() == pytest.approx(r.teams * 200)
    assert float(drafted.get_column("dollars").min()) >= 1.0  # type: ignore[arg-type]
    assert out.filter(~pl.col("drafted")).get_column("dollars").sum() == 0
    # monotone: more value over replacement -> at least as many dollars
    d = drafted.sort("vor")
    assert (np.diff(d.get_column("dollars").to_numpy()) >= -1e-9).all()


def test_positions_are_filled_before_flex() -> None:
    r = rules()
    out = v.value_all(PROJ, POSITIONS, r, WITHIN).filter(
        (pl.col("variant") == "all") & pl.col("drafted")
    )
    centres = out.filter(pl.col("nba_position").is_in(["C", "F-C", "C-F"])).height
    assert centres >= r.roster_slots["C"] * r.teams


def test_snake_leagues_get_ranks_not_dollars() -> None:
    out = v.value_all(PROJ, POSITIONS, rules(ScoringFormat.H2H_ONE_WIN, budget=None), WITHIN)
    assert out.get_column("dollars").null_count() == out.height
    assert out.filter(pl.col("variant") == "all").get_column("overall_rank").min() == 1


def test_eligibility_and_tiers() -> None:
    assert v.eligibility("G-F") == ("G", "F")
    assert v.eligibility(None) == ()
    t = v.tiers(np.array([10.0, 9.9, 5.0, 4.9, 1.0]))
    assert t.to_list()[0] == t.to_list()[1] < t.to_list()[2] == t.to_list()[3] < t.to_list()[4]


def test_tiers_are_capped_at_a_draft_round() -> None:
    """WEB-022: dense values used to land 585 of 589 players in one tier."""
    dense = np.linspace(5.0, 4.0, 64)  # no big gaps anywhere
    t = v.tiers(dense, max_size=16).to_list()
    assert max(t) == 4  # 64 players / 16 per round
    assert all(t.count(k) == 16 for k in range(1, 5))
    gap = np.array([10.0, 9.9, *np.linspace(5.0, 4.0, 20)])
    assert v.tiers(gap, max_size=16).to_list()[:3] == [1, 1, 2]  # gap breaks still apply


def test_values_carry_the_league_size_and_round_tiers() -> None:
    vals = v.value_all(PROJ, POSITIONS, rules(teams=8), WITHIN).filter(pl.col("variant") == "all")
    assert vals["league_teams"].unique().to_list() == [8]
    assert max(vals.group_by("tier").len()["len"].to_list()) <= 8


# ------------------------------------------------------------------ DRAFT-011: replacement fill
def _two(games: tuple[float, float]) -> pl.DataFrame:
    return pl.DataFrame(
        {"nba_player_id": [1, 2], "games": list(games), "pts": [20.0, 20.0], "reb": [5.0, 5.0]}
    )


def test_replacement_fill_leaves_full_season_players_unchanged() -> None:
    full = _two((82.0, 82.0))
    repl = {"pts": 10.0, "reb": 3.0}
    assert v.weekly(full, ["pts", "reb"], repl).equals(v.weekly(full, ["pts", "reb"]))


def test_replacement_fill_credits_missed_games_at_replacement_level() -> None:
    repl = {"pts": 10.0, "reb": 3.0}
    w = v.weekly(_two((82.0, 42.0)), ["pts", "reb"], repl)
    gap = w["w_pts"][0] - w["w_pts"][1]
    assert gap == pytest.approx((82 - 42) * (20.0 - 10.0) / v.SEASON_WEEKS)
    no_fill = v.weekly(_two((82.0, 42.0)), ["pts", "reb"])
    assert no_fill["w_pts"][0] - no_fill["w_pts"][1] == pytest.approx(40 * 20.0 / v.SEASON_WEEKS)


def test_replacement_line_is_just_outside_the_pool() -> None:
    proj = pl.DataFrame({"nba_player_id": [1, 2, 3, 4, 5, 6], "pts": [30.0, 25, 20, 12, 10, 1]})
    line = v.replacement_line(proj, [1, 2, 3, 4, 5, 6], ["pts"], pool_size=3, n=2)
    assert line == {"pts": pytest.approx(11.0)}  # ranks 4 and 5


def test_an_injured_star_ranks_higher_with_replacement_fill() -> None:
    star = PROJ.sort("pts", descending=True)["nba_player_id"][0]
    hurt = PROJ.with_columns(
        pl.when(pl.col("nba_player_id") == star)
        .then(35.0)
        .otherwise(pl.col("games"))
        .alias("games")
    )

    def rank(fill: bool) -> int:
        vals = v.value_all(hurt, POSITIONS, rules(), WITHIN, fill=fill).filter(
            pl.col("variant") == "all"
        )
        return int(vals.filter(pl.col("nba_player_id") == star)["overall_rank"][0])

    assert rank(fill=True) < rank(fill=False)
