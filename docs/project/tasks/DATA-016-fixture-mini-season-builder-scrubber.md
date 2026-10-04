---
id: DATA-016
title: "Fixture mini-season builder + scrubber"
epic: EP-21 Warehouse
phase: 2
component: testing
status: todo
ready: true
size: S
autonomy: auto
gate: G-20
depends_on: [DATA-004, DATA-006, DATA-007, DATA-000]
areas: [tools/**, tests/fixtures/**]
standards: [testing, security]
assignee:
created: 2026-09-24
completed:
---
# DATA-016 — Fixture mini-season builder + scrubber

## Objective
`just record-fixture` and a frozen ~30-day mini-season for integration, dbt, eval-smoke tests.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: Scrubber replaces manager/team names, emails, GUIDs; league IDs hashed (test asserts none leak)
- [ ] AC2: Mini-season covers 2 leagues (category + points)
- [ ] AC3: Documented in testing standard §3

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
