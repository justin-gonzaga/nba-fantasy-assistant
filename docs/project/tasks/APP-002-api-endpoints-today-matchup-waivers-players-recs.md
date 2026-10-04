---
id: APP-002
title: "API endpoints: today, matchup, waivers (from the brief snapshot)"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [APP-001]
areas: [apps/api/**, apps/pipeline/src/fantasy_pipeline/daily_brief.py, apps/pipeline/src/fantasy_pipeline/jobs_nba.py, apps/pipeline/src/fantasy_pipeline/cli.py, apps/pipeline/tests/**]
standards: [backend]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# APP-002 — API endpoints: today, matchup, waivers (from the brief snapshot)

## Objective
First slice of the endpoints: `/today`, `/matchup` and `/waivers`, served from the brief snapshot the daily job now
publishes (`briefs/{day}.json`, D-62). Players, recommendations, trades and evaluation follow in later slices
(DEC-010 wires the engine's logged recommendations; this slice doesn't wait for it).

## Context to read (only these)
- docs/standards/backend.md
- apps/web/src/api/types.ts
- D-62 in docs/project/architecture-decisions.md

## Acceptance criteria
- [x] AC1: The daily brief job publishes a versioned JSON snapshot next to the markdown, holding only what the engine
      computed (outlook, team totals, lineup, injuries, pickups, sources)
      Verify: apps/pipeline/tests/test_daily_brief.py::test_compose_gives_the_markdown_and_a_json_snapshot
- [x] AC2: `GET /today`, `/matchup`, `/waivers` serve the latest snapshot (or `?day=`) in camelCase; values the
      engine doesn't compute (season record, per-category notes, deadlines, confidence) are null, never invented
      Verify: apps/api/tests/test_views.py
- [x] AC3: No snapshot -> 404 problem `no-brief`; an unsupported snapshot schema -> 503 problem `snapshot-schema`;
      an invalid `?day=` -> 422 problem `invalid-request`
      Verify: apps/api/tests/test_views.py, test_errors.py
- [x] AC4: The OpenAPI contract is updated
      Verify: apps/api/tests/test_openapi.py

## Test requirements
TDD: route tests over a temporary data root with a snapshot built by the pipeline's own `compose`.

## Evaluation requirements
None (serving computed outputs; no new decision logic).

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + smoke | test_daily_brief.py (compose, publish); `python -m fantasy_pipeline brief --sample --league <tmp> --at 2026-09-27T20:00:00+00:00` | passed; `data/briefs/2026-09-27.json` written (smoke files removed after) |
| AC2 | test + smoke | apps/api/tests/test_views.py; test_snapshot_contract.py (a pipeline-built snapshot through every view); `curl /today?day=2026-09-27` on the running API | passed; real snapshot served (pre-season: zero totals, 4.5 expected categories) |
| AC3 | test | test_views.py (404 no-brief, 503 snapshot-schema, 422 invalid day) | passed |
| AC4 | test | test_openapi.py vs regenerated apps/api/openapi.json | passed; `just ci-local` 390 passed, coverage 93.40 % |

## Implementation history
- 2026-09-28: `daily_brief.compose` (markdown + snapshot, schema 1) and `publish` (md + json), used by the daily job
  and the `brief` command. API: camelCase models (`ApiModel`), `ApiProblem`, `DataStore.brief_snapshot`, views
  router; system responses switched to camelCase too (one contract style for the generated TS client).

## Decisions
_None yet._

## Known issues
- The SPA's types (apps/web/src/api/types.ts) still describe the mockup shapes (e.g. `week`, `winProb`,
  required notes/deadlines); WEB-002..004 / APP-003 move them to this contract.
- Actions carry no deadline or confidence yet (no calibrated source); per-category notes are null.

## Follow-ups
- APP-007: players, recommendations, trades and evaluation endpoints.
