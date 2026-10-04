"""Contract tests every `UserStore` adapter must pass (APP-008 AC1).

The Firestore run needs the emulator: `gcloud emulators firestore start --host-port=127.0.0.1:8681`
and `FIRESTORE_EMULATOR_HOST=127.0.0.1:8681` (CI starts one in the test-py job).
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from fantasy_api.users.model import Invite, User
from fantasy_api.users.store import InMemoryUserStore, UserStore

T0 = datetime(2026, 10, 3, 9, 0, tzinfo=UTC)
EMULATOR = os.environ.get("FIRESTORE_EMULATOR_HOST")


@pytest.fixture(params=["memory", "firestore"])
def store(request: pytest.FixtureRequest) -> Iterator[UserStore]:
    if request.param == "memory":
        yield InMemoryUserStore()
        return
    if not EMULATOR:
        if os.environ.get("REQUIRE_FIRESTORE_EMULATOR"):
            pytest.fail("REQUIRE_FIRESTORE_EMULATOR is set but FIRESTORE_EMULATOR_HOST is not")
        pytest.skip("Firestore emulator not running: set FIRESTORE_EMULATOR_HOST (see module doc)")
    from google.cloud import firestore  # noqa: PLC0415 - only with the emulator

    from fantasy_api.users.firestore import FirestoreUserStore  # noqa: PLC0415

    # A fresh project per test isolates the data without clearing the emulator.
    client = firestore.Client(project=f"demo-{uuid.uuid4().hex[:12]}")
    yield FirestoreUserStore(client)


def _user(uid: str = "u1", email: str = "a@example.com", role: str = "member") -> User:
    return User(
        uid=uid,
        email=email,
        display_name="Ann",
        role=role,  # type: ignore[arg-type]
        created_at=T0,
        last_seen_at=T0,
    )


def _invite(invite_id: str = "i1", email: str = "b@example.com", at: datetime = T0) -> Invite:
    return Invite(
        id=invite_id,
        email=email,
        role="member",
        created_by="owner",
        created_at=at,
        expires_at=at + timedelta(days=14),
    )


def test_users_round_trip_by_uid(store: UserStore) -> None:
    assert store.get_user("u1") is None
    user = _user()
    store.save_user(user)
    assert store.get_user("u1") == user
    store.save_user(replace(user, email="new@example.com"))
    got = store.get_user("u1")
    assert got is not None
    assert got.email == "new@example.com"
    assert [u.uid for u in store.list_users()] == ["u1"]


def test_users_are_found_by_email_and_deleted(store: UserStore) -> None:
    store.save_user(_user("u1", "a@example.com"))
    store.save_user(_user("u2", "c@example.com", role="owner"))
    found = store.user_by_email("c@example.com")
    assert found is not None
    assert found.uid == "u2"
    assert found.role == "owner"
    assert store.user_by_email("nobody@example.com") is None
    assert store.delete_user("u1") is True
    assert store.delete_user("u1") is False
    assert [u.uid for u in store.list_users()] == ["u2"]


def test_invites_round_trip_and_delete(store: UserStore) -> None:
    invite = _invite()
    store.save_invite(invite)
    assert store.get_invite("i1") == invite
    assert store.list_invites() == [invite]
    assert store.delete_invite("i1") is True
    assert store.delete_invite("i1") is False
    assert store.get_invite("i1") is None


def test_open_invite_is_the_newest_unclaimed_one_for_the_email(store: UserStore) -> None:
    store.save_invite(_invite("old", at=T0))
    store.save_invite(_invite("new", at=T0 + timedelta(hours=1)))
    store.save_invite(_invite("other", email="z@example.com"))
    found = store.open_invite_for("b@example.com")
    assert found is not None
    assert found.id == "new"
    assert store.open_invite_for("nobody@example.com") is None


def test_claiming_binds_the_uid_and_creates_the_user_once(store: UserStore) -> None:
    store.save_invite(_invite())
    member = _user("u9", "b@example.com")
    assert store.claim_invite("i1", member) is True
    claimed = store.get_invite("i1")
    assert claimed is not None
    assert claimed.claimed_by == "u9"
    assert claimed.claimed_at == member.created_at
    assert store.get_user("u9") == member
    assert store.open_invite_for("b@example.com") is None
    assert store.claim_invite("i1", _user("u10", "b@example.com")) is False
    assert store.get_user("u10") is None
    assert store.claim_invite("missing", _user("u11")) is False


# --- review: atomic owner rules (no two first owners, never zero owners) ---


def _owner(uid: str, email: str) -> User:
    t = datetime(2026, 10, 3, tzinfo=UTC)
    return User(uid, email, None, "owner", t, t)


def test_only_one_first_owner_even_when_two_race(store: UserStore) -> None:
    import threading  # noqa: PLC0415

    results: list[bool] = []
    barrier = threading.Barrier(2)

    def first(uid: str, email: str) -> None:
        barrier.wait()
        results.append(store.create_first_owner(_owner(uid, email)))

    threads = [
        threading.Thread(target=first, args=("u1", "a@example.com")),
        threading.Thread(target=first, args=("u2", "b@example.com")),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [False, True]
    assert [u.role for u in store.list_users()].count("owner") == 1


def test_the_last_owner_cannot_be_deleted(store: UserStore) -> None:
    store.create_first_owner(_owner("u1", "a@example.com"))
    assert store.delete_user_keeping_an_owner("u1") == "last-owner"
    assert store.get_user("u1") is not None
    store.save_user(_owner("u2", "b@example.com"))
    assert store.delete_user_keeping_an_owner("u1") == "deleted"
    assert store.delete_user_keeping_an_owner("nobody") == "missing"


def test_settings_compare_and_set(store: UserStore) -> None:
    """APP-009: a save succeeds only on the stored version (0 when none), so tabs can't clobber."""
    from fantasy_api.users.settings import DEFAULTS  # noqa: PLC0415

    assert store.get_settings("u1") is None
    first = replace(DEFAULTS, theme="dark", version=1)
    assert store.save_settings_if("u1", first, 0)
    assert store.get_settings("u1") == first
    assert not store.save_settings_if("u1", replace(first, theme="light", version=1), 0)
    assert store.save_settings_if("u1", replace(first, alerts=("brief",), version=2), 1)
    got = store.get_settings("u1")
    assert got is not None
    assert (got.theme, got.alerts, got.version) == ("dark", ("brief",), 2)


