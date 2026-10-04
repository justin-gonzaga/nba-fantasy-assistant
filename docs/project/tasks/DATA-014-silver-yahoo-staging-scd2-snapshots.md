---
id: DATA-014
title: "Silver: Yahoo staging + SCD2 snapshots"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: M
autonomy: auto
gate: G-20
depends_on: [DATA-012, DATA-005, DATA-000]
areas: [warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-014 — Silver: Yahoo staging + SCD2 snapshots

## Objective
Staging and SCD2 state history for league settings, rosters, ownership, eligibility, matchups.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: stg_yahoo__* + snp_* with observed_at preserved; tests per standard

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
