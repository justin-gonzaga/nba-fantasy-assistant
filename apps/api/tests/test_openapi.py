import json
from pathlib import Path

from fantasy_api.main import create_app

SNAPSHOT = Path(__file__).parents[1] / "openapi.json"


def test_openapi_matches_the_committed_contract() -> None:
    """Regenerate with `uv run fantasy-api --write-openapi` when a change is intended."""
    current = create_app("unused").openapi()
    assert json.loads(SNAPSHOT.read_text(encoding="utf-8")) == current