def test_link_codes_are_single_use_and_expire(store: UserStore) -> None:
    from fantasy_api.users.settings import LinkCode  # noqa: PLC0415

    store.save_link_code(LinkCode("ABCD2345", "u1", T0 + timedelta(minutes=10)))
    store.save_link_code(LinkCode("WXYZ6789", "u1", T0 + timedelta(minutes=10)))
    used = store.use_link_code("ABCD2345", T0)
    assert used is not None
    assert used.uid == "u1"
    assert store.use_link_code("ABCD2345", T0) is None  # used
    assert store.use_link_code("WXYZ6789", T0 + timedelta(minutes=10)) is None  # expired
    assert store.use_link_code("NOPE2345", T0) is None


def test_sims_mutate_atomically_and_go_with_the_user(store: UserStore) -> None:
    """SIM-005 AC3: one transaction per plan; a rule error writes nothing; they go with the user."""
    from fantasy_api.users.sims import Plan, Sim, SimRuleError  # noqa: PLC0415

    def sim(i: int) -> Sim:
        return Sim(f"r{i}", "practice", "2026-27", "t", {"n": i}, {"rows": [[i, i]]}, False, T0, T0)

    assert store.mutate_sims("u1", lambda sims: (Plan(upserts=(sim(1), sim(2))), len(sims))) == 0
    assert sorted(s.id for s in store.list_sims("u1")) == ["r1", "r2"]
    assert store.list_sims("u1")[0].detail is not None  # nested arrays survive the round trip
    assert {s.id: s.detail for s in store.list_sims("u1")}["r1"] == {"rows": [[1, 1]]}

    def refuse(_: list[Sim]) -> tuple[Plan, None]:
        raise SimRuleError("too-many-pins", "no")

    with pytest.raises(SimRuleError):
        store.mutate_sims("u1", refuse)
    store.mutate_sims("u1", lambda _: (Plan(deletes=("r1",)), None))
    assert [s.id for s in store.list_sims("u1")] == ["r2"]
    assert store.list_sims("u2") == []  # per user

    store.save_user(_user("u1", role="member"))
    store.save_user(_user("u9", "o@example.com", role="owner"))
    assert store.delete_user_keeping_an_owner("u1") == "deleted"
    assert store.list_sims("u1") == []


def test_draft_settings_compare_and_set(store: UserStore) -> None:
    """APP-011 AC3: atomic compare-and-set on the version (0 when none); the doc round-trips."""
    from fantasy_api.users.draft_settings import DraftDoc  # noqa: PLC0415

    assert store.get_draft_settings("u1") is None
    data = {
        "activeId": "p1",
        "presets": [{"id": "p1", "league": {"categories": ["pts", "reb"], "teams": 12}}],
        "fx": {"sound": True, "volume": 0.6, "tick": "last10", "motion": "auto"},
    }
    first = DraftDoc(1, data)
    assert store.save_draft_settings_if("u1", first, 0)
    assert store.get_draft_settings("u1") == first
    assert not store.save_draft_settings_if("u1", DraftDoc(1, {**data, "activeId": None}), 0)
    assert store.get_draft_settings("u1") == first
    assert store.save_draft_settings_if("u1", DraftDoc(2, {**data, "activeId": None}), 1)
    got = store.get_draft_settings("u1")
    assert got is not None
    assert (got.version, got.data["activeId"]) == (2, None)
    assert store.get_draft_settings("u2") is None  # per user


def test_draft_settings_go_with_the_user(store: UserStore) -> None:
    from fantasy_api.users.draft_settings import DraftDoc  # noqa: PLC0415

    store.save_user(_user("u1", role="member"))
    store.save_user(_user("u9", "o@example.com", role="owner"))
    assert store.save_draft_settings_if("u1", DraftDoc(1), 0)
    assert store.delete_user_keeping_an_owner("u1") == "deleted"
    assert store.get_draft_settings("u1") is None
