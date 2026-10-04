---
id: YAHOO-001
title: "Prepare the Yahoo developer programme application (owner submits)"
epic: EP-01 Discovery
phase: 0
component: docs
status: in_progress
ready: true
size: S
autonomy: gated
gate: none
depends_on: []
areas: [docs/**, packages/ingest/**, apps/**]
standards: [data-engineering, security]
assignee: claude
created: 2026-09-25
completed:
---
# YAHOO-001 — Prepare the Yahoo developer programme application (owner submits)

## Objective
Draft an honest application for sports.yahoo.com/developer (personal, non-commercial, portfolio/research use; Yahoo attribution; read-only; data minimisation and pseudonymisation). The owner reviews and submits it. Track the outcome.

## Context to read (only these)
- docs/research/yahoo-api.md
- docs/architecture/adr/0025-yahoo-api-closed-assisted-import.md

## Acceptance criteria
- [x] AC1: Application text drafted, covering the use case, data scope, privacy (pseudonymisation, deletion), attribution, and non-commercial status
      Verify: docs/project/yahoo-application.md
- [x] AC2: The owner submits it (owner action); the submission date is recorded
      Verify: Implementation history entry
- [ ] AC3: The outcome is tracked, with a follow-up task if approved (restore the API client behind the Source interface; rotate the secret)
      Verify: task file + ADR-0025 revisit trigger

## Test requirements
Per the testing standard.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
### 2026-09-25
- AC1 drafted: docs/project/yahoo-application.md (personal, non-commercial, read-only, pseudonymisation, attribution). The owner **submitted it on 2026-09-25** (form: Expected Users = Small; Notes per docs/project/yahoo-application.md; existing Client ID). AC3 (tracking the outcome) remains open.

## Decisions
_None yet._

## Known issues
The owner submits it; Claude drafts only.

## Follow-ups
_None._
