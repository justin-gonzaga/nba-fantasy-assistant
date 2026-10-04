---
id: ML-006
title: "Translation factors + informative priors for cold-start projections"
epic: EP-60 ML
phase: 9
component: models
status: todo
ready: false
size: M
autonomy: auto
gate: G-19
depends_on: [DATA-025, RSCH-003, ANL-005, RSCH-004]
areas: [packages/ingest/**, packages/models/**, warehouse/**]
standards: [ml]
assignee:
created: 2026-09-24
completed:
---
# ML-006 — Translation factors + informative priors for cold-start projections

## Objective
D-40: estimate league translation factors; build draft/age/position priors; EB blending; evaluate by games-played bucket vs the replacement-level baseline.

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
