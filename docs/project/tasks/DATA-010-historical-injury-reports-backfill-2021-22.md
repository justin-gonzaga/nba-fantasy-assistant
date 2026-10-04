---
id: DATA-010
title: "Historical injury reports backfill (2021-22+)"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [DATA-007]
areas: [apps/pipeline/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-010 — Historical injury reports backfill (2021-22+)

## Objective
Backfill all archived injury report versions for availability-model training.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: All available report versions for 2021-22..2025-26 stored and extracted
- [ ] AC2: Coverage report (reports/day, gaps) written to docs/research/nba-data.md

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
