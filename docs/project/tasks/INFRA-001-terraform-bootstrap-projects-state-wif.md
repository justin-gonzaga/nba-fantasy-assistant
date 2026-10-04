---
id: INFRA-001
title: "Terraform bootstrap: dev/prod projects, state bucket, Workload Identity Federation"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [FND-001]
areas: [infra/terraform/**, docs/runbooks/**, .github/workflows/**]
standards: [devops, security]
assignee:
created: 2026-09-24
completed: 2026-09-25
---
# INFRA-001 — Terraform bootstrap: dev/prod projects, state bucket, Workload Identity Federation

## Objective
Create the GCP foundation with Terraform so every later resource is code-managed.

## Notes
Needs the owner: create the GCP account and billing (~10 min). Bootstrap state is applied once locally, then migrated to the GCS backend.

## Context to read (only these)
- `docs/project/architecture-decisions.md` Part 7 (I1–I6), D-01, D-04, D-28
- `docs/standards/security.md`

## Acceptance criteria
- [x] AC1: Owner actions documented and done (runbook docs/runbooks/gcp-bootstrap.md): GCP account, billing account, `gcloud auth login` + ADC
      Verify: `just doctor` shows gcloud login + ADC ok
- [x] AC2: `infra/terraform/bootstrap` creates: an admin area with a versioned, locked tfstate bucket; projects `<prefix>-dev` and `<prefix>-prod` with the required APIs enabled
      Verify: `terraform apply` output + `gcloud storage buckets describe gs://<prefix>-tfstate`
- [x] AC3: Workload Identity Federation pool/provider restricted to the owner's GitHub repo; a deploy SA impersonable only from `main` for prod, and from any branch for dev
      Verify: wif.tf attribute_condition/principalSet review; CI auth run in FND-006
- [x] AC4: Billing budget at the G-08 ceiling with alert thresholds (50/90/100 %)
      Verify: apply output `budget_id`; thresholds in budget.tf
- [x] AC5: Claude's local credentials limited to the dev project (documented; prod is reachable only via CI)
      Verify: `gcloud projects get-iam-policy <prefix>-prod` filtered to claude-agent shows viewer roles only

## Test requirements
`terraform fmt -check`, `terraform validate`, and `tflint` in CI; `terraform plan` shows no drift after apply; IAM verified by negative tests (e.g. the ingest SA cannot delete raw objects).

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | owner actions | docs/runbooks/gcp-bootstrap.md; `just doctor` (gcloud login + ADC ok) | ✅ |
| AC2 | terraform apply | `Apply complete! Resources: 54 added`; `gcloud storage buckets describe gs://nbafa-hdfo-tfstate` → versioned, PAP enforced, AUSTRALIA-SOUTHEAST1 | ✅ |
| AC3 | code + plan | wif.tf: condition on repository_id/owner_id; prod SA bound to `attribute.deploy_tier/prod` (main or v* tags) | ✅ (end-to-end test in FND-006 CI) |
| AC4 | apply output | budget_id a0f47317-…; A$15/month, thresholds 0.5/0.9/1.0 | ✅ |
| AC5 | IAM query | `gcloud projects get-iam-policy nbafa-hdfo-prod` for claude-agent → only logging.viewer, monitoring.viewer | ✅ |
| Drift | terraform plan after state migration to GCS | `No changes`, exit 0 | ✅ |

## Implementation history
- 2026-09-25: Terraform written; `init/validate/plan` run (54 to add). Plain-English summary in docs/infra/bootstrap-plan-summary.md. Owner approved apply (panel).
- 2026-09-25: Applied (54 added); state migrated to gs://nbafa-hdfo-tfstate/bootstrap; re-plan shows no changes; local state deleted. tflint + IAM negative tests carried to FND-006/INFRA-002.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
