---
id: DEC-007
title: "Lineup MILP (HiGHS) + legality property tests [R-04]"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: G-14
depends_on: [RSCH-004]
areas: [packages/decision/**]
standards: [ml, evaluation, testing]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DEC-007 — Lineup MILP (HiGHS) + legality property tests [R-04]

## Objective
Daily lineup optimiser using objective weights.

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md §19 (approved, D-61)

## Pre-registered test (written 2026-09-28, before any result)
- **Objective (both methods)**, lexicographic: first the **number of active players who play today**
  (anyone with a game adds counting stats), then the **sum of their value** (the draft G-score total, the
  value the greedy MVP rule uses). Players who don't play or are Out are never active. Slots G×3, F×3,
  C×1, Util×3 with G/F/C eligibility from NBA positions.
  *Amended 2026-09-28 before any code or result: a pure value sum would let the optimiser "win" by
  benching low-value players with games, which isn't a real improvement.*
- **Replay**: every 2025-26 regular-season game day × 16 sample rosters (a snake draft of the top 224 by
  value); "plays today" = the player has a game-log row that day.
- **Rule**: the optimiser ships if (1) its objective (active count, then value) is >= greedy's on **every** replayed roster-day,
  (2) every lineup is legal (no ineligible slot, no slot over capacity, nobody active without a game),
  and (3) it runs in < 1 s per lineup. The report states how often it beats greedy and by how much.

## Acceptance criteria
- [x] AC1: `fantasy_decision.lineup.optimise`: an integer program (SciPy HiGHS) over eligible slots [R-04]
      Verify: packages/decision/tests/test_lineup.py (a case greedy gets wrong; property tests with hypothesis)
- [x] AC2: The replay test is run and its report committed; if it ships, the brief uses it
      Verify: docs/evaluation/reports/DEC-007-lineup.md

## Test requirements
TDD; hypothesis property tests for legality and never-worse-than-greedy.

## Evaluation requirements
The pre-registered replay above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | packages/decision/tests/test_lineup.py: a case greedy gets wrong (1 → 2 active), no-game players never active, Util flexibility, 150 hypothesis rosters: always legal and never worse than greedy | ✅ |
| AC2 | report | docs/evaluation/reports/DEC-007-lineup.md: 2,624 replayed lineups; more active players in 36 (+1 each), same count with more value in 6; worse 0, illegal 0; slowest 10 ms: **SHIPS**; the brief's lineup now uses it | ✅ |

## Implementation history
- 2026-09-28: pre-registration 0aad42e, amended before any result in 738a953 (lexicographic objective). `fantasy_decision.lineup` (SciPy HiGHS MILP + the greedy baseline), `fantasy_evaluation.lineup_replay` (with sample-roster standings the owner asked for), CLI `lineup-replay`; `brief.lineup` now uses the optimiser.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
