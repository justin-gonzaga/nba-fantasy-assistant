---
id: EXP-004
title: "Experiment: team/coach context in the pre-season projection"
epic: EP-15 Draft assistant
phase: 7
component: models
status: todo
ready: false
size: M
autonomy: review
gate: G-29
depends_on: [ANL-010]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, testing]
assignee:
created: 2026-10-03
completed:
---
# EXP-004 — Team/coach context in the pre-season projection

## Objective
If ANL-010 says "go", test whether adding the context effects it found (e.g. pace, a new coach, usage freed by a
departing teammate) to the pre-season projection beats **H1+aging+M1** where it matters: the draft. Same
discipline as DRAFT-011/012: one pre-registered variant, a leak-free replay, a ship rule, and the current method
stays unless the rule is met.

## Context to read (only these)
- ANL-010's report (which effects, what sizes); DRAFT-012 (the pre-registration and replay pattern); D-54, D-55
- `docs/architecture/ml-methodology-plan.md` (the amendment this needs: G-29)

## Pre-registration (completed and committed before any run; G-29 approves it)
- **Variant**: exactly the effects ANL-010 found significant, with sizes estimated on seasons ≤ 2024-25 only.
- **Ship rule (superiority)**: on the DRAFT-011 replay with IL replacements (2025-26, leak-free, 40 drafts,
  seed 0), variant − current all-play share has its 95 % CI lower bound **> 0**, and no category's 2025-26
  projection MAE is worse by more than 2 %.
- **Reported, not deciding**: per-stat MAE (all players; movers; players with a new coach); the top-25
  before/after.

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner before a draft | if it ships, values reflect team context and the player detail says why (e.g. "new coach: faster pace, +3 % counting stats") | a player traded after the projection run: context follows the as-of team |
| It doesn't ship | values unchanged; the report explains what was tried and why it lost | — |

## Acceptance criteria
- [ ] AC1: the pre-registration above is completed with ANL-010's numbers and approved (G-29) before the run.
      Verify: commit order in the git log; G-29 APPROVED
- [ ] AC2: the replay runs variant vs current and writes the report with the ship decision by the rule.
      Verify: `docs/evaluation/reports/EXP-004-team-context.md` + a `test_draft_replay_run.py` case
- [ ] AC3: if it ships, explanations come from structured evidence (the context fields), no free text.
      Verify: an API test for the explanation field

## Test requirements
TDD on the adjustment functions with synthetic histories; the replay reuses DRAFT-011's tested logic.

## Evaluation requirements
The pre-registered replay; bootstrap CIs [R-54].

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-03 — Specified; blocked on ANL-010's go/no-go and G-29.
- 2026-10-03 — ANL-010 returned **NO-GO** (no context flag explains ≥ 2 % of the projection's value errors; the
  largest, `moved`, 0.23 %). Not run. Reopen only with new evidence (e.g. a larger sample of seasons, or the
  in-season weekly projections, where role changes are fresher).

## Decisions
_None yet._

## Known issues
- Unlikely before the 18 Oct draft (RSCH-009 → DATA-038 → ANL-010 → G-29 → EXP-004). The in-season weekly
  projections are the next place it could apply.

## Follow-ups
_None._
