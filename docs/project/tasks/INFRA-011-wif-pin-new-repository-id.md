---
id: INFRA-011
title: "Pin Workload Identity Federation to the new public repository id"
epic: EP-10 Foundation
phase: 1
component: infra
status: in_progress
ready: true
size: S
autonomy: review
gate: G-36
depends_on: [SEC-001]
areas: [infra/terraform/bootstrap/**, docs/project/**]
standards: [security, infrastructure]
assignee: claude
created: 2026-10-04
completed:
---
# INFRA-011 — Pin Workload Identity Federation to the new repository id

## Objective
SEC-001 moved the project to a fresh public repository (the old one is now the private archive). The Workload
Identity provider only trusts the old numeric repository id, so the CI deploy jobs cannot authenticate to GCP from the
new repository. Pin the new id (and so stop trusting the archive), then re-enable the deploy jobs.

## Context to read (only these)
- `infra/terraform/bootstrap/wif.tf`, `variables.tf`
- `.github/workflows/ci.yml` (jobs gated by `vars.CLOUD_RUN_ENABLED` and `vars.FIREBASE_ENABLED`)

## Acceptance criteria
- [x] AC1: the default `github_repository_id` is the new repository's numeric id.
      Verify: `gh api repos/justin-gonzaga/nba-fantasy-assistant --jq .id` equals the default in `variables.tf`
- [x] AC2: the change is valid and its plan touches only the WIF trust.
      Verify: `terraform fmt -check`, `terraform validate`, and `terraform plan` show 1 to add, 1 to change, 1 to destroy
      (the provider's attribute condition and the dev deploy principal binding) and nothing else
- [ ] AC3: owner applies the bootstrap, then the deploy jobs run green from the new repository.
      Verify: after `terraform apply` (owner), set repository variables `CLOUD_RUN_ENABLED` and `FIREBASE_ENABLED` to
      `true`, then a merge to `main` shows the deploy jobs passing (`gh run list`)

## Test requirements
Plan only; Claude never runs `apply` against the shared admin project.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | command | new id 1403819022; `variables.tf` default updated | pass |
| AC2 | command | `terraform fmt -check`, `validate` (valid), `plan -lock=false`: `Plan: 1 to add, 1 to change, 1 to destroy`; changed: `google_iam_workload_identity_pool_provider.github` (attribute condition), replaced: `google_service_account_iam_member.deploy_dev_wif` | pass |
| AC3 | owner | `terraform apply` in `infra/terraform/bootstrap`, then flip the two variables | pending (owner) |

## Implementation history
- 2026-10-04 — Created after the repository swap (SEC-001, G-36). Until AC3, `CLOUD_RUN_ENABLED` and `FIREBASE_ENABLED`
  are `false` on the new repository so the deploy jobs are skipped instead of failing. The live site keeps running on
  the last deployed build.

## Decisions
- Keep matching on the immutable repository id (a recreated repository with the same name must not inherit access).

## Known issues
- Until the apply, no deploy from CI: new web and API changes are not live.

## Follow-ups
- Owner: apply, flip the two variables, confirm a deploy.
