---
id: DATA-020
title: "NBA <-> Yahoo player crosswalk + overrides"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: S
autonomy: auto
gate: G-20
depends_on: [DATA-013, DATA-014, DISC-006, DATA-000]
areas: [warehouse/**, packages/ingest/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-020 — NBA <-> Yahoo player crosswalk + overrides

## Objective
dim_player with both IDs; overrides CSV; coverage test.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: Automated matching per DISC-006; overrides seed file
- [ ] AC2: Test: 100% of rostered + top-N FA players mapped (error severity)

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
