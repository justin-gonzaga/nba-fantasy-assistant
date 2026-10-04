---
id: WEB-013
title: "SPA Google sign-in (Firebase Auth) + public invoker + live API URL"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [APP-005]
areas: [apps/web/**, apps/api/**, packages/core/src/fantasy_core/settings.py, infra/terraform/**, .github/workflows/ci.yml, docs/**]
standards: [frontend, security]
assignee:
created: 2026-09-28
completed: 2026-09-28
---
# WEB-013 — SPA Google sign-in (Firebase Auth) + public invoker + live API URL

## Objective
The website signs the owner in with Google (Firebase Auth) and sends the ID token to the API (APP-005 verifies it);
the Cloud Run API gets a public invoker in dev (its own sign-in checks protect data); Terraform creates the Firebase
web app and outputs the live build's public variables. Demo mode stays sign-in-free and never loads the Firebase SDK.

## Context to read (only these)
- D-27 in docs/project/architecture-decisions.md; docs/security/app-005-auth-review.md; docs/standards/frontend.md

## Acceptance criteria
- [x] AC1: Live mode shows "Sign in with Google" until signed in, then the app with the account and a sign-out;
      a failed sign-in is shown; demo mode needs no sign-in
      Verify: apps/web/src/auth/auth.test.tsx
- [x] AC2: Every live API call carries `Authorization: Bearer <ID token>`
      Verify: auth.test.tsx "sends the sign-in token as a bearer header"
- [x] AC3: Terraform: the Firebase web app, the Auth API enabled, a public invoker only where the env opts in (dev),
      and an output with the live build's public variables
      Verify: `terraform -chdir=infra/terraform/modules/env test` runs "api_public_only_when_opted_in", "api_fails_closed_without_an_allowlist"
- [x] AC4: The Firebase SDK is loaded only in live mode (a separate chunk); the initial bundle stays within budget
      Verify: `just web build` output (chunks) and the CI budget step

## Test requirements
Vitest with a fake auth adapter; terraform test (mocked providers).

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `just web test` (auth.test.tsx: sign in, account + sign out, failed sign-in, demo without sign-in) | passed (25 web tests) |
| AC2 | test | auth.test.tsx "sends the sign-in token as a bearer header" | passed |
| AC3 | terraform test | `terraform -chdir=infra/terraform/modules/env test` | 14 passed, 0 failed (2 new/extended runs) |
| AC4 | build | `pnpm build` | entry 114 kB gzipped; Firebase in separate lazy chunks (~46 kB); all JS 158 kB (< 200 kB budget) |

## Implementation history
- 2026-09-28: auth/auth.tsx (AuthAdapter, SignInGate, useSession), auth/firebase.ts (config from env, lazy SDK), http token header, select.ts live mode = API URL + Firebase config, App wiring + sign-out; Terraform: identitytoolkit API, firebase web app + config data source, `api_public` (dev: true), outputs `web_build_env`; CI hosting build reads the five repo variables; runbook step 5.

## Decisions
- The Firebase web config (API key, auth domain, app id) is public by design and goes into GitHub repo variables
  for the build; it is not a secret. Access control is the API's allowlist.

- Reviewer (CHANGES REQUESTED -> fixed): the API had no CORS, so browsers would have blocked every live call
  (unit tests use a stub fetch, which doesn't enforce CORS). Added CORSMiddleware: the site's origins plus a regex
  for PR preview channels, GET only, `Authorization` allowed (apps/api/tests/test_cors.py); Terraform sets
  CORS_ORIGINS / CORS_ORIGIN_REGEX. /docs, /redoc and /openapi.json are now off outside local.

## Known issues
- End-to-end sign-in can't be tested before the owner's apply and the console's "enable Google" step.

## Follow-ups
_None._
