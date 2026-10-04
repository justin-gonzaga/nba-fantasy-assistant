---
id: DATA-039
title: "NBA data provider interface and a data-licence setting"
epic: EP-20 Ingestion
phase: 7
component: pipeline
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: []
areas: [packages/core/src/fantasy_core/settings.py, packages/core/tests/**, packages/ingest/src/fantasy_ingest/**, packages/ingest/tests/**, apps/api/src/fantasy_api/**, apps/api/tests/**, apps/api/openapi.json, docs/runbooks/data-licence.md]
standards: [software-engineering, data-engineering, testing]
assignee:
created: 2026-10-04
completed:
---
# DATA-039 — Swap the data source without touching the product

## Objective
The product runs today on free, unofficial NBA sources (personal use only). The owner will build and use it personally,
then repoint to a licensed provider later, without paying now (owner direction 2026-10-04; research note
`docs/research/player-images-and-data-licensing.md`). This task makes that a configuration change: one
`DataProvider` interface that the existing NBA.com adapters implement, and one `DATA_LICENSE` setting
(`personal` default, `commercial`) that the API exposes so the app can behave correctly. It does not choose or buy a provider.

## Context to read (only these)
- `docs/research/player-images-and-data-licensing.md`; `docs/architecture/adr/0009-nba-data-sources.md`
- `packages/ingest/src/fantasy_ingest/nba_cdn.py`, `packages/core/src/fantasy_core/settings.py`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner using it personally | "nothing changes for me" | default `personal`; existing ingest output is byte-identical |
| Owner later switching provider | "one new adapter, one setting" | an adapter must return the same staging rows; a contract test fails if a field is missing |
| API client (web) | "should I show headshots?" | the public config exposes `dataLicense` and `features.playerImages`; an unknown value fails closed (`personal`) |
| Misconfiguration | "set to commercial by accident" | `commercial` needs a `DATA_PROVIDER` other than `nba_free`, else startup fails with a clear message |

## Acceptance criteria
- [ ] AC1: a `DataProvider` protocol (schedule, box scores, game logs, rosters) with the current NBA.com code behind
      `NbaFreeProvider`; no caller imports the NBA.com modules directly any more.
      Verify: `uv run pytest -q packages/ingest/tests`; `uv run lint-imports` passes
- [ ] AC2: `DATA_LICENSE` and `DATA_PROVIDER` settings; `commercial` with `nba_free` fails at startup; an unknown value
      is treated as `personal`.
      Verify: `uv run pytest -q packages/core/tests -k data_license`
- [ ] AC3: a provider contract test (shared fixtures) that any adapter must pass, run against `NbaFreeProvider`.
      Verify: `uv run pytest -q packages/ingest/tests -k provider_contract`
- [ ] AC4: the public config route returns `dataLicense` and `features.playerImages` (true only for `personal` AND an
      owner-authenticated caller or a local build); the OpenAPI file and generated client are updated.
      Verify: `uv run pytest -q apps/api/tests -k data_license`; `just api-client` then `git diff --exit-code apps/api/openapi.json`
- [ ] AC5: a runbook says how to add a provider and what must be true before `commercial` (licence read, images policy).
      Verify: `docs/runbooks/data-licence.md` exists and is linked from `docs/runbooks/README.md`

## Test requirements
Contract tests with recorded fixtures; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Created from the owner's decision to build on free data first and license later.

## Decisions
- No provider is chosen here (the G-35 menu does that, with real quotes).

## Known issues
_None._

## Follow-ups
- Provider choice and quotes (G-35). Wikimedia Commons images are an optional later task.
