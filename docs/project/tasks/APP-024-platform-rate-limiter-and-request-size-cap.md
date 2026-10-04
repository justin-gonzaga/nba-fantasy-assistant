---
id: APP-024
title: "The platform rate limiter, request size cap and abuse-control table"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-008, APP-020, APP-026]
areas: [apps/api/src/fantasy_api/ratelimit*.py, apps/api/src/fantasy_api/limits_table.py, apps/api/tests/test_ratelimit.py, apps/api/tests/test_request_limits.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-024 — The one rate limiter

## Objective
Every feature that can be hammered needs a limit, and there must be exactly one mechanism and one table so limits are
not scattered or duplicated. This task builds the mechanism (a per-instance token bucket for short windows and shared
Firestore counters for daily and hourly limits), the config table, the request-size cap and the route-walk test.
**Every later task adds rows to the table and nothing else**: APP-012 (`/usernames/*`), APP-013 (uploads), APP-014 and
APP-022 (league creates), APP-015 (previews, joins), APP-017 (reports), APP-023 (requests). Step-up, MFA and session
revocation are APP-027. Rules: `docs/standards/user-data-and-auth.md` (Sessions, Phone/SMS).

**What this task cannot do (found in review).** The sign-in screens call Firebase directly with the client SDK, so SMS
codes and verification or reset emails are sent by Firebase and never pass through this API. The API therefore cannot cap
them. Their controls are the SMS region allow-list, reCAPTCHA defence, the provider's own throttles, the billing budget
and a usage alert (INFRA-009), the `AUTH_METHODS` kill switch (APP-018) and a measured drill (SEC-002).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Sessions, Phone/SMS, Logging)
- `docs/specification/leagues-and-accounts.md` §8; APP-020 `record_event`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Attacker hammering | "bounded" | per-IP and per-account limits per route group; 429 with `Retry-After`; thresholds in one table |
| Cloud Run scale-out | "limits still hold" | short windows use a per-instance bucket (documented tolerance: N instances allow up to N times the rate); daily and hourly limits use Firestore counters shared across instances |
| Counter store down or a counter missing | "fail safe" | the limit becomes tighter (a stricter default), never looser |
| Huge request body | "refused early" | a 16 KB body cap on JSON routes (the avatar upload route has its own 2 MB cap in APP-013) returns 413 |
| New route without a limit | "cannot forget" | the OpenAPI route walk fails for a write route with no table row or explicit `unlimited` reason |
| Lockout of a legitimate user | "recoverable" | per-account limits reset on a rolling window; the owner can read the limit state; no permanent lockouts from limits |

## Acceptance criteria
- [ ] AC1: one `rate_limit(group)` dependency and one table (`limits_table.py`) hold every threshold; exceeding returns
      429 with `Retry-After`; there is no second limiter.
      Verify: `uv run pytest -q apps/api/tests/test_ratelimit.py -k "limits or retry_after"`;
      `grep -rln "class .*RateLimit\|def rate_limit" apps` lists only the limiter module
- [ ] AC2: short windows are per-instance buckets; daily and hourly limits use shared counters (store contract test on
      both backends) and survive an instance restart.
      Verify: `uv run pytest -q apps/api/tests/test_ratelimit.py -k "shared or restart"`
- [ ] AC3: a missing or unreadable counter fails safe (stricter, never looser).
      Verify: `uv run pytest -q apps/api/tests/test_ratelimit.py -k "fail_safe"`
- [ ] AC4: a route-walk test fails when a write route has neither a table row nor an `unlimited` reason, and the table is
      seeded with the rows in the spec §8 that already exist (default write limit per account and per IP).
      Verify: `uv run pytest -q apps/api/tests/test_ratelimit.py -k "route_walk"`
- [ ] AC5: JSON request bodies over 16 KB return 413 and are not parsed; the exemption list is explicit.
      Verify: `uv run pytest -q apps/api/tests/test_request_limits.py`
- [ ] AC6: limit hits are security events (APP-020) with the route group and a pseudonymous id, never an IP in clear.
      Verify: `uv run pytest -q apps/api/tests/test_ratelimit.py -k "event"`

## Test requirements
Fake clock; store contract tests on the in-memory and the Firestore-emulator backends; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original APP-018). Narrowed after review: SMS and verification-email caps cannot
  be enforced at the API; step-up, MFA and revocation moved to APP-027.

## Decisions
- A limiter that every feature feeds rows into is the guard against duplicate throttles.

## Known issues
- The per-instance bucket tolerance (N times the rate across N instances) is deliberate and documented; D-71 caps
  instances at a small number.

## Follow-ups
_None._
