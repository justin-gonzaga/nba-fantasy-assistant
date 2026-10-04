"""Telegram delivery of the daily brief (MVP-004).

The bot token comes from settings (TELEGRAM_BOT_TOKEN in .env, a SecretStr) and never appears in
logs or error messages: the request URL contains it, so errors are built from the status only.
The owner's chat id is discovered from a message they sent the bot (getUpdates) and kept in
data/telegram_chat.json (git-ignored).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from pydantic import SecretStr

from dikit.errors import SourceUnavailable

API = "https://api.telegram.org"
LIMIT = 4000  # Telegram's hard limit is 4,096 characters
CHAT_FILE = Path("data/telegram_chat.json")
SOURCE = "telegram"


def split(text: str, limit: int = LIMIT) -> list[str]:
    parts: list[str] = []
    cur: list[str] = []
    for line in text.split("\n"):
        if cur and len("\n".join([*cur, line])) > limit:
            parts.append("\n".join(cur))
            cur = []
        cur.append(line)
    parts.append("\n".join(cur))
    return parts


class Telegram:
    def __init__(self, token: SecretStr, *, transport: httpx.BaseTransport | None = None) -> None:
        self._token = token
        self._http = httpx.Client(timeout=20.0, transport=transport)

    def _call(self, method: str, payload: dict[str, Any] | None = None) -> httpx.Response:
        url = f"{API}/bot{self._token.get_secret_value()}/{method}"
        try:
            return self._http.post(url, json=payload or {})
        except httpx.HTTPError as err:  # the message may contain the URL: don't chain it
            msg = f"{method}: {type(err).__name__}"
            raise SourceUnavailable(SOURCE, msg) from None

    def send(self, chat_id: int, text: str) -> None:
        for part in split(text):
            resp = self._call(
                "sendMessage", {"chat_id": chat_id, "text": part, "parse_mode": "Markdown"}
            )
            if resp.status_code == 400:  # noqa: PLR2004 - markdown Telegram couldn't parse
                resp = self._call("sendMessage", {"chat_id": chat_id, "text": part})
            if resp.status_code != 200:  # noqa: PLR2004
                msg = f"sendMessage: HTTP {resp.status_code}"
                raise SourceUnavailable(SOURCE, msg)

    def chat_ids(self) -> list[int]:
        resp = self._call("getUpdates")
        if resp.status_code != 200:  # noqa: PLR2004
            msg = f"getUpdates: HTTP {resp.status_code}"
            raise SourceUnavailable(SOURCE, msg)
        ids = [u["message"]["chat"]["id"] for u in resp.json().get("result", []) if "message" in u]
        return sorted(set(ids))

    def close(self) -> None:
        self._http.close()


def save_chat(chat_id: int, path: Path = CHAT_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"chat_id": chat_id}), encoding="utf-8")


def load_chat(path: Path = CHAT_FILE) -> int | None:
    if not path.exists():
        return None
    return int(json.loads(path.read_text(encoding="utf-8"))["chat_id"])
