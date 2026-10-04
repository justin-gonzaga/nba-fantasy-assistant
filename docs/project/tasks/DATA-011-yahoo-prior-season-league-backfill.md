---
id: DATA-011
title: "Yahoo prior-season league backfill"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: cancelled
ready: true
size: S
autonomy: auto
gate: none
depends_on: [DATA-004]
areas: [apps/pipeline/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-011 — Yahoo prior-season league backfill

## Objective
Backfill prior seasons of the owner's league (settings, matchups, transactions, final rosters) where accessible.

## Context to read (only these)
- Task file only

## Acceptance criteria
- [ ] AC1: All accessible prior seasons fetched; limitations (no historical FA pools) documented

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
Cancelled 2026-09-24: the owner confirmed the league has no earlier seasons.

## Follow-ups
_None._
