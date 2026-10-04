---
id: WEB-038
title: "Commissioner tools: members and roles, invites, requests, transfer and delete"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-016, WEB-034]
areas: [apps/web/src/leagues/manage/**, apps/web/e2e/league-admin*.spec.ts]
standards: [frontend, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-038 — Commissioner tools

## Objective
The management tabs of a league for commissioners and co-commissioners: Members and roles, Invites, Requests and the
danger zone (transfer, delete). Everything shown is gated by the API's `viewer.permissions` (WEB-034 supplies the
helper). Spec: `docs/specification/leagues-and-accounts.md` §3, §6.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §3, §6
- APP-015, APP-016 and APP-023 response shapes; the permission helper from WEB-034

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Commissioner | "manage people" | members list with role badges; appoint or demote a co-commissioner; remove or block with a confirm that names the person; reset a team name or picture to the default |
| Co-commissioner | "limited tools" | only the actions the API allows are shown |
| Commissioner | "invites" | create a link with lifetime and max uses; the full URL is shown once with Copy and Share; the list shows label, expiry and uses; revoke |
| Commissioner | "requests" | pending list with message; accept or decline; badge count on the tab; a full league explains why accept fails |
| Commissioner | "hand over or close" | Transfer to a co-commissioner with typed confirmation; Delete by typing the league name; leaving is blocked with an explanation |
| Step-up needed | "ask me again" | a 401 `reauth-required` opens the re-sign-in dialog and then retries once |
| Phone / keyboard / zoom | usable | tools under a segmented control; destructive actions need a deliberate second step; 320 px, axe clean |

## Acceptance criteria
- [ ] AC1: Members: appoint, demote, remove, block, unblock and reset, each with a named confirmation; co-commissioners see only
      their allowed actions.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "league-members"`
- [ ] AC2: Invites: create (lifetime, max uses), copy and share, shown once, revoke; Requests: accept or decline with
      the count badge.
      Verify: `test:e2e --grep "league-invites|league-requests"`
- [ ] AC3: Delete requires the typed name, Archive and Unarchive are one click with a note that an archived league is
      read-only, Transfer requires a co-commissioner, and Leave is blocked with the reason for a commissioner; a `reauth-required` response triggers the re-sign-in dialog and one retry.
      Verify: `test:e2e --grep "league-danger"`
- [ ] AC4: 320/768/1280 px layouts, axe clean, keyboard-only path (create a link, remove a member) works.
      Verify: `test:e2e --grep "a11y|keyboard|phone"` extended

## Test requirements
Fixture leagues for each role; Playwright with the API stubbed.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original WEB-034).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
