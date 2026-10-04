---
id: DATA-009
title: "stats.nba.com source + resumable historical backfill (3 seasons)"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: M
autonomy: auto
gate: G-05
depends_on: [DATA-002, DISC-003]
areas: [packages/ingest/**, apps/pipeline/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-009 — stats.nba.com source + resumable historical backfill (3 seasons)

## Objective
Backfill player/team game logs and reference data for 2023-24..2025-26 from the home IP.

## Context to read (only these)
- `docs/research/nba-data.md`

## Acceptance criteria
- [ ] AC1: Endpoints from DISC-003 with contracts + fixtures
- [ ] AC2: Resumable via checkpoints; safe to interrupt; pacing per DISC-003
- [ ] AC3: Backfill completed; row counts reconciled against known game counts

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
