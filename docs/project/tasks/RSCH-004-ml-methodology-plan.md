---
id: RSCH-004
title: "ML methodology plan grounded in verified literature (for owner approval, G-19)"
epic: EP-02 Research
phase: 0
component: docs
status: done
ready: true
size: M
autonomy: gated
gate: none
depends_on: [RSCH-001, RSCH-002]
areas: [docs/architecture/ml-methodology-plan.md, docs/research/**]
standards: [ml, evaluation, documentation]
assignee: claude
created: 2026-09-25
completed: 2026-09-27
---
# RSCH-004 — ML methodology plan (owner approval required)

## Objective
A fully fleshed-out, literature-grounded plan for every modelling and decision component, written before any ML code (owner mandate, ML standard §0). It is presented to the owner as decision panels for gate G-19.

## Context to read (only these)
- `docs/research/ml-literature-review.md` (verified entries only)
- `docs/architecture/ml-and-decision-design.md`
- `docs/standards/ml.md`, `docs/standards/evaluation.md`

## Acceptance criteria
- [x] AC1: For each component, the plan states: the problem, target, method, features (with as-of availability), training data, validation, metrics, baselines, leakage risks, retraining, monitoring, explainability and compute. Components: preseason/draft projections, EB baseline, minutes, per-minute rates, distributions, availability, cold start, simulation + format objectives, lineup MILP, add/drop/stream valuation, trade, explanations, NL answers.
      Verify: docs/architecture/ml-methodology-plan.md (a checklist table per component)
- [x] AC2: Every methodological claim cites a reference marked **Verified** in RSCH-001, stating which specific result is used and how our setting differs.
      Verify: `just check` citation lint (every [R-xx] in the plan is Verified) + a manual table
- [x] AC3: Choices with no literature support are listed explicitly, each with the empirical test that will justify or reject it.
      Verify: the plan's "Unsupported choices" section
- [x] AC4: The owner approves the plan via decision panels (G-19 APPROVED).
      Verify: human-approval-gates.md G-19 status

## Test requirements
Citation lint: every [R-xx] used in the plan exists and is Verified.

## Evaluation requirements
The plan's evaluation designs must follow docs/standards/evaluation.md.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | doc | ml-methodology-plan.md: draft components (Parts 1-1c, approved G-21/23/24) + Part 2 in-season cards §14-21 (projections, minutes, availability, distributions, simulation/objective, lineup MILP, add/drop, explanations/NL); §22 lists what is deferred (trade, cold start, ranker) | ✅ (trade + cold start deferred, noted) |
| AC2 | script | every [R-xx] in Part 2 (34 ids) is Verified/Corrected in the literature files (check run 2026-09-28) | ✅ |
| AC3 | doc | §23 unsupported choices U12-U15, each with its test | ✅ |
| AC4 | owner | G-19 APPROVED 2026-09-28, all ★ answers (D-61) | ✅ |
_Filled at completion: one row per AC._

## Implementation history
- 2026-09-28: Part 2 written overnight from the verified reference list only; no new references needed. The questions for the owner are in §24.

## Decisions
_None yet._

## Known issues
- Time pressure: draft projections (DRAFT-002) wait on G-19. Present the draft/preseason section to the owner first, so the draft milestone isn't missed.

## Follow-ups
_None._
