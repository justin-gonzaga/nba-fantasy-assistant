import json

import pytest

from dikit.logging import bind_context, clear_context, configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    clear_context()


def test_json_output_has_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(app_env="dev")
    bind_context(run_id="r-123", task="FND-007", job="daily")
    get_logger("test").info("job_started", rows=5)
    event = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert event["event"] == "job_started"
    assert event["run_id"] == "r-123"
    assert event["task"] == "FND-007"
    assert event["job"] == "daily"
    assert event["rows"] == 5
    assert event["level"] == "info"
    assert event["timestamp"].endswith("Z")


def test_secret_like_keys_are_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(app_env="prod")
    get_logger("test").info("token_refreshed", access_token="abc123", client_secret="xyz", ok=True)
    out = capsys.readouterr().out
    assert "abc123" not in out
    assert "xyz" not in out
    event = json.loads(out.strip().splitlines()[-1])
    assert event["access_token"] == "***"
    assert event["ok"] is True


def test_nested_secret_keys_are_redacted(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(app_env="dev")
    get_logger("test").info(
        "payload", ctx={"refresh_token": "leak1", "ok": [{"password": "leak2"}]}
    )
    out = capsys.readouterr().out
    assert "leak1" not in out
    assert "leak2" not in out
    event = json.loads(out.strip().splitlines()[-1])
    assert event["ctx"]["refresh_token"] == "***"


def test_local_renders_console(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(app_env="local")
    get_logger("test").info("hello_console")
    out = capsys.readouterr().out
    assert "hello_console" in out
    with pytest.raises(json.JSONDecodeError):
        json.loads(out.strip().splitlines()[-1])


def test_stream_is_resolved_per_call_not_at_configure(monkeypatch: pytest.MonkeyPatch) -> None:
    import io  # noqa: PLC0415
    import sys  # noqa: PLC0415

    configure_logging(app_env="prod")
    replaced = io.StringIO()
    monkeypatch.setattr(sys, "stdout", replaced)
    get_logger("t").info("after_swap")
    assert "after_swap" in replaced.getvalue()
