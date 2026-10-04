---
id: DATA-008
title: "Daily + intraday snapshot jobs scheduled (collection LIVE)"
epic: EP-20 Ingestion
phase: 2
component: pipeline
status: todo
ready: true
size: S
autonomy: review
gate: G-15
depends_on: [DATA-026, DATA-006, DATA-007, FND-011, FND-012, FND-013, INFRA-004]
areas: [apps/pipeline/**, docs/runbooks/**]
standards: [data-engineering, devops]
assignee:
created: 2026-09-24
completed:
---
# DATA-008 — Daily + intraday snapshot jobs scheduled (collection LIVE)

## Objective
MILESTONE M1: point-in-time collection running on schedule before 2026-10-20.

## Context to read (only these)
- `docs/project/roadmap.md M1`

## Acceptance criteria
- [ ] AC1: `fantasy run daily-snapshot` runs Yahoo + NBA CDN jobs; `fantasy run injury-snapshot` intraday
- [ ] AC2: Cloud Scheduler → Cloud Run jobs run unattended for 3 consecutive days with results in job_runs
- [ ] AC3: Failure alert demonstrated
- [ ] AC4: Runbook docs/runbooks/daily-collection.md (what to check, how to re-run)

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
