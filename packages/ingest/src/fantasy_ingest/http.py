"""The paced client with the browser-style headers NBA hosts require (DISC-003/004 findings).

stats.nba.com and cdn.nba.com answer 403 without them; 1.0 s spacing is used for stats.nba.com.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from dikit.store import http

BROWSER_HEADERS: Mapping[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    ),
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


class PacedClient(http.PacedClient):
    def __init__(self, source: str, **kw: Any) -> None:
        kw.setdefault("headers", BROWSER_HEADERS)
        super().__init__(source, **kw)
