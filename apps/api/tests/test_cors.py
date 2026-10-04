from pathlib import Path

from fastapi.testclient import TestClient

from fantasy_api.main import create_app

SITE = "https://nbafa-hdfo-dev.web.app"
PREVIEW = "https://nbafa-hdfo-dev--pr-42-abc123.web.app"
PREVIEW_REGEX = r"https://nbafa-hdfo-dev--pr-[a-z0-9-]+\.web\.app"


def _client(tmp_path: Path, *, docs: bool = True) -> TestClient:
    app = create_app(str(tmp_path), cors_origins=[SITE], cors_origin_regex=PREVIEW_REGEX, docs=docs)
    return TestClient(app)


def _preflight(client: TestClient, origin: str) -> dict[str, str]:
    r = client.options(
        "/today",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    return dict(r.headers)


def test_the_website_and_its_previews_may_call_the_api_with_a_token(tmp_path: Path) -> None:
    client = _client(tmp_path)
    for origin in (SITE, PREVIEW):
        h = _preflight(client, origin)
        assert h.get("access-control-allow-origin") == origin
        assert "authorization" in h.get("access-control-allow-headers", "").lower()


def test_other_origins_get_no_cors_grant(tmp_path: Path) -> None:
    h = _preflight(_client(tmp_path), "https://evil.example")
    assert "access-control-allow-origin" not in h


def test_docs_and_schema_are_off_outside_local(tmp_path: Path) -> None:
    client = _client(tmp_path, docs=False)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert _client(tmp_path).get("/openapi.json").status_code == 200
