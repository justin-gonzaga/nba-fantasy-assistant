---
id: DATA-023
title: "DQ framework: dq_results, reconciliation, freshness, `just dq`"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: S
autonomy: auto
gate: G-20
depends_on: [DATA-021, DATA-000]
areas: [warehouse/**, apps/pipeline/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-023 — DQ framework: dq_results, reconciliation, freshness, `just dq`

## Objective
Operationalise architecture §4.5.

## Context to read (only these)
- `docs/architecture/system-architecture.md §4.5`

## Acceptance criteria
- [ ] AC1: All six DQ dimensions have at least one check
- [ ] AC2: Results persisted to gold.dq_results; error blocks promotion, warn surfaces
- [ ] AC3: `just dq` summary is phone-length

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
