"""Where the daily chain keeps its files (INFRA-006, D-63): a local folder or a gs:// prefix.

Paths below are relative to the root (e.g. "predictions/week_projection.parquet"). The default root
is the settings' WORK_ROOT ("data" locally); the cloud job uses the serve bucket, which is also
where the API reads (D-62), so publishing becomes a no-op there.
"""

from __future__ import annotations

import fsspec
import polars as pl

from dikit import jobs


class Workspace:
    def __init__(self, root: str) -> None:
        self.root = root
        self.fs, self._base = fsspec.core.url_to_fs(root)

    def url(self, rel: str) -> str:
        return f"{self._base.rstrip('/')}/{rel}" if self._base else rel

    def _parent(self, rel: str) -> None:
        parent = self.url(rel).rsplit("/", 1)[0]
        self.fs.makedirs(parent, exist_ok=True)

    def exists(self, rel: str) -> bool:
        return bool(self.fs.exists(self.url(rel)))

    def read_text(self, rel: str) -> str:
        return bytes(self.fs.cat_file(self.url(rel))).decode("utf-8")

    def write_text(self, rel: str, text: str) -> None:
        self._parent(rel)
        self.fs.pipe_file(self.url(rel), text.encode("utf-8"))

    def read_parquet(self, rel: str) -> pl.DataFrame:
        with self.fs.open(self.url(rel), "rb") as f:
            return pl.read_parquet(f)

    def write_parquet(self, rel: str, df: pl.DataFrame) -> None:
        self._parent(rel)
        with self.fs.open(self.url(rel), "wb") as f:
            df.write_parquet(f)

    def full_url(self, rel: str) -> str:
        """The URL fsspec needs to reopen the file elsewhere (keeps the protocol, e.g. gs://)."""
        protocol = self.fs.protocol if isinstance(self.fs.protocol, str) else self.fs.protocol[0]
        return self.url(rel) if protocol == "file" else f"{protocol}://{self.url(rel)}"


def RunLogSink(w: Workspace, rel: str) -> jobs.JsonlSink:  # noqa: N802 - reads as a type
    """The job runner's run log inside the workspace."""
    return jobs.JsonlSink(w.full_url(rel))


_current: Workspace | None = None


def use(root: str | None) -> Workspace | None:
    """Switch the default workspace (tests, the CLI's --work-root); None resets to settings."""
    global _current  # noqa: PLW0603 - one process-wide default, like the settings cache
    _current = Workspace(root) if root else None
    return _current


def get() -> Workspace:
    global _current  # noqa: PLW0603
    if _current is None:
        from fantasy_core.settings import get_settings  # noqa: PLC0415 - read lazily

        _current = Workspace(get_settings().work_root)
    return _current
