---
id: INFRA-004
title: "Cloud Run jobs/service + Cloud Scheduler (awake window)"
epic: EP-11 Infrastructure
phase: 2
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-003, FND-015]
areas: [infra/**, .github/workflows/ci.yml, apps/pipeline/**, packages/core/src/fantasy_core/settings.py, docs/runbooks/**]
standards: [devops, security]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# INFRA-004 — Cloud Run jobs/service + Cloud Scheduler (awake window)

## Objective
Deploy the API as a Cloud Run service (private until APP-005), deployed by CI by image digest, reading the serve
bucket that the daily chain now publishes to. Pipeline jobs on Cloud Run + Scheduler move to INFRA-006.

## Context to read (only these)
- docs/standards/devops.md
- infra/terraform/modules/env/serving.tf, run.tf

## Acceptance criteria
- [x] AC1: A Cloud Run `api` service running as the api identity, scaling to zero, reading the serve bucket, with
      no public invoker; only CI deploys revisions
      Verify: `terraform -chdir=infra/terraform/modules/env test` run "api_runs_privately_as_the_api_identity"
- [x] AC2: CI builds, pushes and deploys the image by digest on merge to main, behind `CLOUD_RUN_ENABLED`
      Verify: .github/workflows/ci.yml job `deploy-api`
- [x] AC3: The daily chain publishes the day's outputs to `SERVE_ROOT` (optional job; never blocks the brief)
      Verify: apps/pipeline/tests/test_publish.py; test_jobs_nba.py (publish = 0 without a serve root)
- [x] AC4: The dev plan only adds resources; an owner runbook lists the steps
      Verify: `terraform -chdir=infra/terraform/envs/dev plan`; docs/runbooks/api-hosting.md

## Test requirements
terraform test (mocked providers); pytest for the publish job.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | terraform test | run "api_runs_privately_as_the_api_identity" | pass (suite 12 passed, 0 failed) |
| AC2 | CI config | ci.yml `deploy-api` (needs `image`; WIF auth; build, Trivy-scan the same image, push, `gcloud run deploy --image <digest>`) | added; runs after the owner's apply + variable |
| AC3 | test | `uv run pytest -q apps/pipeline` | 52 passed, incl. test_publish (2); full suite 392 passed |
| AC4 | plan + doc | dev plan; docs/runbooks/api-hosting.md | Plan: 31 to add, 0 to change, 0 to destroy |

## Implementation history
- 2026-09-28: run.tf (Cloud Run v2 service with a placeholder image Terraform then ignores; CI deploy + actAs
  bindings), CI `deploy-api`, `publish` module + optional `publish` job, `serve_root` setting, runbook.

## Decisions
- The service account email is written from the naming convention (known at plan time) with an explicit
  dependency on the account, so plan-time tests can check it.

## Known issues
- Reviewer (PASS): the deploy job now scans the exact image it pushes (it builds its own copy; the `image` job's scan covers PRs).
- End-to-end deploy is untested until the owner's apply (the registry and service must exist first).

## Follow-ups
- INFRA-006: pipeline jobs on Cloud Run Jobs + Cloud Scheduler (so the owner's PC can be off).
- APP-005: sign-in, then a public invoker and `VITE_API_URL` on the website build.
