---
id: APP-026
title: "User-data registry (USER_DATA_OWNERS) and its coverage test"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: S
autonomy: review
gate: G-35
depends_on: [APP-008]
areas: [apps/api/src/fantasy_api/lifecycle/registry*.py, apps/api/tests/test_lifecycle_registry.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-026 — The one registry of user data

## Objective
Nothing that holds personal data may be forgotten by export or deletion. This task adds the single registry
`USER_DATA_OWNERS`: each entry names a store (a Firestore collection or a bucket prefix), the field that links it to an
account, its category, its retention, and the function that exports it and the function that deletes or anonymises it. It
also adds the coverage test that fails when a new collection or prefix is not registered. It builds only the registry and
the test; **every task that creates user data registers its own entry** (APP-012 usernames, APP-013 avatars, APP-014
leagues, teams and members, APP-015 invites, APP-017 reports, APP-020 security events, APP-021 consents and the profile,
APP-023 requests, blocks and memberships). The export is APP-019 and the deletion cascade is APP-025; both read this
registry and nothing else.

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (User rights, Change control)
- `apps/api/src/fantasy_api/users/*` and the store module that defines the collection names

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Developer adds a collection | "cannot forget" | a new collection constant or bucket prefix with no registry entry fails the test, naming the file |
| Developer registers an entry | "one obvious way" | an entry is a small typed record; a missing export or delete function is an import-time error |
| Shared data | "not mine alone" | an entry can declare `anonymise` instead of `delete` (for example the activity log's `actorTeamId`) |
| Backend swap | "same on both stores" | the test runs on the in-memory and the Firestore-emulator definitions |

## Acceptance criteria
- [ ] AC1: `USER_DATA_OWNERS` and the `register()` helper exist; an entry without an export function and a delete or
      anonymise function is rejected at import time.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "entry"`
- [ ] AC2: the coverage test walks every collection and bucket-prefix definition in `apps/api` and fails when one is not
      registered or explicitly marked `not_user_data` with a reason.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "coverage"`
- [ ] AC3: the existing `users` collection is registered here (the first entry), proving the pattern.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "users"`

## Test requirements
Pure unit tests; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split out of APP-019 so the registry exists before the tasks that must register with it).

## Decisions
- The registry is one module owned by this task; registering is the duty of whichever task introduces the data.

## Known issues
_None._

## Follow-ups
_None._
