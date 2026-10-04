---
id: WEB-015
title: "Owner admin: invite, list and remove members"
epic: EP-70 Dashboard
phase: 7
component: web
status: todo
ready: true
size: S
autonomy: auto
gate: G-25
depends_on: [APP-008, WEB-014]
areas: [apps/web/**]
standards: [frontend]
assignee:
created: 2026-10-02
completed:
---
# WEB-015 — Owner admin: members and invites

## Objective
In Settings, the owner sees a Members section: invite by email, see pending invites (with expiry), revoke them, and
remove members (APP-008). Members don't see it.

## Context to read (only these)
- APP-008's endpoints in `apps/api/openapi.json`; WEB-014's Settings page

## User stories and edge cases
| Persona | Story | Edge cases |
|---|---|---|
| Owner | "Invite my friend" | invalid email inline; a duplicate shows the existing invite; an existing member → message from the 409 |
| Owner | "Remove someone" | in-page confirmation; the list updates; removing yourself as the last owner is disabled with the reason |
| Member | Opens Settings | no Members section; direct calls are 403 (API-enforced, not just hidden) |

## Acceptance criteria
- [ ] AC1: owners see Members with members and pending invites (email, role, invited/expires dates); members don't.
      Verify: `MembersSection.test.tsx` (owner vs member rendering)
- [ ] AC2: invite, revoke and remove work with inline validation, 409 messages, and an in-page confirmation for removal.
      Verify: `MembersSection.test.tsx` (one test per action and error)

## Test requirements
Vitest with a fake `ApiClient`.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-02 — Specified; waits on G-25.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
