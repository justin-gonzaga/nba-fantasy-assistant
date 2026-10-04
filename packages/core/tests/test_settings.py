import pytest

from dikit.errors import ConfigError
from fantasy_core.settings import get_settings, load_settings


def test_defaults_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("APP_ENV", "DATA_ROOT", "USER_TZ", "GCP_PROJECT"):
        monkeypatch.delenv(key, raising=False)
    s = load_settings(env_file=None)
    assert s.app_env == "local"
    assert s.data_root == "data"
    assert s.user_tz == "Australia/Sydney"
    assert s.awake_start < s.awake_end


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("DATA_ROOT", "gs://fantasy-raw-dev")
    s = load_settings(env_file=None)
    assert s.app_env == "dev"
    assert s.data_root.startswith("gs://")


def test_invalid_timezone_is_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TZ", "Mars/Olympus_Mons")
    with pytest.raises(ConfigError):
        load_settings(env_file=None)


def test_invalid_env_is_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    with pytest.raises(ConfigError):
        load_settings(env_file=None)


def test_secrets_are_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("YAHOO_CLIENT_SECRET", "super-secret-value")
    s = load_settings(env_file=None)
    assert s.yahoo_client_secret is not None
    assert s.yahoo_client_secret.get_secret_value() == "super-secret-value"
    assert "super-secret-value" not in repr(s)
    assert "super-secret-value" not in str(s.model_dump())


def test_get_settings_is_cached() -> None:
    get_settings.cache_clear()
    assert get_settings() is get_settings()
