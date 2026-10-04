"""Assisted import of Yahoo pages (ADR-0025): the owner pastes a page and we parse it.

This module covers the League Settings page (the settings part of DISC-011): a two-column
"Setting<TAB>Value" table copied from Yahoo's "Scoring & Settings" view.
"""

from __future__ import annotations

import re

from dikit.errors import ContractViolation
from fantasy_core.league import Category, LeagueRules, ScoringFormat

SCORING_TYPES = {
    "Head-to-Head - Categories": ScoringFormat.H2H_CATEGORIES,
    "Head-to-Head - One Win": ScoringFormat.H2H_ONE_WIN,
    "Rotisserie": ScoringFormat.ROTISSERIE,
    "Head-to-Head - Points": ScoringFormat.H2H_POINTS,
    "Points": ScoringFormat.SEASON_POINTS,
}

# Yahoo abbreviation -> our category (only what the projections support; ANL-001 adds DD/TD, A/T).
CATEGORIES = {
    "FG%": Category("fg_pct", "fgm", "fga"),
    "FT%": Category("ft_pct", "ftm", "fta"),
    "3PT%": Category("fg3_pct", "fg3m", "fg3a"),
    "3PTM": Category("fg3m", "fg3m"),
    "PTS": Category("pts", "pts"),
    "REB": Category("reb", "reb"),
    "AST": Category("ast", "ast"),
    "ST": Category("stl", "stl"),
    "BLK": Category("blk", "blk"),
    "TO": Category("tov", "tov", negative=True),
    "FGM": Category("fgm", "fgm"),
    "FGA": Category("fga", "fga"),
    "FTM": Category("ftm", "ftm"),
    "FTA": Category("fta", "fta"),
}
STAT_OF = {abbr: cat.stat for abbr, cat in CATEGORIES.items() if not cat.is_ratio}

_ABBR = re.compile(r"\(([^)]+)\)")
_MODIFIER = re.compile(r"\(([^)]+)\):\s*(-?\d+(?:\.\d+)?)")


def parse_settings_table(text: str) -> dict[str, str]:
    """`Key:<TAB>Value` lines (the colon is optional) -> dict; header/blank lines skipped."""
    table: dict[str, str] = {}
    for line in text.splitlines():
        if "\t" not in line:
            continue
        key, _, value = line.partition("\t")
        key = key.strip().rstrip(":").strip()
        if key and key != "Setting":
            table[key] = value.strip()
    return table


def _require(table: dict[str, str], key: str) -> str:
    if key not in table:
        msg = f"league settings paste is missing '{key}'"
        raise ContractViolation(msg)
    return table[key]


def _categories(line: str) -> tuple[Category, ...]:
    out = []
    for part in line.split(","):
        m = _ABBR.search(part)
        abbr = m.group(1) if m else ""
        if abbr not in CATEGORIES:
            msg = f"unsupported stat category {part.strip()!r} (supported: {sorted(CATEGORIES)})"
            raise ContractViolation(msg)
        out.append(CATEGORIES[abbr])
    return tuple(out)


def _modifiers(line: str) -> dict[str, float]:
    mods = {}
    for abbr, pts in _MODIFIER.findall(line):
        if abbr not in STAT_OF:
            msg = f"unsupported stat modifier {abbr!r}"
            raise ContractViolation(msg)
        mods[STAT_OF[abbr]] = float(pts)
    return mods


def parse_league_settings(text: str) -> LeagueRules:
    table = parse_settings_table(text)
    scoring_text = _require(table, "Scoring Type")
    if scoring_text not in SCORING_TYPES:
        msg = f"unknown scoring type {scoring_text!r}"
        raise ContractViolation(msg)
    scoring = SCORING_TYPES[scoring_text]
    slots: dict[str, int] = {}
    for pos in _require(table, "Roster Positions").split(","):
        slots[pos.strip()] = slots.get(pos.strip(), 0) + 1
    budget_text = table.get("Salary Cap Draft Budget")
    budget = (
        int(budget_text.lstrip("$"))
        if budget_text and "Salary Cap" in table.get("Draft Type", "")
        else None
    )
    if scoring.uses_categories:
        categories, modifiers = _categories(_require(table, "Players Stat Categories")), {}
    else:
        categories, modifiers = (), _modifiers(_require(table, "Stat Modifiers"))
    return LeagueRules(
        scoring=scoring,
        teams=int(_require(table, "Max Teams")),
        roster_slots=slots,
        categories=categories,
        modifiers=modifiers,
        auction_budget=budget,
    )
