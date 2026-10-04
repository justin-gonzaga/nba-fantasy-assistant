"""Firestore (Native) adapter for `UserStore` (G-25 Q1 A).

Only the API writes, through the server SDK and the API's service account (`roles/datastore.user`);
the database's security rules deny every client (infra/terraform/modules/env/firestore.rules).
Collections: `users/{uid}`, `invites/{id}`, `settings/{uid}`, `link_codes/{code}` and
`sims/{uid}:{id}` (with a `uid` field).
Every request reads afresh: no caching, so a removed
member is refused on their next request.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar, cast

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from fantasy_api.users.model import Invite, Role, User
from fantasy_api.users.settings import LinkCode, Settings
from fantasy_api.users.sims import Plan, Sim
from fantasy_api.users.store import DeleteResult

USERS = "users"
INVITES = "invites"
SETTINGS = "settings"
LINK_CODES = "link_codes"
SIMS = "sims"
R = TypeVar("R")


def _ts(value: Any) -> datetime:
    """Firestore returns its own datetime subclass; keep plain aware UTC datetimes."""
    d = cast(datetime, value)
    return datetime(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, tzinfo=UTC)


def _user_doc(user: User) -> dict[str, Any]:
    return {
        "email": user.email,
        "displayName": user.display_name,
        "role": user.role,
        "createdAt": user.created_at,
        "lastSeenAt": user.last_seen_at,
    }


def _user(uid: str, d: dict[str, Any]) -> User:
    return User(
        uid=uid,
        email=str(d["email"]),
        display_name=d.get("displayName"),
        role=cast(Role, d["role"]),
        created_at=_ts(d["createdAt"]),
        last_seen_at=_ts(d["lastSeenAt"]),
    )


def _invite_doc(invite: Invite) -> dict[str, Any]:
    return {
        "email": invite.email,
        "role": invite.role,
        "createdBy": invite.created_by,
        "createdAt": invite.created_at,
        "expiresAt": invite.expires_at,
        "claimedBy": invite.claimed_by,
        "claimedAt": invite.claimed_at,
    }


def _invite(invite_id: str, d: dict[str, Any]) -> Invite:
    return Invite(
        id=invite_id,
        email=str(d["email"]),
        role=cast(Role, d["role"]),
        created_by=str(d["createdBy"]),
        created_at=_ts(d["createdAt"]),
        expires_at=_ts(d["expiresAt"]),
        claimed_by=d.get("claimedBy"),
        claimed_at=_ts(d["claimedAt"]) if d.get("claimedAt") is not None else None,
    )


def _settings_doc(s: Settings) -> dict[str, Any]:
    return {
        "timeZone": s.time_zone,
        "briefEnabled": s.brief_enabled,
        "awakeStart": s.awake_start,
        "awakeEnd": s.awake_end,
        "alerts": list(s.alerts),
        "draftStrategy": s.draft_strategy,
        "theme": s.theme,
        "displayName": s.display_name,
        "telegramChatId": s.telegram_chat_id,
        "version": s.version,
    }


def _settings(d: dict[str, Any]) -> Settings:
    return Settings(
        time_zone=str(d["timeZone"]),
        brief_enabled=bool(d["briefEnabled"]),
        awake_start=str(d["awakeStart"]),
        awake_end=str(d["awakeEnd"]),
        alerts=tuple(d["alerts"]),
        draft_strategy=str(d["draftStrategy"]),
        theme=d["theme"],
        display_name=d.get("displayName"),
        telegram_chat_id=d.get("telegramChatId"),
        version=int(d["version"]),
    )


def _sim_doc(uid: str, s: Sim) -> dict[str, Any]:
    # Payloads as JSON text: Firestore has no arrays of arrays; the API never queries inside them.
    return {
        "uid": uid,
        "id": s.id,
        "kind": s.kind,
        "season": s.season,
        "title": s.title,
        "summary": json.dumps(s.summary, separators=(",", ":")),
        "detail": None if s.detail is None else json.dumps(s.detail, separators=(",", ":")),
        "pinned": s.pinned,
        "createdAt": s.created_at,
        "updatedAt": s.updated_at,
        "version": s.version,
    }


def _sim(d: dict[str, Any]) -> Sim:
    return Sim(
        id=str(d["id"]),
        kind=d["kind"],
        season=str(d["season"]),
        title=str(d["title"]),
        summary=json.loads(d["summary"]),
        detail=None if d.get("detail") is None else json.loads(d["detail"]),
        pinned=bool(d["pinned"]),
        created_at=_ts(d["createdAt"]),
        updated_at=_ts(d["updatedAt"]),
        version=int(d["version"]),
    )


class FirestoreUserStore:
    def __init__(self, client: firestore.Client) -> None:
        self._db = client

    @classmethod
    def for_project(cls, project: str) -> FirestoreUserStore:  # pragma: no cover - real GCP
        return cls(firestore.Client(project=project))

    def _get(self, collection: str, doc_id: str) -> dict[str, Any] | None:
        snap = self._db.collection(collection).document(doc_id).get()
        return snap.to_dict() if snap.exists else None

    def _delete(self, collection: str, doc_id: str) -> bool:
        ref = self._db.collection(collection).document(doc_id)
        if not ref.get().exists:
            return False
        ref.delete()
        return True

    def _where_email(self, collection: str, email: str) -> list[tuple[str, dict[str, Any]]]:
        query = self._db.collection(collection).where(filter=FieldFilter("email", "==", email))
        return [(s.id, s.to_dict() or {}) for s in query.stream()]

    def get_user(self, uid: str) -> User | None:
        d = self._get(USERS, uid)
        return _user(uid, d) if d is not None else None

    def save_user(self, user: User) -> None:
        self._db.collection(USERS).document(user.uid).set(_user_doc(user))

    def delete_user(self, uid: str) -> bool:
        return self._delete(USERS, uid)

    def list_users(self) -> list[User]:
        users = [_user(s.id, s.to_dict() or {}) for s in self._db.collection(USERS).stream()]
        return sorted(users, key=lambda u: (u.created_at, u.uid))

    def user_by_email(self, email: str) -> User | None:
        found = self._where_email(USERS, email)
        return _user(*found[0]) if found else None

    def get_invite(self, invite_id: str) -> Invite | None:
        d = self._get(INVITES, invite_id)
        return _invite(invite_id, d) if d is not None else None

    def save_invite(self, invite: Invite) -> None:
        self._db.collection(INVITES).document(invite.id).set(_invite_doc(invite))

    def delete_invite(self, invite_id: str) -> bool:
        return self._delete(INVITES, invite_id)

    def list_invites(self) -> list[Invite]:
        invites = [_invite(s.id, s.to_dict() or {}) for s in self._db.collection(INVITES).stream()]
        return sorted(invites, key=lambda i: (i.created_at, i.id))

    def open_invite_for(self, email: str) -> Invite | None:
        # A single-field equality query (automatic index); the claimed filter runs here.
        open_ = [_invite(i, d) for i, d in self._where_email(INVITES, email)]
        open_ = [i for i in open_ if i.claimed_by is None]
        return max(open_, key=lambda i: (i.created_at, i.id), default=None)

    def _owners(self) -> Any:
        return self._db.collection(USERS).where(filter=FieldFilter("role", "==", "owner"))

    def create_first_owner(self, user: User) -> bool:
        owners = self._owners()
        user_ref = self._db.collection(USERS).document(user.uid)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def create(tx: firestore.Transaction) -> bool:
            if any(True for _ in owners.limit(1).get(transaction=tx)):
                return False
            tx.set(user_ref, _user_doc(user))
            return True

        return bool(create(self._db.transaction()))

    def delete_user_keeping_an_owner(self, uid: str) -> DeleteResult:
        owners = self._owners()
        ref = self._db.collection(USERS).document(uid)
        sims = self._sims(uid)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def delete(tx: firestore.Transaction) -> DeleteResult:
            snap = ref.get(transaction=tx)
            if not snap.exists:
                return "missing"
            is_owner = (snap.to_dict() or {}).get("role") == "owner"
            if is_owner and len(list(owners.limit(2).get(transaction=tx))) <= 1:
                return "last-owner"
            saved = list(sims.get(transaction=tx))  # every read before the first write
            tx.delete(ref)
            tx.delete(self._db.collection(SETTINGS).document(uid))
            for sim in saved:
                tx.delete(sim.reference)
            return "deleted"

        result: DeleteResult = delete(self._db.transaction())
        return result

    def claim_invite(self, invite_id: str, user: User) -> bool:
        invite_ref = self._db.collection(INVITES).document(invite_id)
        user_ref = self._db.collection(USERS).document(user.uid)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def claim(tx: firestore.Transaction) -> bool:
            snap = invite_ref.get(transaction=tx)
            if not snap.exists or (snap.to_dict() or {}).get("claimedBy") is not None:
                return False
            tx.update(invite_ref, {"claimedBy": user.uid, "claimedAt": user.created_at})
            tx.set(user_ref, _user_doc(user))
            return True

        return bool(claim(self._db.transaction()))

    def get_settings(self, uid: str) -> Settings | None:
        d = self._get(SETTINGS, uid)
        return _settings(d) if d is not None else None

    def save_settings_if(self, uid: str, settings: Settings, expected_version: int) -> bool:
        ref = self._db.collection(SETTINGS).document(uid)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def save(tx: firestore.Transaction) -> bool:
            snap = ref.get(transaction=tx)
            stored = int((snap.to_dict() or {}).get("version", 0)) if snap.exists else 0
            if stored != expected_version:
                return False
            tx.set(ref, _settings_doc(settings))
            return True

        return bool(save(self._db.transaction()))

    def save_link_code(self, code: LinkCode) -> None:
        self._db.collection(LINK_CODES).document(code.code).set(
            {"uid": code.uid, "expiresAt": code.expires_at, "used": code.used}
        )

    def use_link_code(self, code: str, now: datetime) -> LinkCode | None:
        ref = self._db.collection(LINK_CODES).document(code)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def use(tx: firestore.Transaction) -> LinkCode | None:
            snap = ref.get(transaction=tx)
            if not snap.exists:
                return None
            d = snap.to_dict() or {}
            found = LinkCode(code, str(d["uid"]), _ts(d["expiresAt"]), bool(d.get("used")))
            if found.used or found.expired(now):
                return None
            tx.update(ref, {"used": True})
            return found

        result: LinkCode | None = use(self._db.transaction())
        return result

    def _sims(self, uid: str) -> Any:
        return self._db.collection(SIMS).where(filter=FieldFilter("uid", "==", uid))

    def list_sims(self, uid: str) -> list[Sim]:
        return [_sim(s.to_dict() or {}) for s in self._sims(uid).stream()]

    def mutate_sims(self, uid: str, decide: Callable[[list[Sim]], tuple[Plan, R]]) -> R:
        query = self._sims(uid)
        col = self._db.collection(SIMS)

        @firestore.transactional  # type: ignore[untyped-decorator,unused-ignore]
        def mutate(tx: firestore.Transaction) -> R:
            current = [_sim(s.to_dict() or {}) for s in query.get(transaction=tx)]
            plan, result = decide(current)  # reads above, writes below (Firestore's rule)
            for sim in plan.upserts:
                tx.set(col.document(f"{uid}:{sim.id}"), _sim_doc(uid, sim))
            for sim_id in plan.deletes:
                tx.delete(col.document(f"{uid}:{sim_id}"))
            return result

        out: R = mutate(self._db.transaction())
        return out
