---
id: DISC-006
title: "Spike: NBA <-> Yahoo player ID crosswalk feasibility"
epic: EP-01 Discovery
phase: 0
component: ingest
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [DISC-011, DISC-003]
areas: [docs/research/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DISC-006 — Spike: NBA <-> Yahoo player ID crosswalk feasibility

## Objective
Validate A-05: >=99% of relevant Yahoo players map automatically to NBA person IDs.

## Context to read (only these)
- `docs/research/yahoo-api.md`
- `docs/research/nba-data.md`

## Acceptance criteria
- [ ] AC1: Matching approach (normalised name + team + position, accents/suffixes handled) prototyped on all rostered + top-300 FA players
- [ ] AC2: Match rate and list of failures recorded; overrides file format proposed
- [ ] AC3: A-05 status updated in research doc

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
