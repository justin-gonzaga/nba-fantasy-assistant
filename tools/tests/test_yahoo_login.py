import pytest

from tools.yahoo_login import REDIRECT_URI, authorize_url, extract_code, parse_env


def test_authorize_url_has_required_params() -> None:
    url = authorize_url("my-client-id")
    assert url.startswith("https://api.login.yahoo.com/oauth2/request_auth?")
    assert "client_id=my-client-id" in url
    assert "response_type=code" in url
    assert "redirect_uri=https%3A%2F%2Flocalhost%3A8080" in url
    assert REDIRECT_URI == "https://localhost:8080"


@pytest.mark.parametrize(
    "pasted",
    [
        "https://localhost:8080/?code=abc123XYZ",
        "https://localhost:8080/?code=abc123XYZ&state=x",
        "  abc123XYZ  ",
    ],
)
def test_extract_code_from_url_or_bare_code(pasted: str) -> None:
    assert extract_code(pasted) == "abc123XYZ"


def test_extract_code_rejects_empty() -> None:
    with pytest.raises(ValueError, match="code"):
        extract_code("https://localhost:8080/?error=access_denied")


def test_parse_env_reads_values_without_exposing(tmp_path: object) -> None:
    import pathlib  # noqa: PLC0415 - local to keep the test self-contained

    p = pathlib.Path(str(tmp_path)) / ".env"
    p.write_text(
        "# c\nYAHOO_CLIENT_ID=abc\nYAHOO_CLIENT_SECRET = s3cr3t \nEMPTY=\n", encoding="utf-8"
    )
    env = parse_env(p)
    assert env["YAHOO_CLIENT_ID"] == "abc"
    assert env["YAHOO_CLIENT_SECRET"] == "s3cr3t"
    assert "EMPTY" not in env
