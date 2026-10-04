"""Access rules over a `UserStore` (D-64, G-25 Q2 A): bootstrap the first owner, claim invites,
owner-only administration. Time comes from an injected `Clock`; the store is read on every request
(no caching), so a removal takes effect on the member's next request.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import timedelta

from dikit.time.clock import Clock
from fantasy_api.errors import ApiProblem
from fantasy_api.users.model import INVITE_TTL, Invite, Role, User, normalise_email
from fantasy_api.users.store import UserStore

LAST_SEEN_EVERY = timedelta(minutes=15)  # throttles last-seen writes; access is still checked live


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(frozen=True)
class Identity:
    """What a verified sign-in token says: the uid is the only key ever trusted."""

    uid: str
    email: str
    display_name: str | None = None


@dataclass
class UserService:
    store: UserStore
    clock: Clock
    new_id: Callable[[], str] = field(default=_new_id)

    # ---------- sign-in ----------
    def sign_in(self, who: Identity, bootstrap_owners: frozenset[str]) -> User:
        now = self.clock.now()
        email = normalise_email(who.email)
        user = self.store.get_user(who.uid)
        if user is not None:
            changed = user.email != email or (
                who.display_name is not None and user.display_name != who.display_name
            )
            if changed or now - user.last_seen_at >= LAST_SEEN_EVERY:
                user = replace(
                    user,
                    email=email,
                    display_name=who.display_name or user.display_name,
                    last_seen_at=now,
                )
                self.store.save_user(user)
            return user

        fresh = User(who.uid, email, who.display_name, "member", now, now)
        if email in bootstrap_owners and not self._owners():
            owner = replace(fresh, role="owner")  # the env allowlist bootstraps once
            if self.store.create_first_owner(owner):  # atomic: two racing sign-ins can't both win
                return owner

        invite = self.store.open_invite_for(email)
        if invite is None:
            raise ApiProblem(
                403,
                "not-invited",
                "This account hasn't been invited",
                "Sign in with the Google account the invite was sent to, or ask the owner.",
            )
        if invite.expired(now):
            raise ApiProblem(
                403, "invite-expired", "This invite has expired", "Ask the owner for a new one."
            )
        member = replace(fresh, role=invite.role)
        if not self.store.claim_invite(invite.id, member):
            raise ApiProblem(409, "invite-claimed", "This invite was just used; sign in again")
        return member

    # ---------- invites ----------
    def invite(self, by: User, email: str, role: Role) -> tuple[Invite, bool]:
        """The open invite for this email and whether it was created now (duplicates reuse it)."""
        now = self.clock.now()
        email = normalise_email(email)
        if self.store.user_by_email(email) is not None:
            raise ApiProblem(409, "already-member", "This email already belongs to a member")
        existing = self.store.open_invite_for(email)
        if existing is not None and not existing.expired(now):
            return existing, False
        if existing is not None:
            self.store.delete_invite(existing.id)  # replace the expired one
        invite = Invite(self.new_id(), email, role, by.uid, now, now + INVITE_TTL)
        self.store.save_invite(invite)
        return invite, True

    def invites(self) -> list[Invite]:
        return self.store.list_invites()

    def revoke_invite(self, invite_id: str) -> None:
        if not self.store.delete_invite(invite_id):
            raise ApiProblem(404, "not-found", "No such invite")

    # ---------- members ----------
    def members(self) -> list[User]:
        return self.store.list_users()

    def remove_member(self, uid: str) -> None:
        result = self.store.delete_user_keeping_an_owner(uid)  # atomic owner count + delete
        if result == "missing":
            raise ApiProblem(404, "not-found", "No such member")
        if result == "last-owner":
            raise ApiProblem(409, "last-owner", "The last owner can't be removed")

    def _owners(self) -> list[User]:
        return [u for u in self.store.list_users() if u.role == "owner"]
