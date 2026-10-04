---
id: DISC-010
title: "Spike: pre-NBA data sources (G League, NCAA, EuroLeague/EuroCup)"
epic: EP-01 Discovery
phase: 9
component: ingest
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [packages/ingest/**, packages/models/**, warehouse/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DISC-010 — Spike: pre-NBA data sources (G League, NCAA, EuroLeague/EuroCup)

## Objective
Find permitted, reliable sources and ID-matching paths for the D-41 leagues.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-40, D-41

## Acceptance criteria
- [ ] AC1: G League via nba_api: endpoints, seasons available, sample fixtures
- [ ] AC2: NCAA: candidate sources with their terms/robots position and rate limits; one permitted source recommended (or documented as unavailable)
- [ ] AC3: EuroLeague/EuroCup public API: endpoints, coverage, terms
- [ ] AC4: Cross-league player ID matching approach (extends D-15), with a coverage estimate for 2025-26 and 2026-27 rookies/signings
- [ ] AC5: Findings in docs/research/pre-nba-data.md

## Test requirements
Findings recorded with sources and access dates.

## Evaluation requirements
n/a

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
