---
id: RSCH-005
title: "ML methodology plan, draft slice (preseason projections + auction valuation)"
epic: EP-02 Research
phase: 0
component: docs
status: done
ready: true
size: M
autonomy: gated
gate: none
depends_on: [RSCH-001]
areas: [docs/architecture/**, docs/research/**]
standards: [ml, data-engineering, documentation]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# RSCH-005 — ML methodology plan, draft slice (preseason projections + auction valuation)

## Objective
Part 1 of RSCH-004: the full component cards (problem, target, method, features, validation, baselines, metrics, leakage, explainability) for preseason projections, the auction $ valuation, and the live auction helper, grounded only in verified references. Unsupported choices are listed with their empirical tests.

## Context to read (only these)
- docs/research/yahoo-api.md (league settings)
- docs/research/nba-data.md
- docs/research/ml-literature-review.md (verified entries)

## Acceptance criteria
- [x] AC1: Component cards for the preseason projection, the auction $ valuation, and the live auction helper
      Verify: docs/architecture/ml-methodology-plan.md §Part 1
- [x] AC2: Every citation is Verified (including new references from the draft-slice literature search)
      Verify: citation lint + the verification table
- [x] AC3: A backtest design for the draft projections (e.g. build 2025-26 preseason values from 2024-25-or-earlier data vs realised 2025-26)
      Verify: the plan's evaluation section
- [x] AC4: The owner approves via panels (G-21)
      Verify: gates file

## Test requirements
Doc only; citation lint (every [R-xx] is Verified).

## Evaluation requirements
Evaluation designs follow docs/standards/evaluation.md.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | doc | docs/architecture/ml-methodology-plan.md §1–3 | ✅ |
| AC2 | citation lint | every bracketed [R-xx] in the plan has status Verified in ml-literature-review.md (23 refs); R-77 (practitioner) is cited unbracketed as precedent only | ✅ |
| AC3 | doc | plan §4 (Fold A 2025-26 from ≤ 2024-25; baselines B0/B1; paired bootstrap gate) | ✅ |
| AC4 | gate | human-approval-gates.md G-21 APPROVED; D-49 | ✅ |

## Implementation history
- 2026-09-25: Plan Part 1 written; G-21 panels asked.

## Decisions
_None yet._

## Known issues
Deadline: the owner approves by ~27 Sep, so the draft build fits before 15 Oct.

## Follow-ups
_None._
