"""The `UserStore` port and its in-memory adapter (tests and local development).

Adapters hold no business rules (bootstrap, expiry, last-owner); those live in `service`.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Literal, Protocol, TypeVar

from fantasy_api.users.model import Invite, User
from fantasy_api.users.settings import LinkCode, Settings
from fantasy_api.users.sims import Plan, Sim

DeleteResult = Literal["deleted", "missing", "last-owner"]
R = TypeVar("R")


class UserStore(Protocol):
    def get_user(self, uid: str) -> User | None: ...

    def save_user(self, user: User) -> None:
        """Create or replace the user with this uid."""
        ...

    def delete_user(self, uid: str) -> bool:
        """True when a user was deleted."""
        ...

    def list_users(self) -> list[User]: ...

    def user_by_email(self, email: str) -> User | None: ...

    def get_invite(self, invite_id: str) -> Invite | None: ...

    def save_invite(self, invite: Invite) -> None: ...

    def delete_invite(self, invite_id: str) -> bool: ...

    def list_invites(self) -> list[Invite]: ...

    def open_invite_for(self, email: str) -> Invite | None:
        """The newest unclaimed invite for this (lowercased) email, expired or not."""
        ...

    def create_first_owner(self, user: User) -> bool:
        """Save `user` (an owner) only if no owner exists yet, atomically (no two first owners)."""
        ...

    def delete_user_keeping_an_owner(self, uid: str) -> DeleteResult:
        """Delete atomically unless it would leave no owner."""
        ...

    def claim_invite(self, invite_id: str, user: User) -> bool:
        """Atomically bind an unclaimed invite to `user.uid` and create the user.

        False (and no change) when the invite is missing or already claimed."""
        ...

    def get_settings(self, uid: str) -> Settings | None:
        """None when this user never saved settings (the API answers with the defaults)."""
        ...

    def save_settings_if(self, uid: str, settings: Settings, expected_version: int) -> bool:
        """Compare-and-set: save only if the stored version (0 when none) is `expected_version`."""
        ...

    def save_link_code(self, code: LinkCode) -> None: ...

    def use_link_code(self, code: str, now: datetime) -> LinkCode | None:
        """Atomically mark an unused, unexpired code used and return it; None otherwise."""
        ...

    def list_sims(self, uid: str) -> list[Sim]:
        """This user's saved sims (SIM-005), any order."""
        ...

    def mutate_sims(self, uid: str, decide: Callable[[list[Sim]], tuple[Plan, R]]) -> R:
        """Atomically: read this user's sims, let `decide` plan the writes, apply them, return its
        result.

        Rule errors raised by `decide` abort with no change."""
        ...


class InMemoryUserStore:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._invites: dict[str, Invite] = {}
        self._settings: dict[str, Settings] = {}
        self._codes: dict[str, LinkCode] = {}
        self._sims: dict[str, dict[str, Sim]] = {}
        self._lock = threading.Lock()

    def get_user(self, uid: str) -> User | None:
        return self._users.get(uid)

    def save_user(self, user: User) -> None:
        self._users[user.uid] = user

    def delete_user(self, uid: str) -> bool:
        return self._users.pop(uid, None) is not None

    def list_users(self) -> list[User]:
        return sorted(self._users.values(), key=lambda u: (u.created_at, u.uid))

    def user_by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)

    def get_invite(self, invite_id: str) -> Invite | None:
        return self._invites.get(invite_id)

    def save_invite(self, invite: Invite) -> None:
        self._invites[invite.id] = invite

    def delete_invite(self, invite_id: str) -> bool:
        return self._invites.pop(invite_id, None) is not None

    def list_invites(self) -> list[Invite]:
        return sorted(self._invites.values(), key=lambda i: (i.created_at, i.id))

    def open_invite_for(self, email: str) -> Invite | None:
        open_ = [i for i in self._invites.values() if i.email == email and i.claimed_by is None]
        return max(open_, key=lambda i: (i.created_at, i.id), default=None)

    def create_first_owner(self, user: User) -> bool:
        with self._lock:
            if any(u.role == "owner" for u in self._users.values()):
                return False
            self._users[user.uid] = user
            return True

    def delete_user_keeping_an_owner(self, uid: str) -> DeleteResult:
        with self._lock:
            target = self._users.get(uid)
            if target is None:
                return "missing"
            owners = sum(u.role == "owner" for u in self._users.values())
            if target.role == "owner" and owners <= 1:
                return "last-owner"
            del self._users[uid]
            self._settings.pop(uid, None)
            self._sims.pop(uid, None)
            return "deleted"

    def claim_invite(self, invite_id: str, user: User) -> bool:
        with self._lock:
            invite = self._invites.get(invite_id)
            if invite is None or invite.claimed_by is not None:
                return False
            self._invites[invite_id] = replace(
                invite, claimed_by=user.uid, claimed_at=user.created_at
            )
            self._users[user.uid] = user
            return True

    def get_settings(self, uid: str) -> Settings | None:
        return self._settings.get(uid)

    def save_settings_if(self, uid: str, settings: Settings, expected_version: int) -> bool:
        with self._lock:
            current = self._settings.get(uid)
            if (current.version if current else 0) != expected_version:
                return False
            self._settings[uid] = settings
            return True

    def save_link_code(self, code: LinkCode) -> None:
        self._codes[code.code] = code

    def use_link_code(self, code: str, now: datetime) -> LinkCode | None:
        with self._lock:
            found = self._codes.get(code)
            if found is None or found.used or found.expired(now):
                return None
            self._codes[code] = replace(found, used=True)
            return found

    def list_sims(self, uid: str) -> list[Sim]:
        return list(self._sims.get(uid, {}).values())

    def mutate_sims(self, uid: str, decide: Callable[[list[Sim]], tuple[Plan, R]]) -> R:
        with self._lock:
            mine = self._sims.setdefault(uid, {})
            plan, result = decide(list(mine.values()))
            for sim in plan.upserts:
                mine[sim.id] = sim
            for sim_id in plan.deletes:
                mine.pop(sim_id, None)
            return result
