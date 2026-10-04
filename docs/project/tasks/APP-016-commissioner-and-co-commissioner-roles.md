---
id: APP-016
title: "Commissioner and co-commissioner roles, transfer, and the permission matrix"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-023, APP-027]
areas: [apps/api/src/fantasy_api/leagues/**, apps/api/tests/test_roles*.py, apps/api/tests/test_league_permissions.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-016 — League roles

## Objective
The creator is the commissioner by default; they appoint co-commissioners; commissioners can change league settings.
This task completes the `can()` matrix for every league route and adds role changes and the transfer of the
commissioner role. Power can never be taken from the commissioner by a co-commissioner, and a league always has
exactly one commissioner. Spec: `docs/specification/leagues-and-accounts.md` §3.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §2, §3
- APP-014/015 league service, `can()` and the test that walks the routes

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Commissioner | "I make my friend a co-commissioner" | `PUT /leagues/{id}/members/{teamId}/role {role}`; max 3; only on a current manager; appears in the activity log |
| Commissioner | "I take it back" | demote to manager; the demoted person keeps their team |
| Commissioner leaving | "someone else runs it" | `POST /leagues/{id}:transfer {teamId}` to a co-commissioner only; the old commissioner becomes a co-commissioner; the new commissioner leaves that group, so the count never rises, and the check runs before any write |
| Co-commissioner overreach | "can't seize the league" | tries appoint, demote, transfer, delete, remove another co-commissioner: all 403 `forbidden-role` |
| Race | no zero- or two-commissioner league | transfer and role change run in one transaction that reads the current roles; the invariant "exactly one commissioner" is asserted after every write |
| The commissioner's account is deleted | "league survives" | handled by APP-025: deletion is refused (409) while the league has other members until a transfer or delete |
| Removed or blocked co-commissioner | consistent | role removed with the team; cannot rejoin as anything but via a fresh join |
| Self-targeting | no loopholes | cannot change one's own role; transfer to self is 422 |

## Acceptance criteria
- [ ] AC1: role changes (appoint, demote) work per the matrix, cap co-commissioners at 3, are idempotent, and write an
      activity entry.
      Verify: `uv run pytest -q apps/api/tests/test_roles.py -k "appoint or demote or cap"`
- [ ] AC2: `:transfer` moves the commissioner role to a co-commissioner atomically and the old commissioner becomes a
      co-commissioner (the count is unchanged); a league never has 0 or 2 commissioners
      (property test over random operation sequences).
      Verify: `uv run pytest -q apps/api/tests/test_roles.py -k "transfer or invariant"`
- [ ] AC3: the permission matrix in the spec is a data table in the code, and a test generates one assertion per
      (role × action) cell and fails if a cell in the spec file and in the code differ.
      Verify: `uv run pytest -q apps/api/tests/test_league_permissions.py -k "matrix"` (parses §3 of the spec)
- [ ] AC4: co-commissioners can edit settings, invites, requests and manager removal, and cannot do any
      commissioner-only action; every denial is 403 `forbidden-role` with no side effect.
      Verify: `uv run pytest -q apps/api/tests/test_roles.py -k "cocommissioner"`
- [ ] AC5: settings changes by a co-commissioner appear in the activity log with their `teamId` and a diff summary
      (field names, not values for text fields).
      Verify: `uv run pytest -q apps/api/tests/test_roles.py -k "log"`
- [ ] AC6: `:transfer` is in the step-up table (APP-027), so a stale sign-in gets 401 `reauth-required` with no change.
      Verify: `uv run pytest -q apps/api/tests/test_roles.py -k "stepup"`
- [ ] AC7: client regenerated with no diff.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Matrix-driven tests, property test for the commissioner invariant, concurrency test (two simultaneous transfers: one
wins).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- The spec's matrix is parsed by a test so the document and the code cannot drift apart (no duplicated source of truth).

## Known issues
_None._

## Follow-ups
_None._
