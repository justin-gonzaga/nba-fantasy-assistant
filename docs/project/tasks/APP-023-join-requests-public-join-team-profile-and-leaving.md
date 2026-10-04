---
id: APP-023
title: "Join requests, public joining, team name and picture, leave, remove and block"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-015, APP-013, APP-022, APP-024, APP-026]
areas: [apps/api/src/fantasy_api/leagues/requests*.py, apps/api/src/fantasy_api/leagues/teams*.py, apps/api/src/fantasy_api/leagues/members*.py, apps/api/tests/test_membership*.py, apps/api/tests/test_teams.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-023 — Requests, public joining, teams, leaving

## Objective
Everything about membership that is not the invite link: joining a public league (open or by approval), the
commissioner's decision on requests, a manager's team name and picture, leaving, and removal and blocking. Spec:
`docs/specification/leagues-and-accounts.md` §3, §5, §6, §8.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §3, §5, §6, §8
- APP-014 `can()`, APP-015 join service and team-name generator, APP-013 media service

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Visitor in the Leagues panel | "join in one click" | `POST /leagues/{id}/join` for `public` + `open`; for `approval` it files a request (one pending per person, at most 50 per league, message up to 140 characters) |
| Commissioner handles requests | "accept or decline" | accept creates the team (re-checks capacity in the transaction); decline allows a new request after 24 h; either clears the pending request |
| Manager renames the team | "change name and picture" | name 2-30, `is_blocked`, unique within the league (case-insensitive), `If-Match` on the team; picture via APP-013; commissioners can reset the name to the default |
| Leaving | "I am out" | a manager leaves and the team is deleted; a commissioner must transfer or delete first (409 `transfer-or-delete`) |
| Removal | "remove and block" | commissioners can remove or block managers; only the commissioner can remove a co-commissioner; blocked accounts cannot join by link, list or request |
| Blocked person | no oracle | the answer is 403 `blocked` with no hint of who blocked; `POST .../members/{teamId}:unblock` (commissioners) removes the block record and restores nothing else; the person may then join normally |
| Many leagues | "bounded" | an account can be in at most 20 leagues (409 `membership-limit`); requests per person per hour are a row in APP-024's table |
| Last slot race | one winner | accept and public join both use the same capacity transaction as APP-015 |

## Acceptance criteria
- [ ] AC1: public open join and approval requests: one pending per person, at most 50 per league, the 24 h re-request
      rule; accept re-checks capacity; decline and accept clear the request.
      Verify: `uv run pytest -q apps/api/tests/test_membership.py -k "request or public_join"`
- [ ] AC2: public join, accept and link join share one capacity transaction function (one definition); 30 concurrent
      mixed joins on a 10-slot league create exactly 10 teams.
      Verify: `uv run pytest -q apps/api/tests/test_membership.py -k "concurrent"`; `grep -rn "def claim_slot" apps` finds one
- [ ] AC3: team rename and picture use APP-013 and If-Match; names are unique per league (case-insensitive) and pass
      `is_blocked`; commissioners can reset to the default.
      Verify: `uv run pytest -q apps/api/tests/test_teams.py`
- [ ] AC4: leave, remove and block follow the permission table; a commissioner cannot leave with other members; a
      blocked account cannot rejoin by any route until unblocked.
      Verify: `uv run pytest -q apps/api/tests/test_membership.py -k "leave or remove or block"`
- [ ] AC5: `:unblock` removes the block record, is a commissioner action, and the person can join afterwards; the
      20-memberships limit returns 409 `membership-limit`.
      Verify: `uv run pytest -q apps/api/tests/test_membership.py -k "unblock or membership_limit"`
- [ ] AC6: requests, blocks, members and team documents are registered in `USER_DATA_OWNERS` (APP-026) with export and
      anonymise functions.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "membership"`
- [ ] AC7: every new route declares its `can()` action; logs and the activity log contain no email or uid; the client
      is regenerated with no diff.
      Verify: `uv run pytest -q apps/api/tests/test_league_permissions.py`; `just api-client` twice, no diff

## Test requirements
Store contract tests on both backends; concurrency tests on the emulator; negative authorisation per route.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original APP-015).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- APP-016 builds the co-commissioner roles and transfer on top of this.
