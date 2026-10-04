---
id: APP-011
title: "Per-user draft settings and presets in the API (versioned, validated)"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [APP-009]
areas: [apps/api/**, packages/core/**]
standards: [backend, testing, security]
assignee: claude
created: 2026-10-04
completed: 2026-10-04
---
# APP-011 — Draft settings and presets (API)

## Objective
Give each signed-in user a saved set of draft presets (league shape, room behaviour, strategy, sound and motion) that
follows them across devices (DRAFT-017 builds the page). It is a **separate document** from `/me/settings`: that one is
read by the daily job (APP-010) field by field and should stay small; presets are larger, edited as a whole, and read
only by the web app.

## Context to read (only these)
- `apps/api/src/fantasy_api/users/settings*.py` (the ETag / compare-and-set / `mutate` pattern), `users/store.py`,
  `users/firestore.py` (the store contract), `errors.py`
- `packages/core/src/fantasy_core/league.py` (`ScoringFormat`, `LeagueRules`)

## The document (schema v1)
```
DraftSettings {
  version: int            # server-assigned, drives the ETag "draft-v<n>"
  activeId: string | null # the preset the setup page starts with; null = the built-in default
  presets: Preset[]       # 0..10, unique ids, unique names (case-insensitive)
  fx: { sound: bool, volume: 0..1, tick: 'off'|'last10'|'every', motion: 'auto'|'reduced' }
}
Preset {
  id: string (1..40, [A-Za-z0-9_-]), name: string (1..40), updatedAt: ISO-8601 UTC
  league: { scoring: ScoringFormat, drafting: 'auction'|'snake', teams: 4..20, budget: 50..1000 | null,
            spots: 5..25, seat: 1..teams,           # budget null for snake; seat is used by snake only
            categories?: string[],                   # category formats: a subset of the supported stats (default 9-cat)
            weights?: { [stat]: -20..20 } }          # points formats: at least one non-zero weight
  room:   { pace: 'real'|'fast'|'untimed'|'custom', nominateSeconds: 5..120, bidSeconds: 5..120,
            styles: 'mix'|'balanced'|'stars'|'punter'|'value' }
  strategy: { punt: null | one of the league's category codes }
  season: 'current' | '<yyyy-yy>'
}
```
**Supported combinations are a server constant**, not a schema shape: today `scoring = h2h_categories` and
`drafting = auction`. DRAFT-019 adds the other scoring formats and DRAFT-021 adds `snake` by extending that constant
(and nothing else; `categories` and `weights` are already in schema v1, validated now, and rejected as
`unsupported-format` where the combination is not yet supported, e.g. `weights` with `h2h_categories`). A well-formed but not-yet-supported combination returns 422 `unsupported-format` naming the field.

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner on phone then laptop | "my presets are on both" | `GET` returns the doc and an ETag; `PUT` needs `If-Match`; stale → 412 with `current`; none → 428 |
| Brand-new user | "nothing saved yet" | `GET` returns the empty doc (`version` 0, no presets) with defaults, no 404 |
| Two tabs edit | no silent overwrite | CAS on the version, as `/me/settings` |
| 11th preset, duplicate name, bad id, teams = 3, spots = 30, seat > teams | clear errors | 422 problems with the offending field path (`presets[2].league.teams`) |
| A huge or hostile body | safe | body ≤ 16 KB (413); unknown keys rejected (422); strings are plain text, never rendered as HTML by the API |
| Another user's data | private | uid comes from the token only; there is no path with a uid |
| Account deletion / export | complete | `DELETE /me` removes the doc in the same transaction; `GET /me/export` includes it |
| Signed-out | n/a | 401 as every `/me/*` |

## Acceptance criteria
- [x] AC1: `GET /me/draft-settings` returns the document and `ETag: "draft-v<n>"` (empty defaults for a new user);
      `PUT` replaces it with `If-Match`; 412 (with `current`) when stale; 428 when missing.
      Verify: `uv run pytest -q apps/api/tests/test_draft_settings.py -k "get or put or etag or stale or missing"`
- [x] AC2: validation covers every range above, uniqueness of ids and names, the 10-preset and 16 KB limits, unknown
      keys, and `unsupported-format`, each with the field path in the problem.
      Verify: `uv run pytest -q apps/api/tests/test_draft_settings.py -k "validation or limits or unsupported"` (table
      driven, one row per rule)
- [x] AC3: the same behaviour on the in-memory and Firestore stores (contract tests; the emulator ones run on CI);
      the write is a single atomic compare-and-set.
      Verify: `uv run pytest -q apps/api/tests/test_users_store.py -k draft` (memory) and the CI emulator job
- [x] AC4: account delete removes the document in the same transaction, and export includes it; another user's
      request never sees it.
      Verify: `uv run pytest -q apps/api/tests/test_draft_settings.py -k "delete or export or isolation"`
- [x] AC5: OpenAPI and the generated TypeScript types are refreshed and the CI diff check passes; the new schema names
      appear camelCase.
      Verify: `just api-client` produces no diff on a second run; `apps/web/src/api/schema.gen.ts` contains
      `DraftSettings`
- [x] AC6: the supported-combinations constant is the only place the format gate lives: a test adds a fake supported
      combination and the API accepts it without any other change.
      Verify: `uv run pytest -q apps/api/tests/test_draft_settings.py -k "supported_constant"`

## Test requirements
Table-driven validation tests; store contract tests shared by both backends; the problem bodies asserted. No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `test_draft_settings.py` -k "get or put or etag or stale or missing": empty defaults, whole-doc PUT, ETag follows the version, 412 with `current`, 428, bad JSON, 401, GET body round-trips into PUT | 13 passed |
| AC2 | unit | `test_draft_settings.py` -k "validation or limits or unsupported": 49-row table (every range, uniqueness, unknown keys, field paths), 10 vs 11 presets, 413 declared and streamed, unsupported-format rows | 60 passed |
| AC3 | contract | `test_users_store.py` -k draft: compare-and-set and removal with the user, on both backends (the Firestore variants skip locally, run in the CI emulator job) | 2 passed, 2 skipped (emulator) |
| AC4 | unit | `test_draft_settings.py` -k "delete or export or isolation" | 3 passed |
| AC5 | build | `just api-client` twice, no diff on the second run; `schema.gen.ts` has `DraftSettings`, `DraftPreset`, camelCase fields; `test_openapi.py` matches | pass |
| AC6 | unit | `test_draft_settings.py` -k supported_constant: a fake (h2h_points, snake) pair is accepted by editing only `SUPPORTED_COMBINATIONS`; other rules still hold | 1 passed |

## Implementation history
- 2026-10-04 — Specified from the owner's request for a saved draft settings page.
- 2026-10-04 — Built: `users/draft_settings.py` (document, validation by field path, `SUPPORTED_COMBINATIONS`),
  `draft_settings_routes.py` (GET/PUT, 16 KB capped body read, hand-validated so problems carry paths),
  `UserStore.get_draft_settings` / `save_draft_settings_if` on both stores (Firestore `draft_settings/{uid}`, JSON text),
  deletion in the same transaction as the user, `draftSettings` in `/me/export`. `just check`: 735 passed, 12 skipped.

## Decisions
- PUT accepts the `version` key (ignored; `If-Match` decides) and `null` for `categories`/`weights`, so the web app can
  send back exactly what GET returned.
- A separate resource over extra fields on `/me/settings`: different size, different readers, whole-document edit.
- Whole-document `PUT` with one version: presets are edited together on one page; merging is the web app's job
  (DRAFT-017, operation replay on a 412), not the server's.

## Known issues
- The Firestore contract variants only run in CI (emulator).

## Follow-ups
- DRAFT-019 / DRAFT-021 extend the supported combinations.
