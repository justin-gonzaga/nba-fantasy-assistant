import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from dikit.errors import ContractViolation, NaiveDatetimeError
from dikit.store.snapshot import SnapshotStore

T0 = datetime(2026, 9, 25, 4, 0, 0, tzinfo=UTC)


@pytest.fixture
def store() -> SnapshotStore:
    return SnapshotStore(f"memory://{uuid.uuid4().hex}")


def test_write_stores_payload_and_manifest(store: SnapshotStore) -> None:
    ref = store.write("src_a", "sales", "year=2016/pt=P", b'{"a": 1}', T0, rows=3)
    assert ref.path.endswith("raw/src_a/sales/year=2016/pt=P/20260925T040000000000Z.json")
    assert store.read(ref.path) == b'{"a": 1}'
    meta = json.loads(store.read(ref.meta_path))
    assert meta["observed_at"] == "2026-09-25T04:00:00+00:00"
    assert meta["rows"] == 3
    assert meta["n_bytes"] == 8
    assert len(meta["sha256"]) == 64
    assert [m["path"] for m in store.manifest("src_a")] == [ref.path]


def test_raw_is_write_once(store: SnapshotStore) -> None:
    store.write("src_a", "e", "k", b"1", T0)
    with pytest.raises(ContractViolation, match="immutable"):
        store.write("src_a", "e", "k", b"2", T0)


def test_has_and_latest_support_resume(store: SnapshotStore) -> None:
    assert not store.has("src_a", "e", "k")
    assert store.latest("src_a", "e", "k") is None
    store.write("src_a", "e", "k", b"old", T0)
    store.write("src_a", "e", "k", b"new", T0.replace(hour=5))
    assert store.has("src_a", "e", "k")
    assert store.latest("src_a", "e", "k") == b"new"
    assert not store.has("src_a", "e", "other")


def test_naive_observed_at_rejected(store: SnapshotStore) -> None:
    with pytest.raises(NaiveDatetimeError):
        store.write("src_a", "e", "k", b"1", datetime(2026, 9, 25))  # noqa: DTZ001


def test_bad_path_parts_rejected(store: SnapshotStore) -> None:
    with pytest.raises(ValueError, match="path part"):
        store.write("src_a", "../e", "k", b"1", T0)


def test_local_root(tmp_path: object) -> None:
    s = SnapshotStore(str(tmp_path))
    ref = s.write("src", "e", "k", b"x", T0)
    assert s.read(ref.path) == b"x"
    assert s.has("src", "e", "k")


def test_latest_ignores_a_longer_key_nested_under_this_one(tmp_path: Path) -> None:
    store = SnapshotStore(str(tmp_path))
    t0 = datetime(2026, 9, 28, tzinfo=UTC)
    store.write("src_a", "sales", "year=2025/kind=a", b"regular", t0)
    nested = "year=2025/kind=a/phase=pre"
    store.write("src_a", "sales", nested, b"pre", t0)
    assert store.latest("src_a", "sales", "year=2025/kind=a") == b"regular"
    assert store.latest("src_a", "sales", nested) == b"pre"


def test_as_of_returns_the_latest_snapshot_observed_by_t(store: SnapshotStore) -> None:
    store.write("src_a", "e", "k", b"old", T0)
    store.write("src_a", "e", "k", b"new", T0.replace(hour=6))
    assert store.as_of("src_a", "e", "k", T0.replace(hour=5)) == b"old"
    assert store.as_of("src_a", "e", "k", T0.replace(hour=6)) == b"new"  # at t counts
    assert store.as_of("src_a", "e", "k", T0.replace(hour=3)) is None  # nothing known yet


def test_as_of_rejects_a_naive_t(store: SnapshotStore) -> None:
    store.write("src_a", "e", "k", b"old", T0)
    with pytest.raises(NaiveDatetimeError):
        store.as_of("src_a", "e", "k", datetime(2026, 9, 25, 5))  # noqa: DTZ001 - the point of the test
