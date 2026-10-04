from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fantasy_api.main import create_app


@pytest.fixture
def client_for() -> Callable[[Path], TestClient]:
    def make(root: Path) -> TestClient:
        return TestClient(create_app(str(root)), raise_server_exceptions=False)

    return make
