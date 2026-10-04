---
id: WEB-012
title: "Firebase Hosting for the SPA (dev + prod), PR previews, /api rewrite"
epic: EP-70 Dashboard
phase: 7
component: infra
status: in_progress
ready: true
size: M
autonomy: review
gate: G-06
depends_on: [WEB-001]
areas: [infra/terraform/**, .github/workflows/**, apps/web/**, firebase.json]
standards: [devops, security, frontend]
assignee: claude
created: 2026-09-27
completed: null
---
# WEB-012 — Firebase Hosting for the SPA (D-59)

## Objective
Serve `apps/web` from Firebase Hosting in dev and prod, deployed by CI, with a preview link per PR and `/api/**` rewritten to the Cloud Run API.

## Context to read (only these)
- docs/project/architecture-decisions.md D-59
- infra/terraform/modules/env/main.tf

## Acceptance criteria
- [ ] AC1: Terraform enables Firebase and a Hosting site in each env project; the deploy SA gets only the Hosting admin role; policy tests cover it
      Verify: `terraform test` on modules/env; the dev plan reviewed (the owner runs `apply` from the branch)
- [x] AC2: `firebase.json`: SPA fallback to index.html, long cache for hashed assets, no-cache for index.html, security headers (CSP, HSTS, X-Content-Type-Options, Referrer-Policy)
      Verify: a test parses firebase.json; `curl -I` on the dev site shows the headers
- [ ] AC3: CI deploys a preview channel per PR (link posted on the PR) and the dev live site on merge to main; prod only from a CalVer tag
      Verify: a PR shows a preview link; the dev site serves the latest main
- [ ] AC4: `/api/**` rewrites to the Cloud Run API (once APP-001 exists; until then a 404 page)
      Verify: `curl https://<dev>.web.app/api/health`
- [ ] AC5: The public build shows only sample/anonymised data; the real app needs sign-in (D-27/D-38)
      Verify: WEB-010 / APP-005 tests; a manual check of the live site

## Test requirements
Terraform policy tests; a firebase.json unit test; a CI smoke `curl` against the preview URL.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tf test + plan | modules/env/hosting.tf (Firebase APIs, project, site = project id, deploy SA hosting admin); `terraform test` 8 passed; dev plan: 5 to add, 0 to change, 0 to destroy | ⏳ owner apply (from main after merge) |
| AC2 | test | apps/web/firebase.json; src/firebase.test.ts (3): SPA rewrite, CSP/HSTS/nosniff on every response, immutable assets, no-cache index.html | ✅ |
| AC3 | CI job | `hosting` job (preview channel per PR + comment; dev deploy on main), gated on the repo variable FIREBASE_ENABLED | ⏳ after apply |
| AC4 | — | the `/api/**` rewrite is added with APP-001 (no API yet); until then every route serves the SPA | ⏳ APP-001 |
| AC5 | — | the public build shows sample data only (fixtures); sign-in comes with APP-005 | ⏳ |

## Implementation history
- 2026-09-28: Terraform (google-beta ~> 7.0 added to the module and both envs), firebase.json + test, the gated CI job. Firebase tools pinned to 15.31.0.

## Decisions
- D-59: Firebase Hosting, public demo + invite-only, no custom domain.

## Known issues
- Firebase Hosting on a billing-enabled project uses the pay-as-you-go plan; our usage sits inside the free quota (10 GB storage, 360 MB/day transfer). A budget alert already exists on the projects.
- `terraform apply` is blocked for Claude by the permission classifier: the owner runs it from this task's branch.

## Follow-ups
_None._
