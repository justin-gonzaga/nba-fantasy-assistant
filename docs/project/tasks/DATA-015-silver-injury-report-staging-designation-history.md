---
id: DATA-015
title: "Silver: injury report staging + designation history"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: todo
ready: true
size: S
autonomy: auto
gate: G-20
depends_on: [DATA-012, DATA-007, DATA-000]
areas: [warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-015 — Silver: injury report staging + designation history

## Objective
Staging and bitemporal designation history per player-game.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: stg_injury__reports with report timestamp, designation accepted_values, reason; tests

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
