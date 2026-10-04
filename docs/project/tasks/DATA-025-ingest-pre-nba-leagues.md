---
id: DATA-025
title: "Ingest pre-NBA league stats + cross-league ID matching"
epic: EP-20 Ingestion
phase: 9
component: ingest
status: todo
ready: false
size: M
autonomy: auto
gate: none
depends_on: [DISC-010, DATA-002]
areas: [packages/ingest/**, packages/models/**, warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-025 — Ingest pre-NBA league stats + cross-league ID matching

## Objective
Sources and backfill for G League, NCAA and EuroLeague/EuroCup per DISC-010.

## Acceptance criteria
_To be refined (ready: false)._

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
Low priority (owner, 2026-09-24): moved to Phase 9. Until then, cold-start players use draft/age/position priors only.

## Follow-ups
_None._
