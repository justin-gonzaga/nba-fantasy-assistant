---
id: DEC-008
title: "Add/drop/stream valuation + rules"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: G-14
depends_on: [DEC-003, DEC-007, ANL-005, RSCH-004]
areas: [packages/decision/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, evaluation, testing]
assignee: claude
created: 2026-09-24
completed: 2026-09-28
---
# DEC-008 — Add/drop/stream valuation + rules

## Objective
Marginal objective deltas with CRN, rules, horizon blending.

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md §20 (approved, D-61)

## Pre-registered test (written 2026-09-28, before any result)
- **League**: 16 rosters of 14 from a snake draft by the leak-free 2025-26 values (DRAFT-009); rosters stay fixed
  except for the move being tested. Free agents = every other player. Each week, each team faces one opponent
  (a fixed random schedule).
- **Weeks**: 2025-26 weeks starting on or after 19 Jan 2026 whose next week also exists (the holdout).
- **Inputs at the Monday decision** (as of that Monday): per-game projections = the ANL-005 in-season blend of the
  leak-free prior with the season so far; expected games = the team's games that week x the player's share of
  his team's games played so far.
- **Method A (live MVP rule)**: `brief.pickups`: the best single add vs dropping the lowest-value player, by the
  normal approximation, this week only.
- **Method B (§20)**: the top 10 free agents by projected weekly value x the 3 lowest-value rostered players, each
  pair scored with the DEC-003 simulator using common random numbers (one seed per team-week) on expected
  categories won this week + **0.5 x** the same next week (U13; 0.3 and 0.7 reported as sensitivity). No move if
  no pair beats keeping the roster.
- **Realised outcome**: with the move made on Monday, the team's actual weekly totals (all rostered players'
  actual stats that week, the added player's instead of the dropped one's) against the week's opponent's actual
  totals: categories won minus categories won without the move; next week likewise, weighted 0.5.
- **Metric**: mean realised gain per team-week; week-block bootstrap 95 % CI [R-55].
- **Ship rule**: B replaces A if B's mean realised gain minus A's has a CI entirely above 0. Either way the report
  (with both methods' gains vs no move) is committed.

## Acceptance criteria
- [x] AC1: `fantasy_decision.moves.best_moves`: pairs scored by simulation with common random numbers, the horizon
      weighting, and "no move" when nothing helps
      Verify: packages/decision/tests/test_moves.py (a clearly helpful add is found; a useless one isn't; CRN determinism)
- [x] AC2: The replay is run and its report committed; the rule decides which method the brief uses
      Verify: docs/evaluation/reports/DEC-008-moves.md

## Test requirements
TDD for the move scoring; the replay is the evaluation.

## Evaluation requirements
The pre-registered test above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest packages/decision/tests/test_moves.py` | 5 passed (helpful add found; useless one not; CRN determinism; next-week discount; below-replacement values don't favour idle players) |
| AC2 | report | docs/evaluation/reports/DEC-008-moves.md (`python -m fantasy_pipeline moves-replay`) | B ships: B - A = +0.2202 categories per team-week (95 % CI +0.0554 to +0.3608); A +0.345, B +0.565 vs no move; sensitivity 0.3/0.7: +0.572/+0.580 |

## Implementation history
- 2026-09-28: first run gave B exactly 0.0000: candidate ranking by value x games put idle free agents first (their values are negative). Fixed with a normal-approximation screen + regression test; disclosed in the report. Then A's result varied across runs (0.38/0.34/0.32): the snake draft broke exact value ties by row order; fixed (ties to lowest id) + test in test_draft_replay.py; final run on deterministic rosters.
- 2026-09-28: pre-registration committed (6f41bc4) before any code or result. `moves.best_moves` (TDD, 4 tests); `fantasy_evaluation.moves_replay` (5 tests: category scoring, realised gain, schedule, no-lookahead inputs, a synthetic replay); `moves-replay` CLI command. Interpretation recorded: method A moves only when its own estimated gain is > 0 (the brief shows pickups but would not advise a negative one).

## Decisions
- Method B ships by the pre-registered rule. Live wiring moves to DEC-010 (needs next week's projection and opponent; the Yahoo schedule isn't released).

## Known issues
- Reviewer (PASS): CRN is partial (numpy rejection samplers shift streams); 1,000 draws without a measured SE (U14); zero-games-so-far players get 0 expected games. Disclosed in the report; revisit at DEC-010 wiring.
- B moved in 100 % of team-weeks; Yahoo's weekly add limit and waiver priority are not modelled, so the live rule may need a minimum-gain threshold.
- The result is one drafted league; the CIs cover week-to-week noise, not other drafts (A ranged 0.32-0.38 across tie orders).
- The snake tie-break fix changes DRAFT-009/010 rosters slightly; their headline numbers were not re-run.

## Follow-ups
- DEC-010: wire `moves.best_moves` into the brief.
- Re-run DRAFT-009/010 with the deterministic tie-break: done 2026-09-28 (DRAFT-009 identical; DRAFT-010 +0.089 -> +0.090, same verdict).
