"""Structured logging (software-engineering standard §7): JSON outside local, console locally."""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

_SECRET_MARKERS = ("token", "secret", "password", "api_key", "authorization")


def _is_secret_key(key: object) -> bool:
    return isinstance(key, str) and any(m in key.lower() for m in _SECRET_MARKERS)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: "***" if _is_secret_key(k) else _scrub(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return type(value)(_scrub(v) for v in value)
    return value


def _redact(
    _logger: Any, _method: str, event: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for key in list(event):
        event[key] = "***" if _is_secret_key(key) else _scrub(event[key])
    return event


def configure_logging(app_env: str = "local", level: int = logging.INFO) -> None:
    renderer: Any = (
        structlog.dev.ConsoleRenderer(colors=False)
        if app_env == "local"
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact,
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        # Resolve sys.stdout per logger, not once here: a replaced/closed stream (test runners,
        # CLI harnesses) must not break later log calls.
        logger_factory=lambda *_: structlog.PrintLogger(file=sys.stdout),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> Any:
    return structlog.get_logger(name)


def bind_context(**values: str) -> None:
    """Attach run/task/job identifiers to every subsequent log event in this context."""
    structlog.contextvars.bind_contextvars(**values)


def clear_context() -> None:
    structlog.contextvars.clear_contextvars()
