---
id: APP-027
title: "Step-up sign-in, MFA level and session revocation"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-018, APP-020, APP-024]
areas: [apps/api/src/fantasy_api/auth/stepup*.py, apps/api/src/fantasy_api/auth/sessions*.py, apps/api/tests/test_auth_stepup.py, apps/api/tests/test_auth_sessions.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-027 — Step-up, MFA level, session revocation

## Objective
Sensitive actions need a recent sign-in, the owner (and admin routes) must have a second factor, and a compromised
account must be recoverable by signing out everywhere. The platform rate limiter is APP-024 and the identity itself is
APP-018; this task consumes both. Rules: `docs/standards/user-data-and-auth.md` (Sessions, Account recovery).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Authentication, Sessions, Account recovery)
- APP-018's `Identity`; APP-020 `record_event`; APP-024's rate-limit table

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member doing something sensitive | "ask me again" | delete account, change email, remove a provider, export, and (for commissioners) transfer or delete a league need `auth_time` within 5 minutes, else 401 `reauth-required`; **every task that adds a sensitive route adds it to the one table here** |
| Owner / big commissioner | "protect my account" | optional TOTP enrolment; the owner and commissioners with 3+ members are prompted; SMS is never the only recovery for the owner |
| Lost device | "sign out everywhere" | `POST /me/sessions:revoke` revokes refresh tokens; sensitive routes and all writes check revocation; tokens issued before the revocation time are rejected |
| Admin routes | owner-only | `requires_mfa` routes return 403 `mfa-required` without a second factor |
| TOTP lost | "I am locked out" | Firebase provides no recovery codes (RSCH-010): the documented recovery is the owner removing the factor after a verified-email check (a security event); the app does not invent codes |
| Revocation check cost | "not slow" | revocation is checked on writes and sensitive routes only; the latency is measured against D-71 targets (SPK-4) |

## Acceptance criteria
- [ ] AC1: step-up: the listed sensitive routes return 401 `reauth-required` when `auth_time` is older than 5 minutes
      and succeed otherwise; the route list is one table and the OpenAPI walk test fails when a new sensitive route is
      missing from it (the table includes `/me/export`, `DELETE /me`, provider link or unlink, league transfer and
      delete, and `/admin/users/{id}:purge`).
      Verify: `uv run pytest -q apps/api/tests/test_auth_stepup.py`
- [ ] AC2: `POST /me/sessions:revoke` revokes refresh tokens; a token issued before the revocation is rejected on every
      route that checks revocation (all sensitive routes and all writes); the old address is notified of an email
      change, MFA change or provider change by an event the notifier consumes (UDR-07).
      Verify: `uv run pytest -q apps/api/tests/test_auth_sessions.py`
- [ ] AC3: the identity records `mfa: none|totp|sms`; `requires_mfa` routes (owner-only admin, moderation) return 403
      `mfa-required` without it; the owner account must have TOTP before admin routes work.
      Verify: `uv run pytest -q apps/api/tests/test_auth_stepup.py -k "mfa"`
- [ ] AC4: absolute session lifetime is capped at 30 days and a stale refresh is refused (UDR-10).
      Verify: `uv run pytest -q apps/api/tests/test_auth_sessions.py -k "lifetime"`

## Test requirements
Fake clock; Firebase Auth emulator for revocation; no real SMS.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split out of APP-024 so the rate limiter can ship before the auth stack is finished).

## Decisions
_None yet._

## Known issues
- Enrolling SMS as a second factor costs money like phone sign-in; TOTP is the default MFA.

## Follow-ups
- WEB-036 provides the screens for MFA, sessions and linked providers.
