---
id: APP-003
title: "OpenAPI -> TypeScript client generation + CI diff check"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [APP-002]
areas: [apps/api/**, apps/web/**, justfile, .github/workflows/ci.yml]
standards: [backend]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# APP-003 — OpenAPI -> TypeScript client generation + CI diff check

## Objective
Make the OpenAPI contract the single source of the SPA's types: generate them, fail CI on drift, add the live HTTP
client, and move the SPA onto the real response shapes (sample fixtures remain as demo mode, D-38).

## Context to read (only these)
- docs/standards/backend.md (OpenAPI is the contract; `just api-client`)
- docs/standards/frontend.md
- apps/api/openapi.json, apps/web/src/api/*

## Acceptance criteria
- [x] AC1: `just api-client` regenerates apps/api/openapi.json and apps/web/src/api/schema.gen.ts; the SPA's types
      come only from the generated file
      Verify: `just api-client` then `git status` (no diff); apps/web/src/api/types.ts
- [x] AC2: CI fails when the generated types differ from the committed contract
      Verify: .github/workflows/ci.yml web job step "generated API types match the committed contract"
- [x] AC3: `httpClient(base)` reads the views and turns problem+json into an `ApiError` with its title
      Verify: apps/web/src/api/http.test.ts
- [x] AC4: The SPA uses the live API when built with `VITE_API_URL`, else the sample data with the "Sample data"
      badge; pages render the real shapes (null record/notes/deadlines handled)
      Verify: apps/web/src/App.test.tsx (incl. "live mode"); `just web build`

## Test requirements
Vitest for the client and pages; the contract diff in CI.

## Evaluation requirements
None.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | command | `just api-client`; `git status` | regenerated, no diff (after writing openapi.json with LF on every OS) |
| AC2 | CI | ci.yml web job: `pnpm api:types && git diff --exit-code src/api/schema.gen.ts` | added; runs on this PR |
| AC3 | test | `just web test` (http.test.ts) | passed |
| AC4 | test + build | App.test.tsx (19 tests total); `just web build` | 19 passed; initial JS 113 kB gzipped (< 200 kB budget) |


## Implementation history
- 2026-09-28: openapi-typescript 7 (devDependency), `api:types` script (+ prettier), types.ts from the generated schemas, http.ts (fetch + ApiError), select.ts (VITE_API_URL -> live, else fixtures), SampleContext so the badge shows only in demo mode; pages adapted (week of <date>, expected categories instead of a week win %, optional record/notes/deadline/confidence/cta/team/positions; Freshness shows a date for date-only sources).

## Decisions
_None yet._

## Known issues
- The deployed site stays in demo mode until the API is hosted (INFRA-003/004) and `VITE_API_URL` is set at build time.

## Follow-ups
_None._
