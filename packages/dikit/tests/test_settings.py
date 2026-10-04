import pytest

from dikit.errors import ConfigError
from dikit.settings import BaseAppSettings, load


class _Product(BaseAppSettings):
    product_flag: bool = False


def test_loads_base_and_product_fields_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("PRODUCT_FLAG", "true")
    s = load(_Product, env_file=None)
    assert s.app_env == "dev"
    assert s.product_flag is True


def test_invalid_values_raise_config_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USER_TZ", "Mars/Olympus")
    with pytest.raises(ConfigError):
        load(_Product, env_file=None)
