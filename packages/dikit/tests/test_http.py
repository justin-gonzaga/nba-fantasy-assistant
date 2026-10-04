import httpx
import pytest

from dikit.errors import SourceUnavailable
from dikit.store.http import DEFAULT_HEADERS, PacedClient


class FakeTime:
    def __init__(self) -> None:
        self.t = 100.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.t

    def sleep(self, s: float) -> None:
        self.sleeps.append(s)
        self.t += s


def _client(handler: httpx.MockTransport, ft: FakeTime, **kw: object) -> PacedClient:
    return PacedClient(
        "src_a",
        min_interval=0.6,
        transport=handler,
        monotonic=ft.monotonic,
        sleep=ft.sleep,
        retry_wait=0.0,
        **kw,  # type: ignore[arg-type]
    )


def test_sends_default_or_given_headers_and_params() -> None:
    seen: list[httpx.Request] = []

    def handle(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, content=b"{}")

    c = _client(httpx.MockTransport(handle), FakeTime())
    assert c.get("https://example.org/x", {"q": "2016"}) == b"{}"
    assert seen[0].headers["Accept"] == DEFAULT_HEADERS["Accept"]
    c2 = _client(httpx.MockTransport(handle), FakeTime(), headers={"X-Test": "1"})
    c2.get("https://example.org/x")
    assert seen[1].headers["X-Test"] == "1"
    assert seen[0].url.params["q"] == "2016"


def test_enforces_min_interval_between_requests() -> None:
    ft = FakeTime()
    c = _client(httpx.MockTransport(lambda _r: httpx.Response(200)), ft)
    c.get("https://x/a")
    ft.t += 0.2  # 0.2 s of work after the first request
    c.get("https://x/b")
    assert ft.sleeps == [pytest.approx(0.4)]
    ft.t += 5.0
    c.get("https://x/c")
    assert len(ft.sleeps) == 1  # already long enough since the last request


def test_rejects_interval_below_policy_floor() -> None:
    with pytest.raises(ValueError, match=r"0.6"):
        PacedClient("src_a", min_interval=0.5)


def test_retries_transient_errors_then_succeeds() -> None:
    codes = iter([500, 429, 200])
    c = _client(
        httpx.MockTransport(lambda _r: httpx.Response(next(codes), content=b"ok")), FakeTime()
    )
    assert c.get("https://x") == b"ok"


def test_gives_up_after_attempts() -> None:
    c = _client(httpx.MockTransport(lambda _r: httpx.Response(503)), FakeTime(), attempts=2)
    with pytest.raises(SourceUnavailable, match="503"):
        c.get("https://x")


def test_client_errors_are_not_retried() -> None:
    calls = []

    def handle(_r: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(403)

    c = _client(httpx.MockTransport(handle), FakeTime())
    with pytest.raises(SourceUnavailable, match="403"):
        c.get("https://x")
    assert len(calls) == 1


def test_timeouts_are_retried() -> None:
    state = {"n": 0}

    def handle(req: httpx.Request) -> httpx.Response:
        state["n"] += 1
        if state["n"] == 1:
            raise httpx.ReadTimeout("slow", request=req)
        return httpx.Response(200, content=b"ok")

    assert _client(httpx.MockTransport(handle), FakeTime()).get("https://x") == b"ok"


def test_get_optional_treats_403_and_404_as_not_published() -> None:
    codes = iter([403, 404, 200])

    def handle(_r: httpx.Request) -> httpx.Response:
        return httpx.Response(next(codes), content=b"pdf")

    c = _client(httpx.MockTransport(handle), FakeTime())
    assert c.get_optional("https://x/a") is None
    assert c.get_optional("https://x/b") is None
    assert c.get_optional("https://x/c") == b"pdf"


def test_get_optional_still_raises_on_other_client_errors() -> None:
    c = _client(httpx.MockTransport(lambda _r: httpx.Response(401)), FakeTime())
    with pytest.raises(SourceUnavailable, match="401"):
        c.get_optional("https://x")
