---
id: INFRA-003
title: "Secret Manager + Artifact Registry"
epic: EP-11 Infrastructure
phase: 2
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-002]
areas: [infra/terraform/**, docs/runbooks/**, .github/workflows/**]
standards: [devops, security]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# INFRA-003 — Secret Manager + Artifact Registry

## Objective
Secrets per env (Telegram token, Yahoo client ID/secret/refresh token, Anthropic key) as names only with scoped
accessor bindings; a Docker registry with cleanup policies; and the serve bucket the API reads (D-62).

## Context to read (only these)
- docs/standards/security.md (secrets)
- infra/terraform/modules/env/*

## Acceptance criteria
- [x] AC1: An `images` Docker repository with cleanup policies; only the CI deploy identity may push
      Verify: `terraform -chdir=infra/terraform/modules/env test` run "images_are_registered_and_pruned"
- [x] AC2: A private `<prefix>-<env>-serve` bucket; api reads it, transform publishes to it
      Verify: run "serve_bucket_is_private_and_least_privilege"
- [x] AC3: Five secrets exist as names only (no values in Terraform); only transform and api can access them
      Verify: run "secrets_have_no_values_and_scoped_readers"
- [x] AC4: The dev plan adds only these resources (plus the pending Firebase ones): nothing changed or destroyed
      Verify: `terraform -chdir=infra/terraform/envs/dev plan`

## Test requirements
Plan-time policy tests with mocked providers (terraform test).

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | terraform test | run "images_are_registered_and_pruned" | pass (suite 11 passed, 0 failed) |
| AC2 | terraform test | run "serve_bucket_is_private_and_least_privilege" | pass |
| AC3 | terraform test | run "secrets_have_no_values_and_scoped_readers" | pass |
| AC4 | plan | `terraform -chdir=infra/terraform/envs/dev plan` | Plan: 28 to add, 0 to change, 0 to destroy (23 new + 5 pending Firebase) |

## Implementation history
- 2026-09-28: serving.tf (APIs, registry + CI push role, serve bucket + IAM, secrets + accessors), outputs, tests.
  The registry keeps 3 versions (~0.35 GB each) to stay near the 0.5 GB free tier.

## Decisions
- The apply is the owner's (Tier B infra; applies were classifier-blocked before). One dev apply covers Firebase too.

## Known issues
- Cost: Secret Manager within the free tier (6 versions/month); Artifact Registry about 1 GB stored, about
  US$0.05/month; the serve bucket is tiny.

## Follow-ups
- INFRA-004: the Cloud Run service (private until APP-005), the CI image push + deploy, and the pipeline's publish
  step to the serve bucket.
