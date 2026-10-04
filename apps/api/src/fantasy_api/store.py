"""Read-only access to the data root the pipeline writes (a local path or a gs:// URI)."""

from __future__ import annotations

import json
from datetime import date
from typing import Any

import fsspec
import polars as pl

WEEK_PROJECTION = "predictions/week_projection.parquet"
BRIEFS = "briefs"
JOB_RUNS = "ops/job_runs.jsonl"


class DataStore:
    def __init__(self, root: str) -> None:
        self.fs, self.root = fsspec.core.url_to_fs(root)

    def _path(self, rel: str) -> str:
        return f"{self.root.rstrip('/')}/{rel}"

    def exists(self, rel: str) -> bool:
        return bool(self.fs.exists(self._path(rel)))

    def read_bytes(self, rel: str) -> bytes:
        with self.fs.open(self._path(rel), "rb") as f:
            data: bytes = f.read()
        return data

    def read_parquet(self, rel: str) -> pl.DataFrame | None:
        """The table at `rel`, or None when it hasn't been published."""
        if not self.exists(rel):
            return None
        with self.fs.open(self._path(rel), "rb") as f:
            return pl.read_parquet(f)

    def week_projection_as_of(self) -> date | None:
        if not self.exists(WEEK_PROJECTION):
            return None
        with self.fs.open(self._path(WEEK_PROJECTION), "rb") as f:
            latest = pl.read_parquet(f, columns=["as_of_day"])["as_of_day"].max()
        return latest if isinstance(latest, date) else None

    def brief_days(self, ext: str = "md") -> list[date]:
        if not self.exists(BRIEFS):
            return []
        days = []
        for p in self.fs.ls(self._path(BRIEFS), detail=False):
            name = str(p).rsplit("/", 1)[-1]
            if name.endswith(f".{ext}"):
                try:
                    days.append(date.fromisoformat(name.removesuffix(f".{ext}")))
                except ValueError:
                    continue
        return sorted(days)

    def job_runs(self) -> list[dict[str, Any]]:
        if not self.exists(JOB_RUNS):
            return []
        with self.fs.open(self._path(JOB_RUNS), "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def brief_snapshot(self, day: date | None = None) -> dict[str, Any] | None:
        """The published brief snapshot for `day`, or the latest one."""
        days = self.brief_days("json")
        if day is None:
            day = days[-1] if days else None
        if day is None or day not in days:
            return None
        with self.fs.open(
            self._path(f"{BRIEFS}/{day.isoformat()}.json"), "r", encoding="utf-8"
        ) as f:
            snap: dict[str, Any] = json.load(f)
        return snap
