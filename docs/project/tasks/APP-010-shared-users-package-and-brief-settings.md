---
id: APP-010
title: "Shared users package; the daily brief follows each user's settings"
epic: EP-70 Dashboard
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: auto
gate: G-30
depends_on: [APP-009]
areas: [packages/**, apps/api/**, apps/pipeline/**, pyproject.toml, uv.lock]
standards: [testing, architecture]
assignee:
created: 2026-10-03
completed:
---
# APP-010 — Shared users package; the brief follows user settings

## Objective
G-30 (A): the daily job must read each user's settings (recipient chat, quiet hours, alert types), which live in the
users store. Apps can't import each other, so move the `UserStore` port, its in-memory and Firestore adapters and
the user/settings model from `apps/api` into a package both apps use; then the daily brief sends each alert only
to users who want it, inside their awake window. Split from APP-009 (its old AC5).

## Context to read (only these)
- D-64, D-68; `apps/api/src/fantasy_api/users/`; `apps/pipeline/src/fantasy_pipeline/daily_brief.py`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner muted injury alerts | no injury alert is sent; the brief still is | brief disabled → nothing is sent |
| Owner's awake window 07:00–22:00 (their time zone) | the brief waits until 07:00 local | a window crossing midnight; DST changes |
| A user with no linked chat | skipped, logged | — |
| Store unavailable | the owner gets the brief from `.env` as today (fallback), and the failure is logged | never a silent skip |

## Acceptance criteria
- [ ] AC1: the users code lives in a package (`packages/users` or `fantasy_core.users`); the API imports it; behaviour
      is unchanged (APP-008/009 tests pass unmodified apart from imports); import-linter enforces the layering.
      Verify: `just check` (import-linter) + `apps/api/tests/test_users*.py`, `test_settings.py`
- [ ] AC2: the daily brief reads recipients, awake window and alert types from the store, falling back to `.env`
      for the owner when the store is unavailable, so a muted alert isn't sent.
      Verify: `apps/pipeline/tests/test_daily_brief.py::test_respects_user_settings`, `::test_store_down_falls_back`

## Test requirements
In-memory store; frozen clock (awake windows, DST); no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-03 — Split from APP-009 after G-30 (A, A).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
