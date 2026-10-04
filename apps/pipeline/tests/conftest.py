"""Shared test setup for the pipeline app."""

from pathlib import Path

import pytest

from fantasy_pipeline import overrides


@pytest.fixture(autouse=True)
def _no_repo_overrides(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests never read the real, owner-curated overrides file in the repo (data, not a fixture)."""
    monkeypatch.setattr(overrides, "DEFAULT_PATH", tmp_path / "no_overrides.csv")
