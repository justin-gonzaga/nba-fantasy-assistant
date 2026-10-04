---
id: INFRA-002
title: "Buckets, BigQuery datasets, service accounts and least-privilege IAM"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-001]
areas: [infra/terraform/**, docs/runbooks/**, .github/workflows/**]
standards: [devops, security]
assignee: claude
created: 2026-09-24
completed: 2026-09-25
---
# INFRA-002 — Buckets, BigQuery datasets, service accounts and least-privilege IAM

## Objective
Provision the storage and identities used by ingestion, dbt and the API in both environments.

## Context to read (only these)
- `docs/project/architecture-decisions.md` Part 7 (I1–I6), D-01, D-04, D-28
- `docs/standards/security.md`

## Acceptance criteria
- [x] AC1: Per-env buckets: raw (prod: versioning + retention policy; dev: 30-day lifecycle), exports; naming convention documented
      Verify: `terraform test` (modules/env) runs dev_buckets… and prod_raw…; runbook docs/runbooks/gcp-environments.md naming table
- [x] AC2: BigQuery datasets per env: raw, staging, intermediate, marts (dbt-native names, S-10 B), features, predictions, recs; plus the CI ephemeral-dataset pattern (per-PR prefix + cleanup job)
      Verify: `terraform test` datasets_use_dbt_native_layers; `.github/workflows/ci-dataset-cleanup.yml` dispatch run
- [x] AC3: Service accounts: ingest (raw object create, no delete), transform (BQ data editor on its datasets + raw read), api (BQ data viewer + job user), scheduler (Cloud Run invoker), deploy (CI)
      Verify: `terraform test` least_privilege_roles; `python tools/iam_negative_tests.py`
- [x] AC4: The dev ingest/transform SAs have read-only access to the prod raw bucket (I3 A)
      Verify: `python tools/iam_negative_tests.py` (dev ingest-sa: get allowed, create denied on prod raw)
- [x] AC5: Negative IAM tests pass (e.g. deleting a raw object is denied; the api SA cannot write)
      Verify: `python tools/iam_negative_tests.py` → 10/10

## Test requirements
`terraform fmt -check`, `terraform validate`, and `tflint` in CI; `terraform plan` shows no drift after apply; IAM verified by negative tests (e.g. the ingest SA cannot delete raw objects).

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | terraform test + apply | `terraform -chdir=infra/terraform/modules/env test` → 5 passed; buckets nbafa-hdfo-{dev,prod}-{raw,exports}; prod raw versioned + 30-day unlocked retention (owner panel); dev 30-day lifecycle | ✅ |
| AC2 | terraform test + apply | 7 datasets per env (dbt-native names); CI pattern `ci_pr<N>_*` + label ci=true; cleanup workflow + repo var GCP_WIF_PROVIDER set | ✅ (cleanup workflow run 36092863016 succeeded via WIF) |
| AC3 | apply + IAM tests | ingest-sa, transform-sa, api-sa, scheduler-sa per env; deploy SA from bootstrap gets dev `bigquery.user` for CI | ✅ |
| AC4 | IAM tests | dev ingest-sa: `storage.objects.get` on prod raw PASS allow; `storage.objects.create` PASS deny | ✅ |
| AC5 | IAM tests | `python tools/iam_negative_tests.py` → 10/10 passed (Policy Troubleshooter) | ✅ |
| Drift | terraform plan | dev and prod: `No changes`, exit 0 | ✅ |
| Checks | just ci-local | 104 passed, coverage 100 % | ✅ |

## Implementation history
- 2026-09-25: module `infra/terraform/modules/env` + roots `envs/{dev,prod}`; plan-time tests (mock provider). Owner approved apply + 30-day retention (panel). Applied dev then prod (33 + 33); re-plan clean; IAM tests 10/10.

## Decisions
- Dataset names follow S-10 B (dbt-native), superseding the AC's bronze/silver/gold wording.
- SA IDs are `<workload>-sa` (GCP needs 6–30 chars; `api` alone is too short).
- Retention stays unlocked so `just purge-yahoo` stays possible (owner: 30 days).

## Known issues
_None._

## Follow-ups
_None._
