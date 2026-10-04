---
id: FND-012
title: "Schedules as code: schedules.yaml → Cloud Scheduler (Terraform) + local on-demand runs"
epic: EP-10 Foundation
phase: 1
component: pipeline
status: todo
ready: true
size: S
autonomy: review
gate: G-13
depends_on: [FND-011]
areas: [apps/pipeline/schedules.yaml, tools/**, docs/runbooks/**]
standards: [devops]
assignee:
created: 2026-09-24
completed:
---
# FND-012 — Local scheduling from schedules.yaml (Windows Task Scheduler)

## Objective
Declare schedules once (schedules.yaml); render them to Cloud Scheduler via Terraform. Cloud from day one (owner, 2026-09-24).

## Context to read (only these)
- `docs/standards/devops.md §6`

## Acceptance criteria
- [ ] AC1: schedules.yaml with daily snapshot and intraday injury schedules per G-13
- [ ] AC2: `schedules.yaml` renders to Terraform Cloud Scheduler jobs (INFRA-004). Locally, `just pipeline <job>` runs on demand; a Windows task is used only for the one-off stats.nba.com history download
- [ ] AC3: Runbook docs/runbooks/scheduling.md
- [ ] AC4: Awake-window support (NFR10): the configurable window suppresses user-facing jobs and notifications outside it, and a morning catch-up job runs at window start

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
