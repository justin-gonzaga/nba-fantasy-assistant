import json

import httpx
import pytest
from pydantic import SecretStr

from dikit.errors import SourceUnavailable
from fantasy_pipeline import telegram

TOKEN = SecretStr("123456:SECRET-token")


def _client(handler: httpx.MockTransport) -> telegram.Telegram:
    return telegram.Telegram(TOKEN, transport=handler)


def test_send_posts_markdown_to_the_chat() -> None:
    seen: list[httpx.Request] = []

    def handle(r: httpx.Request) -> httpx.Response:
        seen.append(r)
        return httpx.Response(200, json={"ok": True, "result": {"message_id": 7}})

    _client(httpx.MockTransport(handle)).send(42, "*Tue 20 Oct*")
    body = json.loads(seen[0].content)
    assert seen[0].url.path.endswith("/sendMessage")
    assert body == {"chat_id": 42, "text": "*Tue 20 Oct*", "parse_mode": "Markdown"}


def test_send_falls_back_to_plain_text_when_markdown_is_rejected() -> None:
    modes: list[object] = []

    def handle(r: httpx.Request) -> httpx.Response:
        body = json.loads(r.content)
        modes.append(body.get("parse_mode"))
        if body.get("parse_mode"):
            return httpx.Response(400, json={"ok": False, "description": "can't parse entities"})
        return httpx.Response(200, json={"ok": True, "result": {}})

    _client(httpx.MockTransport(handle)).send(42, "odd_text *")
    assert modes == ["Markdown", None]


def test_errors_never_contain_the_token() -> None:
    client = _client(httpx.MockTransport(lambda _r: httpx.Response(401, json={"ok": False})))
    with pytest.raises(SourceUnavailable) as err:
        client.send(42, "hi")
    assert "SECRET" not in str(err.value)
    assert "123456" not in str(err.value)


def test_chat_ids_come_from_messages_sent_to_the_bot() -> None:
    updates = {
        "ok": True,
        "result": [
            {"update_id": 1, "message": {"chat": {"id": 555, "type": "private"}, "text": "hi"}},
            {"update_id": 2, "message": {"chat": {"id": 555, "type": "private"}, "text": "again"}},
        ],
    }
    client = _client(httpx.MockTransport(lambda _r: httpx.Response(200, json=updates)))
    assert client.chat_ids() == [555]


def test_long_messages_are_split_at_line_breaks() -> None:
    text = "\n".join(f"line {i} " + "x" * 90 for i in range(100))
    parts = telegram.split(text, limit=4000)
    assert len(parts) > 1
    assert all(len(p) <= 4000 for p in parts)
    assert "\n".join(parts) == text
