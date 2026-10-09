"""Response models: the API's contract (camelCase on the wire, like the SPA's types).

Domain objects are never returned directly. Fields the engine doesn't compute are null, never
invented (explanations standard).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from fantasy_core.league import ScoringFormat


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Health(ApiModel):
    status: Literal["ok"]
    version: str


class Product(ApiModel):
    name: str
    as_of: date | None  # None: not produced yet


class JobFreshness(ApiModel):
    job: str
    last_status: str
    last_run: datetime
    last_success: datetime | None


class SystemFreshness(ApiModel):
    products: list[Product]
    jobs: list[JobFreshness]


class Source(ApiModel):
    name: str
    as_of: str | None


class Freshness(ApiModel):
    as_of: datetime | None  # when the brief was computed
    sources: list[Source]
    stale_since: date | None = None  # the NBA data hasn't updated since this day (INFRA-007)


class CategoryProjection(ApiModel):
    code: str
    mine: str
    theirs: str
    win_prob: float
    note: str | None = None


class Record(ApiModel):
    wins: int
    losses: int
    ties: int


class Matchup(ApiModel):
    week_start: date
    week_end: date
    days_left: int
    opponent: str | None
    record: Record | None = None  # the season record isn't ingested yet
    expected_categories: float
    categories: list[CategoryProjection]
    freshness: Freshness


class Action(ApiModel):
    id: str
    kind: Literal["lineup", "injury", "stream"]
    title: str
    detail: str
    why: list[str]
    deadline: str | None = None
    confidence: Literal["high", "medium", "low"] | None = None
    cta: str | None = None


class Today(ApiModel):
    date: date
    matchup: Matchup | None
    actions: list[Action]
    freshness: Freshness


class WaiverCandidate(ApiModel):
    id: str
    name: str
    team: str | None = None
    positions: str | None = None
    games_left: int
    helps: list[str]
    gain: float  # expected category wins gained over the waivers' horizon


class Waivers(ApiModel):
    candidates: list[WaiverCandidate]
    suggested_drop: str | None
    horizon: str = "this week"  # what `gain` covers (DEC-010: + half of next week)
    freshness: Freshness


class PlayerProjection(ApiModel):
    """Projected per-game averages for the season (the draft model, DRAFT-008)."""

    games: float
    mpg: float
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg3m: float = Field(alias="fg3m")  # not camelCased to "fg3M"
    tov: float
    fg_pct: float | None  # None when no attempts are projected
    ft_pct: float | None


class Badge(ApiModel):
    """WEB-018: a short label with the stored numbers it was decided on."""

    code: Literal[
        "injured_today",
        "adjusted",
        "injury_prone",
        "missed_time",
        "breakout",
        "bounce_back",
        "rookie",
        "top_tier",
    ]
    label: str  # the word shown (injured_today: today's status, e.g. "Questionable")
    tone: Literal["neutral", "accent", "win", "lose", "warn"]
    why: str  # one line built only from served numbers


class Indicator(ApiModel):
    """WEB-020: a decision indicator with the stored numbers behind it."""

    code: Literal["range", "certainty", "role", "punt_fit", "consistency", "age"]
    label: str
    tone: Literal["neutral", "accent", "win", "lose", "warn"]
    why: str  # one line built only from served numbers
    signal: bool = False  # may be the one chip shown in the player's row
    value: float | None = None  # for sorting: mpg change (role), spread (certainty; lower = surer)


class PlayerRow(ApiModel):
    id: int
    name: str
    team: str | None  # None until the week table knows the player's team
    positions: str | None
    rank: int
    tier: int
    dollars: float  # auction value in this league's budget
    healthy_rank: int | None = None  # WEB-019: rank if everyone played 72 games
    healthy_dollars: float | None = None
    value: float  # total standardized value (the ranking score)
    in_pool: bool  # among the players expected to be drafted
    status: str | None  # today's injury report status, if any
    strengths: dict[str, float]  # category -> standardized contribution (+ helps)
    projection: PlayerProjection | None
    badges: list[Badge] = Field(default_factory=list)  # highest priority first (WEB-018)
    indicators: list[Indicator] = Field(default_factory=list)  # WEB-020 decision panel
    signal: Indicator | None = None  # the one indicator chip for the row


class Players(ApiModel):
    variant: str  # "all" or a punt strategy, e.g. "punt_ast"
    variants: list[str]
    players: list[PlayerRow]
    # badge inputs not published yet, e.g. "Breakout model not published" (WEB-018)
    badge_notes: list[str] = Field(default_factory=list)
    freshness: Freshness


# ---------- Users, roles and invites (APP-008, D-64) ----------
Role = Literal["owner", "member"]


class Me(ApiModel):
    uid: str
    email: str
    display_name: str | None
    role: Role


class Member(Me):
    created_at: datetime
    last_seen_at: datetime


class InviteCreate(ApiModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^\s*[^@\s]+@[^@\s]+\.[^@\s]+\s*$")
    role: Role = "member"


class Invite(ApiModel):
    id: str
    email: str
    role: Role
    created_by: str  # the inviting owner's uid
    created_at: datetime
    expires_at: datetime
    claimed_by: str | None
    claimed_at: datetime | None
    status: Literal["open", "expired", "claimed"]


# ---------- settings (APP-009) ----------
AlertKind = Literal["brief", "injury", "waiver"]
ThemeChoice = Literal["system", "light", "dark"]


class UserSettings(ApiModel):
    time_zone: str
    brief_enabled: bool
    awake_start: str = Field(description="HH:MM, 24-hour, in time_zone")
    awake_end: str = Field(description="HH:MM, 24-hour, in time_zone")
    alerts: list[AlertKind]
    draft_strategy: str = Field(description="all, or punt_<category>")
    theme: ThemeChoice
    display_name: str | None
    telegram_linked: bool
    version: int = Field(description="0 until first saved; the ETag carries it too")


class SettingsPatch(ApiModel):
    """Only the fields sent change. Send with If-Match: the ETag from GET /me/settings."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    time_zone: str | None = None
    brief_enabled: bool | None = None
    awake_start: str | None = None
    awake_end: str | None = None
    alerts: list[str] | None = None
    draft_strategy: str | None = None
    theme: str | None = None
    display_name: str | None = None


