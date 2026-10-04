---
id: DATA-013
title: "Silver: NBA staging models"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: M
autonomy: auto
gate: G-20
depends_on: [DATA-012, DATA-006, DATA-009, DATA-000]
areas: [warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-013 — Silver: NBA staging models

## Objective
Typed, deduplicated staging of schedule, box scores, game logs, players, teams.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: stg_nba__* models with contracts, PK/range tests, incremental with full-refresh equivalence test
- [ ] AC2: Reconciliation: player points sum = team points

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
