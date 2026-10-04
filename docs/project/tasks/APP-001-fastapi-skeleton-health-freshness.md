---
id: APP-001
title: "FastAPI skeleton + health/freshness"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [FND-010]
areas: [apps/api/**, pyproject.toml, platform-manifest.yaml, docs/project/**]
standards: [backend]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# APP-001 — FastAPI skeleton + health/freshness

## Objective
The web API's skeleton (FastAPI, `apps/api`, package `fantasy_api`) with `/system/health` and
`/system/freshness`, read-only over the data root the pipeline writes (D-62), RFC 9457 errors and an OpenAPI
contract snapshot, so APP-002 only adds routes.

## Context to read (only these)
- docs/standards/backend.md
- docs/project/architecture-decisions.md D-62
- apps/web/src/api/types.ts (the response shapes the SPA expects)

## Acceptance criteria
- [x] AC1: `GET /system/health` answers 200 with the status and version; the app starts with `uv run fantasy-api`
      Verify: apps/api/tests/test_system.py
- [x] AC2: `GET /system/freshness` reports, per data product (week projection, brief) and per pipeline job, when
      it was last produced (`as_of`, UTC) from the data root, read-only; a missing product is reported, not an error
      Verify: apps/api/tests/test_system.py (a temporary data root with and without files)
- [x] AC3: Errors are RFC 9457 problem+json with a stable `type` URI; no stack trace leaks
      Verify: apps/api/tests/test_errors.py
- [x] AC4: The OpenAPI schema is committed and a test fails when it drifts
      Verify: apps/api/tests/test_openapi.py (apps/api/openapi.json)

## Test requirements
TDD: route tests with FastAPI's TestClient against a temporary data root; no network, no BigQuery.

## Evaluation requirements
None (no model or decision logic).

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + smoke | apps/api/tests/test_system.py; `uv run fantasy-api --port 8765` then `curl /system/health` | passed; `{"status":"ok","version":"0.1.0"}` |
| AC2 | test + smoke | test_system.py (empty and seeded temporary data roots); `curl /system/freshness` on the real data root | passed; real run log read (7 jobs, week projection 2026-09-27) |
| AC3 | test + smoke | apps/api/tests/test_errors.py; `curl -i /today` (not built yet) | passed; 404 application/problem+json, no stack trace on a 500 |
| AC4 | test | apps/api/tests/test_openapi.py vs apps/api/openapi.json | passed; `just ci-local` 381 passed, coverage 93.18 % |

## Implementation history
- 2026-09-28: D-62 recorded (serve published files; DATA-023 dependency dropped, owner delegated). Tests first (6), then `fantasy_api` (store over fsspec, system router, problem+json handlers, app factory, `fantasy-api` entry point with `--write-openapi`). Registered in the workspace, mypy path and import-linter (`fantasy_pipeline | fantasy_api` as independent top layers).

## Decisions
- D-62 (delegated): serve published files from the data root; DATA-023 dependency dropped.

## Known issues
- Starlette warns that its TestClient's use of httpx is deprecated (library notice; revisit when FastAPI updates).
- No auth yet: APP-005 (Google sign-in + allowlist) before the API is exposed beyond localhost.

## Follow-ups
_None._
