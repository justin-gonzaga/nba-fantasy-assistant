---
id: WEB-036
title: "Account security settings: providers, second factor, sessions, export and delete"
epic: EP-76 Identity and data protection
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-018, APP-027, APP-019, APP-025, WEB-030, WEB-031]
areas: [apps/web/src/settings/security/**, apps/web/e2e/security-settings*.spec.ts]
standards: [frontend, design-language, security, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-036 — Security and data settings

## Objective
One settings section where a person manages how they sign in and what is kept: linked providers, a second factor,
signing out everywhere, downloading their data and deleting the account. It sits beside the profile page (WEB-031) and
uses the API behaviour from APP-018, APP-027, APP-019 and APP-025. Rules: `docs/standards/user-data-and-auth.md`.

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Sessions, User rights)
- APP-018, APP-027, APP-019, APP-025 response shapes; WEB-031 settings layout

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member | "which sign-in methods do I have?" | list of linked providers with a masked email or phone; link a new one after re-sign-in; cannot unlink the last method |
| Member | "add a second factor" | TOTP enrolment with QR and manual key and a code check; there are no recovery codes (Firebase has none), so the screen says plainly that a lost device is recovered by contacting the owner after an email check; SMS is offered only if enabled |
| Member | "sign out everywhere" | one button with confirmation; the current device is signed out too |
| Member | "download my data" | requests the export, shows progress and the 24 h link; one a day message |
| Member | "delete my account" | a clear list of what goes and what is kept; typed username; re-sign-in; the 14-day cancel note; commissioner leagues listed as blockers |
| Owner | "admin needs MFA" | a banner until a second factor is enrolled |
| Keyboard / zoom / screen reader | usable | QR has a text alternative; 320 px; axe clean |

## Acceptance criteria
- [ ] AC1: linked providers list, link flow after re-sign-in, and the last-method guard.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "security-providers"` (Auth emulator)
- [ ] AC2: TOTP enrolment, the no-recovery-codes notice, and the owner banner.
      Verify: `test:e2e --grep "security-mfa"`
- [ ] AC3: sign out everywhere calls the revoke endpoint and returns to the sign-in page; the old token is refused.
      Verify: `test:e2e --grep "security-sessions"`
- [ ] AC4: export request and download link; delete flow with typed confirmation, grace-period note and commissioner
      blockers.
      Verify: `test:e2e --grep "security-data"`
- [ ] AC5: axe clean at 320 px and 1280 px; keyboard-only path through enrolment works; no secret (the TOTP seed)
      is written to storage or logs.
      Verify: `test:e2e --grep "a11y|keyboard|no-leak"` extended

## Test requirements
Playwright against the Auth emulator and API stub; component tests for the enrolment view.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
