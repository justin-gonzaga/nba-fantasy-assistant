"""Typed configuration (software-engineering standard §8): the kernel's base settings plus this
product's league and bot fields. Secrets are SecretStr and never logged.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import SecretStr

from dikit.settings import BaseAppSettings, load


class Settings(BaseAppSettings):
    # Where the daily chain keeps its files (predictions, briefs, league, run log): a local folder,
    # or gs://<prefix>-<env>-serve for the cloud job (INFRA-006, D-63).
    work_root: str = "data"
    # The Telegram chat for the brief when there is no local chat file (the cloud job).
    telegram_chat_id: int | None = None
    # gs://<prefix>-<env>-serve: the pipeline publishes, the API reads (D-62)
    serve_root: str | None = None
    site_url: str = ""  # INFRA-005 watchdog: the website and the API health URL to probe
    api_url: str = ""
    watchdog_muted: bool = False  # off-season: silence the watchdog without deleting it
    # APP-008: "memory" (the allowlist bootstraps the owner each start, like before) until the
    # owner's Terraform apply creates Firestore; then "firestore" (users, invites, roles persist).
    users_backend: str = "memory"
    # Who may sign in to the API (comma-separated emails, D-27) and the tokens' Firebase project
    # (default: gcp_project).
    allowed_emails: str = ""
    firebase_project: str | None = None
    # Browser origins that may call the API (comma-separated) and a regex for preview channels.
    cors_origins: str = ""
    cors_origin_regex: str = ""
    yahoo_league_key: str | None = None
    yahoo_client_id: SecretStr | None = None
    yahoo_client_secret: SecretStr | None = None
    telegram_bot_token: SecretStr | None = None
    # APP-009 (G-30 A): Telegram echoes it on every webhook call; unset turns the webhook off.
    telegram_webhook_secret: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None


def load_settings(env_file: str | None = ".env") -> Settings:
    """Build Settings, converting validation failures into ConfigError."""
    return load(Settings, env_file)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings()
