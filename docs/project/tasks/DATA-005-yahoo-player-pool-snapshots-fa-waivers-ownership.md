---
id: DATA-005
title: "Yahoo player pool snapshots (FA/waivers, ownership, eligibility)"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: blocked
ready: true
size: S
autonomy: auto
gate: G-04
depends_on: [DATA-004]
areas: [packages/ingest/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-005 — Yahoo player pool snapshots (FA/waivers, ownership, eligibility)

## Objective
Daily snapshot of top-N free agents/waivers + all rostered players with ownership % and position eligibility.

## Context to read (only these)
- `docs/research/yahoo-api.md`

## Acceptance criteria
- [ ] AC1: Configurable N (default 300) by Yahoo rank; waivers included
- [ ] AC2: Ownership % and eligibility captured
- [ ] AC3: Contract tests on fixtures

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
