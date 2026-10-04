"""Per-user settings (APP-009, D-64 "settings in scope"): defaults, validation and versions.

A stored document carries a `version`; the API turns it into an ETag and accepts a change only with
the matching `If-Match` (optimistic concurrency: two tabs can't silently overwrite each other).
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Literal, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

AlertType = Literal["brief", "injury", "waiver"]
Theme = Literal["system", "light", "dark"]
ALERTS: tuple[AlertType, ...] = get_args(AlertType)
THEMES: tuple[Theme, ...] = get_args(Theme)
PUNTABLE = ("pts", "reb", "ast", "stl", "blk", "fg3m", "fg_pct", "ft_pct", "tov")
STRATEGIES = ("all", *(f"punt_{c}" for c in PUNTABLE))
LINK_CODE_TTL = timedelta(minutes=10)
MAX_NAME = 60
_HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


@dataclass(frozen=True)
class Settings:
    time_zone: str = "Australia/Sydney"
    brief_enabled: bool = True
    awake_start: str = "07:00"
    awake_end: str = "22:00"
    alerts: tuple[AlertType, ...] = ALERTS
    draft_strategy: str = "all"
    theme: Theme = "system"
    display_name: str | None = None  # None: use the name from Google
    telegram_chat_id: str | None = None  # private: the API only says whether it is linked
    version: int = 0  # 0 = never saved (the defaults)


DEFAULTS = Settings()


class InvalidSettingError(ValueError):
    """A field failed validation; `field` names it for the 422 problem."""

    def __init__(self, field_name: str, message: str) -> None:
        super().__init__(message)
        self.field = field_name


def _zone(value: object) -> object:
    try:
        ZoneInfo(str(value))
    except (ZoneInfoNotFoundError, ValueError) as e:
        raise ValueError(f"{value!r} is not an IANA time zone") from e
    return str(value)


def _hhmm(value: object) -> object:
    if not isinstance(value, str) or not _HHMM.match(value):
        raise ValueError("use 24-hour HH:MM, e.g. 07:30")
    return value


def _flag(value: object) -> object:
    if not isinstance(value, bool):
        raise ValueError("must be true or false")
    return value


def _alerts(value: object) -> object:
    if not isinstance(value, list | tuple) or any(a not in ALERTS for a in value):
        raise ValueError(f"choose from {', '.join(ALERTS)}")
    return tuple(a for a in ALERTS if a in value)  # canonical order, no duplicates


def _one_of(choices: tuple[str, ...], hint: str) -> Callable[[object], object]:
    def check(value: object) -> object:
        if value not in choices:
            raise ValueError(hint)
        return value

    return check


def _name(value: object) -> object:
    if value is None:
        return None
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= MAX_NAME:
        raise ValueError(f"1 to {MAX_NAME} characters, or null to use your Google name")
    return value.strip()


_CHECKS: dict[str, Callable[[object], object]] = {
    "time_zone": _zone,
    "awake_start": _hhmm,
    "awake_end": _hhmm,
    "brief_enabled": _flag,
    "alerts": _alerts,
    "draft_strategy": _one_of(STRATEGIES, "all, or punt_<category>"),
    "theme": _one_of(THEMES, f"choose from {', '.join(THEMES)}"),
    "display_name": _name,
}


def validate(changes: dict[str, object]) -> dict[str, object]:
    """Each changed field checked and normalised; `InvalidSettingError` names the first bad one."""
    out: dict[str, object] = {}
    for key, value in changes.items():
        check = _CHECKS.get(key)
        if check is None:
            raise InvalidSettingError(key, "not a setting")
        try:
            out[key] = check(value)
        except ValueError as e:
            raise InvalidSettingError(key, str(e)) from e
    return out


def apply(current: Settings, changes: dict[str, object]) -> Settings:
    """The validated changes on top of `current`, with the next version."""
    return replace(current, **validate(changes), version=current.version + 1)  # type: ignore[arg-type]


@dataclass(frozen=True)
class LinkCode:
    code: str
    uid: str
    expires_at: datetime
    used: bool = field(default=False)

    def expired(self, now: datetime) -> bool:
        return now >= self.expires_at


def new_link_code() -> str:
    """Eight characters from an unambiguous alphabet (no 0/O, 1/I/L)."""
    alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(8))
