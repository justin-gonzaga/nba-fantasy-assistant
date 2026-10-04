"""Paced, retrying HTTP client for polite fetching from public sources.

- A minimum interval between requests (policy floor 0.6 s).
- Retries with exponential backoff on timeouts, connection errors, 429 and 5xx only.
- `get_optional` treats 403/404 as "not published yet" (None).
- Headers are the caller's: some hosts refuse requests without browser-style headers.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

import httpx
from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from dikit.errors import SourceUnavailable

MIN_INTERVAL_FLOOR = 0.6

DEFAULT_HEADERS: Mapping[str, str] = {"Accept": "application/json, text/plain, */*"}


class _TransientError(Exception):
    pass


def _is_transient(exc: BaseException) -> bool:
    return isinstance(exc, _TransientError | httpx.TimeoutException | httpx.TransportError)


class PacedClient:
    def __init__(  # noqa: PLR0913 - explicit knobs keep tests deterministic
        self,
        source: str,
        *,
        min_interval: float = 1.0,
        attempts: int = 4,
        timeout: float = 30.0,
        retry_wait: float = 2.0,
        transport: httpx.BaseTransport | None = None,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        headers: Mapping[str, str] = DEFAULT_HEADERS,
    ) -> None:
        if min_interval < MIN_INTERVAL_FLOOR:
            msg = f"min_interval must be >= {MIN_INTERVAL_FLOOR} s (source politeness policy)"
            raise ValueError(msg)
        self.source = source
        self._min_interval = min_interval
        self._attempts = attempts
        self._retry_wait = retry_wait
        self._monotonic = monotonic
        self._sleep = sleep
        self._last: float | None = None
        self._http = httpx.Client(headers=dict(headers), timeout=timeout, transport=transport)

    def _pace(self) -> None:
        if self._last is not None:
            wait = self._min_interval - (self._monotonic() - self._last)
            if wait > 0:
                self._sleep(wait)
        self._last = self._monotonic()

    def _once(
        self, url: str, params: Mapping[str, str] | None, missing_ok: bool = False
    ) -> bytes | None:
        self._pace()
        resp = self._http.get(url, params=params)
        if missing_ok and resp.status_code in {403, 404}:
            return None  # static hosts often answer 403 for files not published yet
        if resp.status_code == 429 or resp.status_code >= 500:  # noqa: PLR2004
            raise _TransientError(f"HTTP {resp.status_code}")
        if resp.status_code != 200:  # noqa: PLR2004
            raise SourceUnavailable(self.source, f"HTTP {resp.status_code} for {url}")
        return resp.content

    def get(self, url: str, params: Mapping[str, str] | None = None) -> bytes:
        payload = self._get(url, params, missing_ok=False)
        assert payload is not None  # noqa: S101 - _once only returns None when missing_ok
        return payload

    def get_optional(self, url: str, params: Mapping[str, str] | None = None) -> bytes | None:
        """None when the file doesn't exist (yet): HTTP 403 or 404."""
        return self._get(url, params, missing_ok=True)

    def _get(self, url: str, params: Mapping[str, str] | None, *, missing_ok: bool) -> bytes | None:
        retrying = Retrying(
            stop=stop_after_attempt(self._attempts),
            wait=wait_exponential(multiplier=self._retry_wait, max=60),
            retry=retry_if_exception(_is_transient),
            sleep=self._sleep,
        )
        try:
            return retrying(self._once, url, params, missing_ok)
        except RetryError as err:
            last = err.last_attempt.exception()
            raise SourceUnavailable(self.source, f"{last} for {url}") from err

    def close(self) -> None:
        self._http.close()
