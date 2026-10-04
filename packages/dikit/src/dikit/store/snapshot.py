"""Immutable raw snapshot store (bronze) over fsspec: a local path or gs:// (D-04, ADR-0005).

Layout: <root>/raw/<source>/<endpoint>/<key>/<observed_at>.json plus a <...>.meta.json sidecar
(the manifest row). Sidecars instead of an appended manifest file, because GCS objects can't
be appended to. Snapshots are write-once: an existing path is never replaced.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import fsspec

from dikit.errors import ContractViolation
from dikit.time.clock import AsOf

_PART = re.compile(r"^[A-Za-z0-9_.=\-]+$")
_META = ".meta.json"


def _check_parts(*parts: str) -> None:
    for chunk in parts:
        for part in chunk.split("/"):
            if not _PART.match(part) or part in {".", ".."}:
                msg = f"invalid path part {part!r}"
                raise ValueError(msg)


def _stamp(path: str) -> str:
    """The observed_at stamp in a snapshot's file name (sortable text: YYYYmmddTHHMMSSffffffZ)."""
    return path.rsplit("/", 1)[-1].split(".", 1)[0]


@dataclass(frozen=True)
class SnapshotRef:
    path: str
    meta_path: str


class SnapshotStore:
    def __init__(self, root: str) -> None:
        self._fs, self._root = fsspec.core.url_to_fs(root)
        self._root = self._root.rstrip("/")

    def _dir(self, source: str, endpoint: str, key: str) -> str:
        _check_parts(source, endpoint, key)
        return f"{self._root}/raw/{source}/{endpoint}/{key}"

    def write(  # noqa: PLR0913 - storage key parts + metadata are all required
        self,
        source: str,
        endpoint: str,
        key: str,
        payload: bytes,
        observed_at: datetime,
        *,
        rows: int | None = None,
        params: dict[str, Any] | None = None,
        ext: str = "json",
    ) -> SnapshotRef:
        ts = AsOf(observed_at).ts
        base = f"{self._dir(source, endpoint, key)}/{ts:%Y%m%dT%H%M%S%fZ}"
        path, meta_path = f"{base}.{ext}", f"{base}{_META}"
        # exists-then-write: safe for a single writer (the backfill CLI). Concurrent writers need a
        # store-level precondition (e.g. GCS if_generation_match=0); see DATA-001.
        if self._fs.exists(path):
            msg = f"raw snapshot already exists and is immutable: {path}"
            raise ContractViolation(msg)
        meta = {
            "path": path,
            "source": source,
            "endpoint": endpoint,
            "key": key,
            "params": params or {},
            "observed_at": ts.isoformat(),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "n_bytes": len(payload),
            "rows": rows,
        }
        self._fs.makedirs(self._dir(source, endpoint, key), exist_ok=True)
        with self._fs.open(path, "wb") as f:
            f.write(payload)
        with self._fs.open(meta_path, "wb") as f:
            f.write(json.dumps(meta, sort_keys=True).encode())
        return SnapshotRef(path, meta_path)

    def read(self, path: str) -> bytes:
        with self._fs.open(path, "rb") as f:
            data: bytes = f.read()
        return data

    def _snapshots(self, source: str, endpoint: str, key: str) -> list[str]:
        d = self._dir(source, endpoint, key)
        if not self._fs.exists(d):
            return []
        # Files only: a longer key can nest under this one (e.g. year=…/kind=a and
        # year=…/kind=a/phase=pre), and its folder must not count.
        entries = self._fs.ls(d, detail=True)
        return sorted(
            e["name"] for e in entries if e["type"] == "file" and not e["name"].endswith(_META)
        )

    def has(self, source: str, endpoint: str, key: str) -> bool:
        return bool(self._snapshots(source, endpoint, key))

    def latest(self, source: str, endpoint: str, key: str) -> bytes | None:
        snaps = self._snapshots(source, endpoint, key)
        return self.read(snaps[-1]) if snaps else None

    def as_of(self, source: str, endpoint: str, key: str, t: datetime) -> bytes | None:
        """The latest snapshot observed at or before `t` (point-in-time read); None if none yet."""
        cutoff = f"{AsOf(t).ts:%Y%m%dT%H%M%S%fZ}"
        known = [p for p in self._snapshots(source, endpoint, key) if _stamp(p) <= cutoff]
        return self.read(known[-1]) if known else None

    def manifest(self, source: str) -> list[dict[str, Any]]:
        _check_parts(source)
        metas = sorted(self._fs.glob(f"{self._root}/raw/{source}/**/*{_META}"))
        return [json.loads(self.read(m)) for m in metas]
