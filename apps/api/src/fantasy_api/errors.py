"""RFC 9457 problem details for every error; no stack traces in responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from dikit.logging import get_logger

PROBLEM_BASE = "/problems"  # a relative URI reference (RFC 9457 §3.1.1), stable per error class
_KINDS = {401: "unauthorised", 403: "forbidden", 404: "not-found", 405: "method-not-allowed"}
log = get_logger(__name__)


class ApiProblem(Exception):  # noqa: N818 - a problem, rendered as RFC 9457
    """Raise to answer with a problem+json of a stable kind."""

    def __init__(  # noqa: PLR0913 - the RFC 9457 members, the optional ones keyword-only
        self,
        status: int,
        kind: str,
        title: str,
        detail: str | None = None,
        *,
        headers: dict[str, str] | None = None,
        extra: dict[str, object] | None = None,
    ) -> None:
        super().__init__(title)
        self.status, self.kind, self.title, self.detail = status, kind, title, detail
        self.headers = headers
        self.extra = extra  # RFC 9457 §3.2 extension members, e.g. the current document on a 412


def problem(  # noqa: PLR0913 - the RFC 9457 members, the optional ones keyword-only
    status: int,
    kind: str,
    title: str,
    detail: str | None = None,
    *,
    headers: dict[str, str] | None = None,
    extra: dict[str, object] | None = None,
) -> JSONResponse:
    body: dict[str, object] = {"type": f"{PROBLEM_BASE}/{kind}", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    for key, value in (extra or {}).items():
        body.setdefault(key, value)  # never overrides the standard members
    return JSONResponse(
        body, status_code=status, media_type="application/problem+json", headers=headers
    )


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiProblem)
    async def _problem(_: Request, exc: ApiProblem) -> JSONResponse:
        return problem(
            exc.status, exc.kind, exc.title, exc.detail, headers=exc.headers, extra=exc.extra
        )

    @app.exception_handler(HTTPException)
    async def _http(_: Request, exc: HTTPException) -> JSONResponse:
        return problem(exc.status_code, _KINDS.get(exc.status_code, "http-error"), str(exc.detail))

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        return problem(422, "invalid-request", "Invalid request", str(exc.errors()[:3]))

    @app.exception_handler(Exception)
    async def _internal(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled", path=request.url.path, error=type(exc).__name__)
        return problem(500, "internal", "Internal error")
