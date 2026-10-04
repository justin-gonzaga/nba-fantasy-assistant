---
id: APP-005
title: "App-level login: Google sign-in, owner allowlist, token verification"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [APP-001]
areas: [apps/api/**, apps/web/src/api/schema.gen.ts, packages/core/src/fantasy_core/settings.py, infra/terraform/**, docs/security/**, docs/runbooks/**]
standards: [backend, security, testing]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# APP-005 — App-level login: Google sign-in, owner allowlist, token verification

## Objective
D-27, server side: every data request carries a Firebase ID token verified on the server; the verified email must
be on an allowlist; a per-user rate limit; the API fails closed outside local development; plus a security review.
The SPA's Google sign-in and the public invoker are WEB-013.

## Context to read (only these)
- D-27 in docs/project/architecture-decisions.md; docs/standards/backend.md; docs/standards/security.md

## Acceptance criteria
- [x] AC1: Data routes (today, matchup, waivers, freshness) need a valid token: missing/invalid -> 401 problem with
      `WWW-Authenticate: Bearer`; a verified allowlisted email passes; others -> 403; health stays public
      Verify: apps/api/tests/test_auth.py
- [x] AC2: Per-user rate limit (60/minute, sliding window) -> 429 problem
      Verify: test_auth.py::test_rate_limit_per_user_with_a_window
- [x] AC3: Outside APP_ENV=local the API refuses to start without an allowlist and a Firebase project; Cloud Run
      gets both from Terraform, the allowlist from a git-ignored tfvars (empty by default: fails closed)
      Verify: test_auth.py::test_outside_local_an_allowlist_is_required; terraform run "api_fails_closed_without_an_allowlist"
- [x] AC4: A security review with threats, mitigations and tests
      Verify: docs/security/app-005-auth-review.md

## Test requirements
TDD with a fake token verifier; terraform test for the Cloud Run environment.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest -q apps/api/tests/test_auth.py` | passed (4 routes x missing token, forged 401, stranger/unverified 403, owner 200) |
| AC2 | test | test_rate_limit_per_user_with_a_window | passed (2/min: 200, 200, 429; after 61 s: 200) |
| AC3 | test + terraform test | test_outside_local_an_allowlist_is_required; `terraform -chdir=infra/terraform/modules/env test` | passed; 13 passed, 0 failed |
| AC4 | doc | docs/security/app-005-auth-review.md | 8 threats, each with a mitigation and a test or evidence |

## Implementation history
- 2026-09-28: auth.py (InvalidToken, RateLimiter, AuthConfig, firebase_verifier, current_user); ApiProblem headers;
  routers depend on current_user; `require_auth_config`; settings `allowed_emails` / `firebase_project`; Cloud Run
  env FIREBASE_PROJECT + ALLOWED_EMAILS (sensitive variable); OpenAPI + TS types regenerated (HTTPBearer scheme).

## Decisions
- The allowlist is a sensitive Terraform variable (git-ignored owner.auto.tfvars), not a Secret Manager secret: a
  secret with no version would make the owner's first apply fail when it creates the service.

## Known issues
- Reviewer (PASS): a Google key-endpoint outage during verification surfaces as a generic 500 (type-only log), not a 401; no leak.
- Rate limit per instance (max 2 instances); see the review's residual risks.

## Follow-ups
- WEB-013: the SPA's Google sign-in (Firebase Auth), then the Cloud Run `allUsers` invoker and `VITE_API_URL`.
