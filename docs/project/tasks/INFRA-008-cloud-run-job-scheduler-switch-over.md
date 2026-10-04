---
id: INFRA-008
title: "Cloud Run job + Cloud Scheduler for the daily chain; owner switch-over"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-007]
areas: [infra/**, .github/workflows/**, docs/**, tools/schedule_daily.ps1]
standards: [devops, security]
assignee:
created: 2026-10-02
completed: 2026-10-02
---
# INFRA-008 — Cloud Run job + Cloud Scheduler for the daily chain; owner switch-over

## Objective
D-63: Terraform a Cloud Run job (`job cloud`) running as transform-sa with WORK_ROOT = the serve bucket, DATA_ROOT = the raw bucket,
the Telegram token from Secret Manager and TELEGRAM_CHAT_ID from a git-ignored tfvars; Cloud Scheduler triggers it at 07:45 Sydney; CI
updates the job's image on deploy. The owner switches the PC to `run fetch` writing raw to GCS.

## Context to read (only these)
- D-63 in docs/project/architecture-decisions.md; docs/project/tasks/INFRA-006-pipeline-jobs-on-cloud-run.md

## Acceptance criteria
- [x] AC1: Terraform: the job, the scheduler (07:45 Australia/Sydney), least-privilege IAM (scheduler invokes; transform reads raw,
      writes serve, reads the secret)
      Verify: `terraform -chdir=infra/terraform/modules/env test`; dev plan only adds
- [x] AC2: CI deploys the job's image by digest with the API's
      Verify: ci.yml deploy step
- [x] AC3: Runbook for the switch-over (secret value, tfvars, DATA_ROOT, the PC task) and a first scheduled run succeeds
      Verify: docs/runbooks/daily-brief.md; the execution log

## Test requirements
TDD; terraform test with mocked providers.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | terraform test + plan | `terraform -chdir=infra/terraform/modules/env test`; dev plan | 15 passed (run "daily_chain_runs_in_the_cloud_on_a_schedule"); Plan: 6 to add, 0 to change, 0 to destroy |
| AC2 | CI config | ci.yml deploy-api: "the daily job runs the same image" (skips until the job exists) | added |
| AC3 | runbook + run | docs/runbooks/daily-brief.md "Switch-over to the cloud chain"; first scheduled execution `daily-sk7hx` (Cloud Scheduler, 2026-10-03 07:45 Sydney = 2026-10-02T21:45Z): succeeded; run log rows incl. `draft-values success 5890` | pass |

## Implementation history
- 2026-10-02: daily.tf (Cloud Run job `daily` running `job cloud` as transform-sa with DATA_ROOT=raw, WORK_ROOT=SERVE_ROOT=serve, TELEGRAM_CHAT_ID from tfvars and the bot token from Secret Manager; transform-sa create-only on raw for the injury report; CI deploy + act-as; Cloud Scheduler 07:45 Australia/Sydney, paused until `daily_schedule_enabled`), dev variables + example tfvars, CI image update, schedule_daily.ps1 `-Mode fetch`, runbook switch-over.

## Decisions
_None yet._

## Known issues
- Not end-to-end tested until the owner adds the token to Secret Manager and applies (the job references the secret's latest version).
- AC3's "first scheduled run succeeds" stays open until the switch-over; this task stays in progress.

## Follow-ups
_None._
