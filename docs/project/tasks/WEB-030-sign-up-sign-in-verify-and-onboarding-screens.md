---
id: WEB-030
title: "Sign-up and sign-in screens (Google, email, phone) with verification"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-021, APP-018, WEB-013]
areas: [apps/web/src/auth/**, apps/web/e2e/signup*.spec.ts, apps/web/firebase.json, tools/tests/test_hosting_headers.py]
standards: [frontend, design-language, security, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-030 — Sign-up and sign-in

## Objective
Replace the single "Sign in with Google" button with the full account entry: choose a method, verify it (email link or
code, SMS code), and arrive signed in. The methods shown come from the API (`GET /auth/config`, APP-018), so turning a
method on or off, or closing sign-up, needs no web deploy. Picking a username and accepting the terms is onboarding
(WEB-037). The screens follow `docs/standards/user-data-and-auth.md` (error wording that does not reveal whether an
account exists; no secrets in URLs; code-entry accessibility) and `docs/standards/design-language.md`.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §6 (sign up, join by link)
- `docs/standards/user-data-and-auth.md` (Authentication, Account recovery, Phone/SMS), `docs/standards/frontend.md`
- `apps/web/src/auth/*` (WEB-013), `apps/web/src/api/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| New user on a phone | "I sign up with Google in two taps" | popup blocked: redirect flow; cancelled popup: neutral message, no error banner; return to the page they came from (including a `/join/<token>` link) |
| New user with email | "I make an account with email and password" | policy from `/auth/config` shown live (minimum length, paste allowed, show/hide); a password found in the common list is refused with a reason; verification email sent; resend with a cool-down; wrong inbox: change email |
| Passwordless | "email me a link" | link opened on another device asks for the email again; expired link: a page to request a new one |
| Phone sign-up | "text me a code" | country picker with only allowed regions; 6 digit input with `autocomplete="one-time-code"` and paste-all; resend after 60 s with the counter shown; wrong code shows attempts left, locked message at the limit; reCAPTCHA / App Check failure is a friendly message; the number is masked after entry |
| Returning user | "sign in" | the same wording for an unknown account and a wrong password ("check your details"); never says whether an email exists; throttle message is generic |
| Same email, other method | "I used Google before" | the linking prompt requires signing in with the existing method; never silently merges |
| Sign-up closed | "not yet" | `signupOpen: false` shows the invite-only message; invited users still proceed; no email collection |
| Keyboard / screen reader | works without a mouse | focus order, labelled inputs, errors announced (`aria-live`), code input usable with a screen reader |
| Phone width and 200 % zoom | no clipping | forms fit at 320 px; the on-screen keyboard does not hide the submit button |
| API down | graceful | `GET /auth/config` fails: show Google only plus a retry, never a blank page |
| Privacy | nothing leaks | no email, phone or code in the URL, console, analytics or error reports; correct autofill attributes |

## Acceptance criteria
- [ ] AC1: the sign-in page renders exactly the methods returned by `/auth/config`, in a fixed order, and a failed
      config call falls back to Google with a retry; there is no second list of methods in the web app.
      Verify: `corepack pnpm@10 --dir apps/web test src/auth` (unit) and `test:e2e --grep signup-methods`
- [ ] AC2: email and password sign-up: policy shown live, short or common passwords rejected, the verification step
      blocks the app until verified, resend has a cool-down.
      Verify: `test:e2e --grep signup-email` (Firebase Auth emulator)
- [ ] AC3: phone sign-up: code entry meets the accessibility rules (`one-time-code`, paste-all, announced errors),
      resend timer, attempt-limit message, masked number afterwards.
      Verify: `test:e2e --grep signup-phone` (emulator) and the axe check in AC6
- [ ] AC4: error wording never distinguishes unknown from wrong credentials, and no screen reveals whether an email or
      phone is registered.
      Verify: `corepack pnpm@10 --dir apps/web test src/auth -t "no enumeration"`
- [ ] AC5: closed sign-up (`signupOpen: false`) shows the closed message and still lets invited users in.
      Verify: `test:e2e --grep signup-closed`
- [ ] AC6: axe finds no serious violation on any of the new screens at 320 px and 1280 px; keyboard-only completion of
      email sign-up is tested.
      Verify: `test:e2e --grep "a11y|keyboard"` extended with the new routes
- [ ] AC7: nothing sensitive is written to `localStorage`, URLs, console or error reporting during any flow, and the
      token-storage choice follows the ADR required by the standard (UDR-12).
      Verify: `test:e2e --grep "no-leak"` (captures console, URL history and storage)
- [ ] AC8: `firebase.json` serves the strict CSP with the media origin (`storage.googleapis.com`, INFRA-010) added to
      `img-src` and nothing else loosened, and `Referrer-Policy: no-referrer` on `/join` and the auth routes (UDR-12).
      Verify: `uv run pytest -q tools/tests/test_hosting_headers.py` (parses `apps/web/firebase.json`)

## Test requirements
Vitest component tests; Playwright e2e against the Firebase Auth emulator (email, phone with emulator codes);
screenshots at 320, 768 and 1280 px stored for review. No real SMS is sent in any test.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (onboarding and legal pages split to WEB-037).

## Decisions
- One config endpoint (APP-018) is the single source for which methods exist; the web app has no copy of the list.

## Known issues
_None._

## Follow-ups
- Sign in with Apple appears only once the owner enables it (an Apple developer account is a paid step, G-35).
