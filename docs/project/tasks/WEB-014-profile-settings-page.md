---
id: WEB-014
title: "Profile and settings page (avatar menu → Settings)"
epic: EP-70 Dashboard
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-25
depends_on: [APP-009]
areas: [apps/web/**]
standards: [frontend]
assignee:
created: 2026-10-02
completed:
---
# WEB-014 — Profile and settings page

## Objective
A Settings screen, reached from the user's avatar (top right), where each user sees who they're signed in as and
edits their settings (D-64), replacing the "Signed in as … · Sign out" footer.

## Context to read (only these)
- APP-009's API contract (`apps/api/openapi.json`)
- `apps/web/src/auth/auth.tsx`, `apps/web/src/App.tsx` (Shell)

## User stories and edge cases
| Persona | Story | Edge cases |
|---|---|---|
| Owner, phone | "Change my brief time and theme" | saving shows progress and success; validation errors appear next to the field; theme applies instantly and persists |
| Two tabs | Saves in one, then the other | 412 → "These settings changed elsewhere" with Reload, never a silent overwrite |
| Member | "Link Telegram" | shows the code and a deep link to the bot, polls until linked, handles expiry with "Get a new code" |
| Any | Leaves with unsaved changes | an "Unsaved changes" prompt in-page (no `window.confirm`) |
| Any | Delete account | a typed confirmation ("delete"), then sign-out; the last owner sees why they can't |
| Demo visitor | Opens Settings in sample mode | a read-only sample profile marked "Sample data"; no network calls |
| Offline / API down | Opens Settings | the error state with Retry; the form isn't shown half-loaded |

## Acceptance criteria
- [ ] AC1: the avatar menu (Google photo or initials) opens Settings and Sign out; keyboard and screen-reader accessible.
      Verify: `apps/web/src/features/settings/SettingsPage.test.tsx::avatar menu`
- [ ] AC2: the form loads `/me/settings`, edits each field with inline validation, and saves with `If-Match`;
      success and 422 field errors are shown.
      Verify: SettingsPage tests (load, edit + save, 422 per field)
- [ ] AC3: 412 shows the conflict message and Reload restores server values.
      Verify: SettingsPage test (412)
- [ ] AC4: Telegram linking flow incl. expiry; delete account with typed confirmation; unsaved-changes guard.
      Verify: SettingsPage tests (one per flow)
- [ ] AC5: sample mode shows a read-only sample profile with no network calls.
      Verify: SettingsPage test (fixture client, fetch spy not called)

## Test requirements
Vitest + Testing Library with a fake `ApiClient`; persona coverage in WEB-008's e2e.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-02 — Specified; waits on G-25 and APP-009.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
