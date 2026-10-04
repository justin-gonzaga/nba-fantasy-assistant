---
id: WEB-037
title: "Onboarding screen (username, picture, consent) and terms and privacy pages"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [WEB-030, APP-012, APP-013, APP-021]
areas: [apps/web/src/onboarding/**, apps/web/src/legal/**, apps/web/e2e/onboarding*.spec.ts, apps/web/e2e/legal*.spec.ts]
standards: [frontend, design-language, security, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-037 — Onboarding and legal pages

## Objective
After a verified sign-in, a new person picks a username, optionally a picture, confirms they are 13 or older and
accepts the terms and privacy notice, then lands where they were going (a league invite is preserved). The terms,
privacy and "no non-essential cookies" pages are rendered from the text the owner approves in SEC-003. Spec:
`docs/specification/leagues-and-accounts.md` §6; rules in `docs/standards/user-data-and-auth.md` (consent, minimisation).

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5, §6
- APP-012, APP-013 and APP-021 response shapes; `docs/standards/frontend.md`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| New user | "pick a name" | live availability (debounced, rate-limit aware), suggested names, reserved and blocklist messages in plain words, 3-20 characters shown as a counter |
| New user | "add a picture" | optional; preview before upload; failure leaves initials; size and type errors explained |
| New user | "agree" | terms and 16+ checkboxes unticked by default; links open in a new tab; no birthdate field |
| Arrived from an invite | "do not lose the link" | the `/join#<token>` fragment is kept (in memory or session storage, never sent to a server) through sign-up and onboarding and resumed |
| Terms version changes | "re-accept" | `consentRequired` from `/me` shows a blocking accept screen; declining signs out |
| Reload mid-way | "do not lose progress" | the draft username is kept in memory only; nothing sensitive in storage |
| Sign-up closed or onboarding refused | clear | `signup-closed` and `onboarding-required` map to explained screens |
| Keyboard / zoom / screen reader | usable | focus order, announced errors, 320 px, 200 % zoom |

## Acceptance criteria
- [ ] AC1: onboarding collects username (live availability), optional picture, terms and age confirmations, posts
      `/me/onboarding`, then continues to the page the user came from.
      Verify: `test:e2e --grep onboarding` including a run that starts at `/join#<token>`
- [ ] AC2: re-acceptance screen appears when `consentRequired` is true and blocks the app until accepted.
      Verify: `test:e2e --grep consent-required`
- [ ] AC3: terms, privacy and cookie statement pages exist from the SEC-003-approved text and are linked from sign-up,
      onboarding and the footer; `document.cookie` is empty before sign-in and no third-party tracker loads.
      Verify: `test:e2e --grep legal`
- [ ] AC4: axe finds no serious violation at 320 px and 1280 px and onboarding is completable by keyboard only.
      Verify: `test:e2e --grep "a11y|keyboard"` extended
- [ ] AC5: no username, picture data or consent detail is written to storage, URLs or console.
      Verify: `test:e2e --grep "no-leak"` extended

## Test requirements
Playwright against the API stub and the Auth emulator; component tests for the availability field.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original WEB-030).

## Decisions
_None yet._

## Known issues
- Legal text is a placeholder until the owner approves SEC-003; the pages must show a "draft" banner until then.

## Follow-ups
_None._
