"""Users and invites (D-64): user state, a separate artefact type from the data products (D-62).

Users are keyed by the sign-in provider's stable uid, never by email, so an email change keeps the
account. Emails are stored lowercased.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Role = Literal["owner", "member"]
ROLES: tuple[Role, ...] = ("owner", "member")
INVITE_TTL = timedelta(days=14)


def normalise_email(email: str) -> str:
    return email.strip().lower()


@dataclass(frozen=True)
class User:
    uid: str
    email: str
    display_name: str | None
    role: Role
    created_at: datetime
    last_seen_at: datetime


@dataclass(frozen=True)
class Invite:
    id: str
    email: str
    role: Role
    created_by: str
    created_at: datetime
    expires_at: datetime
    claimed_by: str | None = None
    claimed_at: datetime | None = None

    def expired(self, now: datetime) -> bool:
        return self.claimed_by is None and now >= self.expires_at
