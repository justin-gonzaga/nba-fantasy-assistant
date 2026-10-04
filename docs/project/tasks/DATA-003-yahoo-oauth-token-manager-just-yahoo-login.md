---
id: DATA-003
title: "Yahoo OAuth token manager + `just yahoo-login`"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: blocked
ready: true
size: S
autonomy: auto
gate: G-03
depends_on: [DATA-002, DISC-001]
areas: [packages/ingest/**, justfile, docs/runbooks/**]
standards: [security]
assignee:
created: 2026-09-24
completed:
---
# DATA-003 — Yahoo OAuth token manager + `just yahoo-login`

## Objective
Owner-run one-time consent; automatic refresh; alerts on refresh failure.

## Context to read (only these)
- `docs/research/yahoo-api.md`
- `docs/standards/security.md §2`

## Acceptance criteria
- [ ] AC1: `just yahoo-login` performs auth-code flow and stores token file with owner-only permissions
- [ ] AC2: Automatic refresh before expiry; refresh failure raises + notifies, no retry storm
- [ ] AC3: Token values never logged (test asserts)
- [ ] AC4: Runbook docs/runbooks/yahoo-auth.md

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
Blocked 2026-09-25: the Yahoo Fantasy API is closed to existing apps (ADR-0025). Resumes only if YAHOO-001 is approved; meanwhile DISC-011/DATA-026 (assisted import) replace it.

## Follow-ups
_None._
