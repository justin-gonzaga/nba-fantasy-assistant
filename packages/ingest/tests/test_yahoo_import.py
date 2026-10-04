from pathlib import Path

import pytest

from dikit.errors import ContractViolation
from fantasy_core.league import ScoringFormat
from fantasy_ingest.yahoo_import import parse_league_settings, parse_settings_table

FIX = Path(__file__).parent / "fixtures" / "yahoo_import"


def _rules(name: str):  # type: ignore[no-untyped-def]
    return parse_league_settings((FIX / name).read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("fixture", "fmt", "n_cats", "n_mods", "budget"),
    [
        ("league_settings_h2h9cat_auction.txt", ScoringFormat.H2H_CATEGORIES, 9, 0, 200),
        ("league_settings_h2h_onewin_snake.txt", ScoringFormat.H2H_ONE_WIN, 9, 0, None),
        ("league_settings_roto_auction.txt", ScoringFormat.ROTISSERIE, 9, 0, 200),
        ("league_settings_h2h_points.txt", ScoringFormat.H2H_POINTS, 0, 6, None),
        ("league_settings_season_points.txt", ScoringFormat.SEASON_POINTS, 0, 6, None),
    ],
)
def test_parses_all_five_formats(
    fixture: str, fmt: ScoringFormat, n_cats: int, n_mods: int, budget: int | None
) -> None:
    rules = _rules(fixture)
    assert rules.scoring == fmt
    assert len(rules.categories) == n_cats
    assert len(rules.modifiers) == n_mods
    assert rules.auction_budget == budget
    assert rules.teams == 16
    assert rules.roster_slots == {"G": 3, "F": 3, "C": 1, "Util": 3, "BN": 4, "IL": 3}
    assert rules.pool_size == 16 * 14


def test_nine_cat_mapping() -> None:
    rules = _rules("league_settings_h2h9cat_auction.txt")
    by = {c.code: c for c in rules.categories}
    assert set(by) == {"fg_pct", "ft_pct", "fg3m", "pts", "reb", "ast", "stl", "blk", "tov"}
    assert (by["fg_pct"].stat, by["fg_pct"].attempts) == ("fgm", "fga")
    assert by["tov"].negative
    assert not by["pts"].negative


def test_points_modifiers() -> None:
    rules = _rules("league_settings_h2h_points.txt")
    assert rules.modifiers == {
        "pts": 1.0,
        "reb": 1.2,
        "ast": 1.5,
        "stl": 3.0,
        "blk": 3.0,
        "tov": -1.0,
    }


def test_table_handles_keys_without_colons() -> None:
    table = parse_settings_table(
        "Setting\tValue\nMax Trades for Entire Season\tNo maximum\nMax Teams:\t12\n"
    )
    assert table == {"Max Trades for Entire Season": "No maximum", "Max Teams": "12"}


def test_unsupported_category_is_explicit() -> None:
    text = (
        (FIX / "league_settings_h2h9cat_auction.txt")
        .read_text(encoding="utf-8")
        .replace("Turnovers (TO)", "Double-Doubles (DD)")
    )
    with pytest.raises(ContractViolation, match="Double-Doubles"):
        parse_league_settings(text)


def test_missing_required_setting_is_explicit() -> None:
    with pytest.raises(ContractViolation, match="Scoring Type"):
        parse_league_settings("Max Teams:\t16\n")
