---
id: DATA-022
title: "AsOfReader + instrumented leakage test harness"
epic: EP-21 Warehouse
phase: 2
component: features
status: todo
ready: true
size: M
autonomy: auto
gate: G-20
depends_on: [DATA-021, FND-007, DATA-000]
areas: [packages/features/**, packages/core/**]
standards: [ml, testing]
assignee:
created: 2026-09-24
completed:
---
# DATA-022 — AsOfReader + instrumented leakage test harness

## Objective
The single sanctioned read path for as-of data, plus the harness proving no future reads [R-60].

## Context to read (only these)
- `docs/standards/data-engineering.md §5`
- `docs/standards/evaluation.md §2`

## Acceptance criteria
- [ ] AC1: AsOfReader(t) filters observed_at <= t for all time-varying tables
- [ ] AC2: Instrumentation records every row's observed_at read; helper asserts max <= t
- [ ] AC3: Import-linter/SQL lint prevents direct reads of time-varying tables from features/models/decision/evaluation
- [ ] AC4: Tests include a deliberately leaky view that the harness catches

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
