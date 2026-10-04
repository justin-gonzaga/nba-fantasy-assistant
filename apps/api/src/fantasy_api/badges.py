"""Player badges (WEB-018): short labels, each built only from stored facts or model outputs.

Every badge carries a one-line "why" made of the numbers it was decided on (explanations standard:
no invented facts). The inputs are optional files on the serve root; a missing file means those
badges are absent and a note says so, never an error.

Rules (task WEB-018, "Badge rules"):
- Injury prone: in >= 2 of the last 3 seasons he was a rotation player (>= 20 min per game played)
  yet played < 60 % of his team's games.
- Missed time: the same test on last season only, when not already Injury prone.
- Breakout chance / Bounce-back: the growth / bounce-back probability is in the top 20 % of the
  players that have one (the lift@20 cut tested in DRAFT-008 / DRAFT-007).
- Rookie: drafted in the target season's draft. First-round value (code `top_tier`): ranked within
  the league's team count under the strategy (WEB-022; tier 1 often held a single player).
- Injured today: today's injury report lists him.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import polars as pl

from fantasy_api.schemas import Badge

HISTORY = "predictions/player_history.parquet"
BREAKOUT = "predictions/breakout_probability.parquet"

# The thresholds, in one place (pinned by test_badges_constants_are_pinned).
ROTATION_MPG = 20.0  # minutes per game played that make a season a rotation season
AVAILABILITY_CUT = 0.6  # share of the team's games below which a rotation season is "low"
HISTORY_SEASONS = 3  # seasons looked back for Injury prone
INJURY_PRONE_MIN_SEASONS = 2  # low rotation seasons needed for Injury prone
TOP_SHARE = 0.2  # the top fifth of the pool for the breakout flags
PRIORITY = (
    "injured_today",
    "adjusted",  # DATA-036: an owner-reviewed raise, with its cited source
    "injury_prone",
    "missed_time",
    "breakout",
    "bounce_back",
    "rookie",
    "top_tier",
)

NO_BREAKOUT = "Breakout model not published"
NO_GROWTH = "Breakout chance appears after the pre-season backfill (draft week)"
NO_TEAMS = "First-round value appears after the next daily run"
NO_HISTORY = "Injury history not published"
_WORDS = {2: "two", 3: "three"}


@dataclass(frozen=True)
class _Season:
    season: str
    games: int
    team_games: int
    minutes: float

    @property
    def low(self) -> bool:
        """A rotation season in which he played under the availability cut."""
        if self.games <= 0 or self.team_games <= 0:
            return False
        return (
            self.minutes / self.games >= ROTATION_MPG
            and self.games / self.team_games < AVAILABILITY_CUT
        )


@dataclass
class BadgeInputs:
    """What the badge rules read, loaded once per request."""

    target_season: str | None = None
    seasons: tuple[str, ...] = ()  # the last HISTORY_SEASONS seasons before the target
    history: dict[int, list[_Season]] = field(default_factory=dict)
    draft: dict[int, tuple[int, int | None]] = field(default_factory=dict)
    top: dict[str, dict[int, float]] = field(default_factory=dict)  # kind -> player -> p
    max_tier: int = 0
    teams: int | None = None  # league size from the values file (WEB-022)
    adjusted: dict[int, str] = field(default_factory=dict)  # DATA-036 notes
    notes: list[str] = field(default_factory=list)


def _start_year(season: str) -> int | None:
    head = season[:4]
    return int(head) if head.isdigit() else None


def _season_of(year: int) -> str:
    return f"{year}-{(year + 1) % 100:02d}"


def _join(items: Sequence[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


def _top_share(table: pl.DataFrame, kind: str) -> dict[int, float]:
    pool = table.filter((pl.col("kind") == kind) & pl.col("p_breakout").is_not_null())
    if pool.is_empty():
        return {}
    k = math.ceil(len(pool) * TOP_SHARE)
    cut = pool["p_breakout"].sort(descending=True)[k - 1]
    top = pool.filter(pl.col("p_breakout") >= cut)
    return {int(r["nba_player_id"]): float(r["p_breakout"]) for r in top.iter_rows(named=True)}


def _load_breakouts(out: BadgeInputs, breakout: pl.DataFrame | None) -> None:
    if breakout is None:
        out.notes.append(NO_BREAKOUT)
        return
    if breakout.is_empty():
        return
    latest = breakout.filter(pl.col("season") == breakout["season"].max())
    out.top = {kind: _top_share(latest, kind) for kind in ("growth", "bounce_back")}
    if not out.top.get("growth"):
        out.notes.append(NO_GROWTH)


def _adjusted(values: pl.DataFrame) -> dict[int, str]:
    if "adjusted" not in values.columns:
        return {}
    rows = values.select("nba_player_id", "adjusted").drop_nulls("adjusted").iter_rows()
    return {int(pid): str(note) for pid, note in rows if note}


def _league_teams(values: pl.DataFrame) -> int | None:
    if "league_teams" not in values.columns or not values["league_teams"].drop_nulls().len():
        return None
    return _int(values["league_teams"].drop_nulls()[0])


def load_inputs(
    values: pl.DataFrame, history: pl.DataFrame | None, breakout: pl.DataFrame | None
) -> BadgeInputs:
    """Read the optional badge inputs; `values` is the auction table for the requested variant."""
    out = BadgeInputs(max_tier=_int(values["tier"].max()) or 0)
    out.teams = _league_teams(values)
    out.adjusted = _adjusted(values)
    if out.teams is None:
        out.notes.append(NO_TEAMS)
    if "season" in values.columns and values["season"].drop_nulls().len():
        out.target_season = str(values["season"].drop_nulls().max())

    _load_breakouts(out, breakout)

    if history is None:
        out.notes.append(NO_HISTORY)
        return out
    for r in history.iter_rows(named=True):
        if r.get("draft_year") is not None:
            out.draft[int(r["nba_player_id"])] = (int(r["draft_year"]), _int(r.get("overall_pick")))
    played = history.filter(
        pl.col("season").is_not_null()
        & pl.col("games_played").is_not_null()
        & pl.col("season_team_games").is_not_null()
    )
    target_year = _start_year(out.target_season) if out.target_season else None
    if target_year is not None:  # the seasons right before the target, published or not
        out.seasons = tuple(_season_of(target_year - k) for k in range(HISTORY_SEASONS, 0, -1))
    else:  # an older values file: the latest seasons in the history
        out.seasons = tuple(sorted(set(played["season"].to_list()))[-HISTORY_SEASONS:])
    for r in (
        played.filter(pl.col("season").is_in(out.seasons)).sort("season").iter_rows(named=True)
    ):
        out.history.setdefault(int(r["nba_player_id"]), []).append(
            _Season(
                season=r["season"],
                games=int(r["games_played"]),
                team_games=int(r["season_team_games"]),
                minutes=float(r["minutes"] or 0.0),
            )
        )
    return out


def _int(x: object) -> int | None:
    return int(x) if isinstance(x, int | float) else None


def _games_why(seasons: list[_Season], all_seasons: tuple[str, ...]) -> str:
    if len({s.team_games for s in seasons}) == 1:
        games = f"{_join([str(s.games) for s in seasons])} of {seasons[0].team_games} games"
    else:
        games = f"{_join([f'{s.games} of {s.team_games}' for s in seasons])} games"
    names = tuple(s.season for s in seasons)
    if names == all_seasons and len(names) in _WORDS:
        return f"Played {games} in the last {_WORDS[len(names)]} seasons"
    return f"Played {games} in {_join(list(names))}"


def badges_for(pid: int, rank: int, status: str | None, inputs: BadgeInputs) -> list[Badge]:
    """All of one player's badges, highest priority first."""
    found: list[Badge] = []
    if status:
        found.append(
            Badge(
                code="injured_today", label=status, tone="warn", why=f"{status} on today's report"
            )
        )
    if (note := inputs.adjusted.get(pid)) is not None:
        found.append(Badge(code="adjusted", label="Adjusted", tone="accent", why=note))
    seasons = inputs.history.get(pid, [])
    prone = sum(s.low for s in seasons) >= INJURY_PRONE_MIN_SEASONS
    if prone:
        found.append(
            Badge(
                code="injury_prone",
                label="Injury prone",
                tone="lose",
                why=_games_why(seasons, inputs.seasons),
            )
        )
    last = seasons[-1] if seasons else None
    if not prone and last is not None and last.season == inputs.seasons[-1] and last.low:
        found.append(
            Badge(
                code="missed_time",
                label="Missed time",
                tone="warn",
                why=f"Played {last.games} of {last.team_games} games last season",
            )
        )
    share = f"top {round(TOP_SHARE * 100)} %"
    if (p := inputs.top.get("growth", {}).get(pid)) is not None:
        found.append(
            Badge(
                code="breakout",
                label="Breakout chance",
                tone="accent",
                why=f"Breakout chance {round(p * 100)} % ({share})",
            )
        )
    if (p := inputs.top.get("bounce_back", {}).get(pid)) is not None:
        found.append(
            Badge(
                code="bounce_back",
                label="Bounce-back",
                tone="win",
                why=f"Bounce-back chance {round(p * 100)} % ({share})",
            )
        )
    target_year = _start_year(inputs.target_season) if inputs.target_season else None
    draft = inputs.draft.get(pid)
    if draft is not None and target_year is not None and draft[0] == target_year:
        pick = f", pick {draft[1]}" if draft[1] is not None else ""
        found.append(
            Badge(code="rookie", label="Rookie", tone="neutral", why=f"{draft[0]} draft{pick}")
        )
    if inputs.teams is not None and rank <= inputs.teams:
        found.append(
            Badge(
                code="top_tier",
                label="First-round value",
                tone="accent",
                why=f"#{rank} for this strategy: first-round value in a {inputs.teams}-team league",
            )
        )
    return sorted(found, key=lambda b: PRIORITY.index(b.code))
