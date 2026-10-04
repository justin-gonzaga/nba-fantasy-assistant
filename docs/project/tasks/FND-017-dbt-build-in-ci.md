---
id: FND-017
title: "dbt build in CI against dev raw (per-PR datasets)"
epic: EP-10 Foundation
phase: 1
component: ci
status: done
ready: true
size: S
autonomy: review
gate: G-01
depends_on: [FND-006, INFRA-002]
areas: [.github/**, infra/terraform/modules/env/**, warehouse/dbt_project.yml]
standards: [devops, security, data]
assignee: claude
created: 2026-09-27
completed: 2026-09-27
---
# FND-017 — dbt build in CI against dev raw (per-PR datasets)

## Objective
Every PR runs `dbt build` (models, seeds, data tests) against the dev raw layer, so a broken model
or a failing data test blocks the merge. Follow-up from FND-006; owner approved 2026-09-27.

## Context to read (only these)
- `docs/standards/devops.md §2`
- `infra/terraform/modules/env/main.tf` (CI section)

## Acceptance criteria
- [x] AC1: The dev deploy SA gets read-only access to the dev raw bucket and raw dataset; prod gets none
      Verify: `terraform -chdir=infra/terraform/modules/env test` (ci_reads_dev_raw_only, ci_has_no_prod_raw_access)
- [x] AC2: The grant is applied in dev and nothing else changes
      Verify: `terraform plan` on envs/dev shows 2 to add, 0 to change, 0 to destroy; then apply
- [x] AC3: A `dbt` CI job builds into labelled ci_pr<N>_* datasets and drops them afterwards
      Verify: .github/workflows/ci.yml job `dbt`; `bq ls` shows no ci_pr<N>_* datasets after the run
- [x] AC4: The dbt job passes on this PR and is a required check on main
      Verify: `gh pr checks`; ruleset 24059050 required contexts include dbt

## Test requirements
Terraform policy tests for AC1 (mock provider); the CI run itself for AC3–AC4.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tf test | `terraform test` on modules/env: 7 passed (incl. ci_reads_dev_raw_only, ci_has_no_prod_raw_access) | pass |
| AC2 | plan/apply | dev plan: 2 to add, 0 to change, 0 to destroy; applied by the owner 2026-09-27 (Claude is not permitted to apply); `bq show nbafa-hdfo-dev:raw` lists the deploy SA | pass |
| AC3 | CI run | PR #30 job `dbt`: PASS=79 WARN=2 ERROR=0 (81 nodes), 2 m 15 s; afterwards `bq ls` shows 0 ci_pr30_* datasets | pass |
| AC4 | CI + ruleset | `dbt` green on PR #30; added to the required checks of ruleset 24059050 | pass |

## Implementation history
- 2026-09-27: The first apply was run on main (no change: the resources only existed on this branch); re-applied from the branch, then the dbt job passed on rerun.

## Decisions
- dbt runs on PRs only (main is already built by the pipeline); the CI identity reads dev raw, never prod.
- Seeds get an explicit `+schema: staging` so CI puts them in ci_pr<N>_staging (dev/prod unchanged).

## Known issues
_None._

## Follow-ups
_None._
