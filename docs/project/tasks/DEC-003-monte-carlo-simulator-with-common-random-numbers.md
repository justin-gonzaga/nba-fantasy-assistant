---
id: DEC-003
title: "Monte Carlo simulator with common random numbers [R-61]"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: G-14
depends_on: [DEC-002, RSCH-004]
areas: [packages/decision/**]
standards: [ml, evaluation, testing]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DEC-003 — Monte Carlo simulator with common random numbers [R-61]

## Objective
Vectorised weekly/season simulation.

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md §18 (approved, D-61)
- docs/evaluation/reports/DEC-002-distributions.md

## Pre-registered test (written 2026-09-28, before any result)
- **Data**: 2025-26 player game logs; **holdout weeks** start on or after 19 Jan 2026 (the same holdout as DEC-002).
- **Matchups**: for each holdout week, 100 matchups of two 10-player teams drawn at random (fixed seed) from that
  week's pool: players with >= 5 earlier games who played >= 1 game that week, ranked in the top 224 by
  season-to-date points per game (a stand-in for rostered players).
- **Means (shared)**: season-to-date per-game averages x games played that week, as in DEC-002.
- **Baseline**: the live normal approximation (brief.win_probs with the DEC-002 variances).
- **Candidate**: Monte Carlo, 2,000 draws per team: NB counts and NB attempts with beta-binomial makes (DEC-002
  parameters), summed per team; P(A wins category) = share of draws A beats B, ties counted as half.
- **Outcome**: the actual winner of each category from the realised weekly totals (a tie = 0.5).
- **Metric**: the Brier score, pooled over the 9 categories [R-40]; reliability table [R-42].
- **Ship rule**: the simulation replaces the normal approximation if the pooled Brier difference (sim - normal)
  has a week-block bootstrap 95 % CI entirely below 0 [R-55]. Either way the report is committed.
- **U14 check**: the Monte Carlo standard error of expected categories won at 2,000 draws, reported.

## Acceptance criteria
- [x] AC1: A vectorised simulator: team category totals from the DEC-002 distributions, P(win) per category,
      expected categories won and P(win the week), with a seed for common random numbers [R-61]
      Verify: packages/decision/tests/test_simulate.py (limits, CRN determinism, symmetry)
- [x] AC2: The pre-registered test is run and its report committed; the rule decides whether the brief uses it
      Verify: docs/evaluation/reports/DEC-003-simulation.md

## Test requirements
TDD for the simulator; the holdout test is the evaluation.

## Evaluation requirements
The pre-registered test above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | packages/decision/tests/test_simulate.py (6): identical teams 50/50, a dominant team wins, TO reversed, same seed = same answer, MC standard error, week-win probability | ✅ |
| AC2 | report | docs/evaluation/reports/DEC-003-simulation.md: 1,200 holdout matchups; pooled Brier difference -0.0001 (95 % CI -0.0003 to +0.0000): **does not ship**; the brief keeps the normal approximation; both well calibrated; U14 MC s.e. 0.027 at 2,000 draws | ✅ |

## Implementation history
- 2026-09-28: pre-registration committed first (8684b8a); `fantasy_decision.simulate`, `fantasy_evaluation.simulation_backtest`, CLI `sim-backtest`. The simulator is kept for joint outcomes and common-random-number comparisons (DEC-004/007/008).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
