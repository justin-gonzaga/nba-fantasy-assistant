"""Per-user draft settings and presets (APP-011): the document, its defaults and its validation.

One whole document per user, replaced as a unit and versioned like `/me/settings` (the API turns the
version into an ETag). Validation works on the raw JSON so every problem names its field path, e.g.
`presets[2].league.teams`. Which scoring/drafting combinations the draft room can run today is the
single constant `SUPPORTED_COMBINATIONS`; a well-formed preset outside it is `unsupported-format`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fantasy_api.users.settings import PUNTABLE
from fantasy_core.league import ScoringFormat

MAX_BODY_BYTES = 16 * 1024
MAX_PRESETS = 10
SUPPORTED_COMBINATIONS: set[tuple[ScoringFormat, str]] = {(ScoringFormat.H2H_CATEGORIES, "auction")}
CATEGORY_CODES: tuple[str, ...] = PUNTABLE  # the 9-cat default and the only categories offered
WEIGHT_STATS: tuple[str, ...] = (*PUNTABLE, "fgm", "fga", "ftm", "fta")
DRAFTING = ("auction", "snake")
PACES = ("real", "fast", "untimed", "custom")
STYLES = ("mix", "balanced", "stars", "punter", "value")
TICKS = ("off", "last10", "every")
MOTIONS = ("auto", "reduced")
_ID = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_SEASON = re.compile(r"^(\d{4})-(\d{2})$")
_MAX_NAME = 40

DEFAULT_FX: dict[str, Any] = {"sound": True, "volume": 0.6, "tick": "last10", "motion": "auto"}


@dataclass(frozen=True)
class DraftDoc:
    """The stored document: `data` is the validated, normalised JSON (camelCase keys)."""

    version: int = 0  # 0 = never saved
    data: dict[str, Any] = field(
        default_factory=lambda: {"activeId": None, "presets": [], "fx": dict(DEFAULT_FX)}
    )


class DraftSettingsError(ValueError):
    """The document failed validation at `path`; `kind` is the problem type."""

    def __init__(self, path: str, message: str, kind: str = "invalid-draft-settings") -> None:
        super().__init__(message)
        self.path = path
        self.kind = kind


def _int(value: object, path: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise DraftSettingsError(path, f"a whole number from {low} to {high}")
    return value


def _num(value: object, path: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float) or not low <= value <= high:
        raise DraftSettingsError(path, f"a number from {low} to {high}")
    return float(value) if isinstance(value, float) else value


def _choice(value: object, path: str, choices: tuple[str, ...]) -> str:
    if not isinstance(value, str) or value not in choices:
        raise DraftSettingsError(path, f"one of {', '.join(choices)}")
    return value


def _object(value: object, path: str, keys: tuple[str, ...]) -> dict[str, Any]:
    """A JSON object with no keys beyond the allowed ones (the caller checks the required ones)."""
    if not isinstance(value, dict):
        raise DraftSettingsError(path, "an object")
    for key in value:
        if key not in keys:
            raise DraftSettingsError(f"{path}.{key}" if path else key, "not a field")
    return value


def _required(obj: dict[str, Any], key: str, path: str) -> Any:
    if key not in obj:
        raise DraftSettingsError(f"{path}.{key}" if path else key, "required")
    return obj[key]


def _fx(value: object) -> dict[str, Any]:
    obj = _object(value, "fx", ("sound", "volume", "tick", "motion"))
    sound = _required(obj, "sound", "fx")
    if not isinstance(sound, bool):
        raise DraftSettingsError("fx.sound", "true or false")
    return {
        "sound": sound,
        "volume": _num(_required(obj, "volume", "fx"), "fx.volume", 0, 1),
        "tick": _choice(_required(obj, "tick", "fx"), "fx.tick", TICKS),
        "motion": _choice(_required(obj, "motion", "fx"), "fx.motion", MOTIONS),
    }


def _stat_list(value: object, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise DraftSettingsError(path, "a non-empty list of categories")
    seen: list[str] = []
    for i, item in enumerate(value):
        code = _choice(item, f"{path}[{i}]", CATEGORY_CODES)
        if code in seen:
            raise DraftSettingsError(f"{path}[{i}]", "listed twice")
        seen.append(code)
    return seen


def _weights(value: object, path: str) -> dict[str, float]:
    obj = _object(value, path, WEIGHT_STATS)
    out = {stat: _num(w, f"{path}.{stat}", -20, 20) for stat, w in obj.items()}
    if not any(out.values()):
        raise DraftSettingsError(path, "at least one non-zero weight")
    return out


def _league(value: object, path: str) -> dict[str, Any]:
    keys = ("scoring", "drafting", "teams", "budget", "spots", "seat", "categories", "weights")
    obj = _object(value, path, keys)
    scoring = ScoringFormat(
        _choice(
            _required(obj, "scoring", path),
            f"{path}.scoring",
            tuple(s.value for s in ScoringFormat),
        )
    )
    drafting = _choice(_required(obj, "drafting", path), f"{path}.drafting", DRAFTING)
    teams = _int(_required(obj, "teams", path), f"{path}.teams", 4, 20)
    budget = _required(obj, "budget", path)
    if drafting == "auction":
        budget = _int(budget, f"{path}.budget", 50, 1000)
    elif budget is not None:
        raise DraftSettingsError(f"{path}.budget", "null for a snake draft")
    out: dict[str, Any] = {
        "scoring": scoring.value,
        "drafting": drafting,
        "teams": teams,
        "budget": budget,
        "spots": _int(_required(obj, "spots", path), f"{path}.spots", 5, 25),
        "seat": _int(_required(obj, "seat", path), f"{path}.seat", 1, teams),
    }
    obj = {k: v for k, v in obj.items() if k not in ("categories", "weights") or v is not None}
    obj = {k: v for k, v in obj.items() if k not in ("categories", "weights") or v is not None}
    if "categories" in obj:
        out["categories"] = _stat_list(obj["categories"], f"{path}.categories")
    if "weights" in obj:
        out["weights"] = _weights(obj["weights"], f"{path}.weights")
    if not scoring.uses_categories and "weights" not in out:
        raise DraftSettingsError(f"{path}.weights", "required for a points format")
    return out


def _room(value: object, path: str) -> dict[str, Any]:
    obj = _object(value, path, ("pace", "nominateSeconds", "bidSeconds", "styles"))
    return {
        "pace": _choice(_required(obj, "pace", path), f"{path}.pace", PACES),
        "nominateSeconds": _int(
            _required(obj, "nominateSeconds", path), f"{path}.nominateSeconds", 5, 120
        ),
        "bidSeconds": _int(_required(obj, "bidSeconds", path), f"{path}.bidSeconds", 5, 120),
        "styles": _choice(_required(obj, "styles", path), f"{path}.styles", STYLES),
    }


def _season(value: object, path: str) -> str:
    if value == "current":
        return "current"
    match = _SEASON.match(value) if isinstance(value, str) else None
    if match is None or (int(match[1]) + 1) % 100 != int(match[2]):
        raise DraftSettingsError(path, "current, or a season like 2025-26")
    return str(value)


def _updated_at(value: object, path: str) -> str:
    try:
        when = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        when = None
    if not isinstance(value, str) or when is None or when.utcoffset() is None:
        raise DraftSettingsError(path, "an ISO-8601 UTC time like 2026-10-04T09:00:00Z")
    return when.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _punt(value: object, path: str, league: dict[str, Any]) -> str | None:
    if value is None:
        return None
    codes = league.get("categories", CATEGORY_CODES) if "weights" not in league else ()
    if not isinstance(value, str) or value not in codes:
        raise DraftSettingsError(path, "null, or one of this league's categories")
    return value


def _preset(value: object, path: str) -> dict[str, Any]:
    keys = ("id", "name", "updatedAt", "league", "room", "strategy", "season")
    obj = _object(value, path, keys)
    pid = _required(obj, "id", path)
    if not isinstance(pid, str) or not _ID.match(pid):
        raise DraftSettingsError(f"{path}.id", "1 to 40 letters, digits, _ or -")
    name = _required(obj, "name", path)
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= _MAX_NAME:
        raise DraftSettingsError(f"{path}.name", f"1 to {_MAX_NAME} characters")
    league = _league(_required(obj, "league", path), f"{path}.league")
    strategy = _object(_required(obj, "strategy", path), f"{path}.strategy", ("punt",))
    return {
        "id": pid,
        "name": name.strip(),
        "updatedAt": _updated_at(_required(obj, "updatedAt", path), f"{path}.updatedAt"),
        "league": league,
        "room": _room(_required(obj, "room", path), f"{path}.room"),
        "strategy": {
            "punt": _punt(
                _required(strategy, "punt", f"{path}.strategy"), f"{path}.strategy.punt", league
            )
        },
        "season": _season(_required(obj, "season", path), f"{path}.season"),
    }


def _supported(preset: dict[str, Any], path: str) -> None:
    league = preset["league"]
    scoring = ScoringFormat(league["scoring"])
    combo = (scoring, league["drafting"])
    if combo not in SUPPORTED_COMBINATIONS:
        field_name = (
            "drafting" if any(s == scoring for s, _ in SUPPORTED_COMBINATIONS) else "scoring"
        )
        raise DraftSettingsError(
            f"{path}.league.{field_name}",
            f"{scoring.value} with {league['drafting']} isn't available yet",
            "unsupported-format",
        )
    for extra, applies in (
        ("categories", scoring.uses_categories),
        ("weights", not scoring.uses_categories),
    ):
        if extra in league and not applies:
            raise DraftSettingsError(
                f"{path}.league.{extra}", f"not used by {scoring.value}", "unsupported-format"
            )


def validate(raw: object) -> dict[str, Any]:
    """The normalised document body, or `DraftSettingsError` naming the first bad field."""
    obj = _object(raw, "", ("activeId", "presets", "fx", "version"))
    if "version" in obj:  # what GET returned, sent back as it came; If-Match decides, not this
        _int(obj["version"], "version", 0, 2**31)
    presets_raw = _required(obj, "presets", "")
    if not isinstance(presets_raw, list):
        raise DraftSettingsError("presets", "a list")
    if len(presets_raw) > MAX_PRESETS:
        raise DraftSettingsError("presets", f"at most {MAX_PRESETS} presets")
    presets = [_preset(p, f"presets[{i}]") for i, p in enumerate(presets_raw)]
    ids: set[str] = set()
    names: set[str] = set()
    for i, p in enumerate(presets):
        if p["id"] in ids:
            raise DraftSettingsError(f"presets[{i}].id", "already used by another preset")
        if p["name"].casefold() in names:
            raise DraftSettingsError(f"presets[{i}].name", "already used by another preset")
        ids.add(p["id"])
        names.add(p["name"].casefold())
    active = _required(obj, "activeId", "")
    if active is not None and active not in ids:
        raise DraftSettingsError("activeId", "null, or the id of one of the presets")
    fx = _fx(_required(obj, "fx", ""))
    for i, p in enumerate(presets):
        _supported(p, f"presets[{i}]")
    return {"activeId": active, "presets": presets, "fx": fx}
