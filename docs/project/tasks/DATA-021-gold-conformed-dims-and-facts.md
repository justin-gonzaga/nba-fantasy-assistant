---
id: DATA-021
title: "Gold: conformed dims and facts"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: M
autonomy: auto
gate: G-20
depends_on: [DATA-020, DATA-015, DATA-000]
areas: [warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-021 — Gold: conformed dims and facts

## Objective
dim_player/team/game, fct_player_game, fct_injury_status, fct_roster_daily, fct_ownership, fct_transaction, fct_matchup_week.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: Models with contracts + relationship tests; bitemporal columns where state varies
- [ ] AC2: Yahoo week-to-date totals reconcile with our recomputation (warn tolerance)

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
