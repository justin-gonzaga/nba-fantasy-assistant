"""League rules: the single description of a Yahoo league's format (FR-S1..S4, ADR-0018).

Minimal version for the draft (DRAFT-003); ANL-001 extends it (DD/TD, A/T, weekly limits).
Every format difference downstream comes from this object, never from branching on names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class ScoringFormat(StrEnum):
    H2H_CATEGORIES = "h2h_categories"
    H2H_ONE_WIN = "h2h_one_win"
    ROTISSERIE = "rotisserie"
    H2H_POINTS = "h2h_points"
    SEASON_POINTS = "season_points"

    @property
    def uses_categories(self) -> bool:
        return self in {
            ScoringFormat.H2H_CATEGORIES,
            ScoringFormat.H2H_ONE_WIN,
            ScoringFormat.ROTISSERIE,
        }

    @property
    def weekly_matchups(self) -> bool:
        """Head-to-head formats are decided week by week, so weekly variance matters [R-01]."""
        return self in {
            ScoringFormat.H2H_CATEGORIES,
            ScoringFormat.H2H_ONE_WIN,
            ScoringFormat.H2H_POINTS,
        }


@dataclass(frozen=True)
class Category:
    """A scored category. Ratio categories are makes/attempts; `negative` means lower is better."""

    code: str  # e.g. "pts", "fg_pct"
    stat: str  # projected stat for counting cats, or makes for ratio cats
    attempts: str | None = None  # set for ratio cats
    negative: bool = False

    @property
    def is_ratio(self) -> bool:
        return self.attempts is not None


@dataclass(frozen=True)
class LeagueRules:
    scoring: ScoringFormat
    teams: int
    roster_slots: dict[str, int]  # e.g. {"G": 3, "F": 3, "C": 1, "Util": 3, "BN": 4, "IL": 3}
    categories: tuple[Category, ...] = ()
    modifiers: dict[str, float] = field(default_factory=dict)  # points formats: stat -> points
    auction_budget: int | None = None

    @property
    def drafted_per_team(self) -> int:
        """Slots filled at the draft (injury slots are empty at draft time)."""
        return sum(n for slot, n in self.roster_slots.items() if slot != "IL")

    @property
    def pool_size(self) -> int:
        return self.teams * self.drafted_per_team
