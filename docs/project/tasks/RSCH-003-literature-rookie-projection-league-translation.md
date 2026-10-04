---
id: RSCH-003
title: "Literature: rookie/pre-NBA projection and league translation factors"
epic: EP-02 Research
phase: 9
component: docs
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: []
areas: [docs/research/**]
standards: [ml]
assignee:
created: 2026-09-24
completed:
---
# RSCH-003 — Literature: rookie/pre-NBA projection and league translation factors

## Objective
Ground D-40 in literature: college/international-to-NBA translation, draft-position priors, rookie development curves.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-40, D-41

## Acceptance criteria
- [ ] AC1: Search log + findings added to ml-literature-review.md with R-IDs and a quality rating (peer-reviewed / practitioner)
- [ ] AC2: Summary of the translation-factor methods (common-player regression, era/league adjustments) and known pitfalls (selection bias: only players good enough to reach the NBA are observed)
- [ ] AC3: Recommended method + evaluation plan for cold-start projections (metrics by games-played bucket)

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
