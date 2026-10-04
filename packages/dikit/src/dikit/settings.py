"""Typed base configuration from the environment and an env file. Secrets are SecretStr and
never logged; products subclass `BaseAppSettings` to add their own fields."""

from __future__ import annotations

from datetime import time
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dikit.errors import ConfigError

AppEnv = Literal["local", "ci", "dev", "prod"]


class BaseAppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: AppEnv = "local"
    data_root: str = Field("data", description="Local path or gs:// URI for raw data")
    gcp_project: str | None = None
    user_tz: str = "Australia/Sydney"
    awake_start: time = time(7, 0)  # notifications only inside the user's waking hours
    awake_end: time = time(23, 0)

    @field_validator("user_tz")
    @classmethod
    def _valid_tz(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"unknown time zone {v!r}") from e
        return v


def load[S: BaseAppSettings](cls: type[S], env_file: str | None = ".env") -> S:
    """Build settings of type `cls`, converting validation failures into ConfigError."""
    try:
        return cls(_env_file=env_file)  # type: ignore[call-arg]  # pydantic-settings init kwarg
    except ValidationError as e:
        raise ConfigError(str(e)) from e