# ---------- draft settings and presets (APP-011) ----------
class DraftFx(ApiModel):
    sound: bool
    volume: float = Field(ge=0, le=1)
    tick: Literal["off", "last10", "every"]
    motion: Literal["auto", "reduced"]


class DraftLeague(ApiModel):
    scoring: ScoringFormat
    drafting: Literal["auction", "snake"]
    teams: int = Field(ge=4, le=20)
    budget: int | None = Field(description="Auction budget 50..1000; null for a snake draft")
    spots: int = Field(ge=5, le=25)
    seat: int = Field(ge=1, description="1..teams; used by snake only")
    categories: list[str] | None = Field(
        default=None, description="Category formats: a subset of the stats"
    )
    weights: dict[str, float] | None = Field(
        default=None, description="Points formats: stat -> points"
    )


class DraftRoom(ApiModel):
    pace: Literal["real", "fast", "untimed", "custom"]
    nominate_seconds: int = Field(ge=5, le=120)
    bid_seconds: int = Field(ge=5, le=120)
    styles: Literal["mix", "balanced", "stars", "punter", "value"]


class DraftStrategy(ApiModel):
    punt: str | None = Field(description="null, or one of the league's category codes")


class DraftPreset(ApiModel):
    id: str = Field(description="1..40 of A-Za-z0-9_-")
    name: str = Field(description="1..40 characters, unique ignoring case")
    updated_at: datetime
    league: DraftLeague
    room: DraftRoom
    strategy: DraftStrategy
    season: str = Field(description="current, or like 2025-26")


class DraftSettings(ApiModel):
    """The saved document. PUT it back whole with If-Match: the ETag from GET /me/draft-settings."""

    active_id: str | None = Field(
        description="The preset the setup page starts with; null = built-in"
    )
    presets: list[DraftPreset] = Field(max_length=10)
    fx: DraftFx
    version: int = Field(
        description="0 until first saved; the ETag carries it too. Ignored on PUT: If-Match decides"
    )


class TelegramLink(ApiModel):
    code: str
    expires_at: datetime
    instructions: str


# ---------- saved sims (SIM-005) ----------
SimKindName = Literal["practice", "league"]


class SimIn(ApiModel):
    """A finished practice draft or a new replay league. `id` is the client's (idempotent)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    id: str
    kind: SimKindName
    season: str
    title: str
    summary: dict[str, Any] = Field(description="Small (≤ 4 KB): what the list shows")
    detail: dict[str, Any] = Field(description="The full run or league (≤ 256 KB)")


class SimUpdate(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")
    title: str
    summary: dict[str, Any]
    detail: dict[str, Any]


class SimPin(ApiModel):
    pinned: bool


class SimSummary(ApiModel):
    id: str
    kind: SimKindName
    season: str
    title: str
    summary: dict[str, Any]
    pinned: bool
    has_detail: bool = Field(description="False once an old practice run is trimmed to its summary")
    created_at: datetime
    updated_at: datetime
    version: int


class SimFull(SimSummary):
    detail: dict[str, Any] | None


class AccountExport(ApiModel):
    profile: Member
    settings: UserSettings
    draft_settings: DraftSettings
    sims: list[SimFull] = []
