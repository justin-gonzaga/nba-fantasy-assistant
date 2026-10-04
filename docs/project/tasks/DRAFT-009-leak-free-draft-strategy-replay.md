---
id: DRAFT-009
title: "Leak-free draft strategy replay: our values vs last-season values on 2025-26"
epic: EP-05 Draft
phase: 1
component: evaluation
status: done
ready: true
size: M
autonomy: auto
gate: G-01
depends_on: [DRAFT-008, DEC-007]
areas: [packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, evaluation]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# DRAFT-009 — Leak-free draft strategy replay

## Objective
The owner asked whether drafting by our values actually works. Replaces the hindsight roster table in the
DEC-007 report: rosters are drafted with information available **before** 2025-26, then scored on 2025-26.

## Context to read (only these)
- docs/evaluation/reports/DEC-007-lineup.md (the hindsight caveat)

## Pre-registered test (written 2026-09-28, before any result)
- **Strategies**:
  - **Ours**: values from the shipped projection method (H1+aging+M1pre) with target 2025-26, i.e. using seasons
    up to 2024-25 and the 2025-26 **pre-season** (known before a 2025-26 draft). No 2026 injury overrides.
  - **Baseline**: values from last season's stats (B0, 2024-25 per game), the naive "draft by last year" strategy.
  - Both value with the same league rules (16 teams, 9-cat, the league's slots) and the same valuation code.
- **Pool**: players with a 2024-25 season plus the 2025 draft class (nobody known only from later).
- **Draft**: 40 random seat orders; 16-team snake, 14 rounds; seats alternate Ours / Baseline; each team takes the best
  available player by its own strategy's value.
- **Season**: every 2025-26 regular-season day, each team's lineup is set by the DEC-007 optimiser using its own values;
  a started player with a game-log row that day contributes his actual stats.
- **Score**: weekly **all-play** H2H: each week, each team is compared with every other team in all 9 categories
  (ties = 0.5); a team's score is its share of category wins.
- **Report**: the mean share for Ours minus Baseline, with a 95 % bootstrap CI over the 40 drafts [R-54]; plus the
  share of drafts in which the Ours teams averaged higher. No ship decision: this is an evaluation of the draft model.

## Acceptance criteria
- [x] AC1: Leak-free values for both strategies (history cut at 2024-25; the pool as defined; no overrides)
      Verify: a test that the projection history excludes 2025-26 regular-season rows
- [x] AC2: The draft + season replay + all-play scoring, tested on synthetic data
      Verify: packages/evaluation/tests/test_draft_replay.py
- [x] AC3: The report is committed and the DEC-007 hindsight table points to it
      Verify: docs/evaluation/reports/DRAFT-009-draft-replay.md

## Test requirements
TDD for the replay mechanics; the real run is the evaluation.

## Evaluation requirements
The pre-registered test above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | code + check | `project_pool` asserts no rows from the target season or later (`assert_no_future`); the minutes model uses opening teams, the pool is 2024-25 + the 2025 class, no overrides; leak check in the report: the top-150's 2025-26 games are equal (56.9 vs 56.7) | ✅ |
| AC2 | tests | packages/evaluation/tests/test_draft_replay.py (3): snake order, all-play symmetry, a sensible strategy beats a reversed one | ✅ |
| AC3 | report | docs/evaluation/reports/DRAFT-009-draft-replay.md: ours - last season = **+0.107** all-play share (95 % CI +0.103 to +0.112), ours higher in 40/40 drafts; the diagnosis explains it (injury-season games); DEC-007's table points here | ✅ |

## Implementation history
- 2026-09-28: the owner spotted that the DEC-007 roster table used 2026-27 values on 2025-26 games (hindsight). Pre-registered (3a2535d), then `fantasy_evaluation.draft_replay` + `fantasy_pipeline.draft_replay_run` + CLI `draft-replay` (4.4 min).

## Decisions
_None yet._

## Known issues
- Positions come from current (2026-27) rosters; a player who changed position label since 2025-26 is slightly misclassified.

## Follow-ups
- Repeat against Marcel (B1), a tougher baseline that also shrinks games.
