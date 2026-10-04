---
id: ANL-002
title: "Category/points value marts"
epic: EP-30 Semantics
phase: 3
component: warehouse
status: todo
ready: true
size: S
autonomy: auto
gate: G-20
depends_on: [ANL-001, DATA-021, DATA-000]
areas: [warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# ANL-002 — Category/points value marts

## Objective
Per-player-game fantasy contributions under the league's rules (ratio components kept separate).

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: mart models + tests; points = sum(stat x modifier) matches Yahoo for sampled games

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
