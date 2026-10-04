import httpx

from fantasy_ingest.http import BROWSER_HEADERS, PacedClient


def test_nba_client_sends_browser_headers() -> None:
    seen: list[httpx.Request] = []

    def handle(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, content=b"{}")

    c = PacedClient("nba_stats", min_interval=0.6, transport=httpx.MockTransport(handle))
    assert c.get("https://stats.nba.com/stats/x") == b"{}"
    assert seen[0].headers["Referer"] == BROWSER_HEADERS["Referer"]
    assert "Mozilla" in seen[0].headers["User-Agent"]
