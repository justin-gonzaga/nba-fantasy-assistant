---
id: DRAFT-010
title: "Leak-free draft replay against Marcel (B1)"
epic: EP-05 Draft
phase: 1
component: evaluation
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [DRAFT-009]
areas: [apps/pipeline/**, docs/evaluation/**]
standards: [ml, evaluation]
assignee: claude
created: 2026-09-28
completed: 2026-09-28
---
# DRAFT-010 — Leak-free draft replay against Marcel (B1)

## Objective
DRAFT-009's follow-up: "last season" was a weak baseline. Marcel also shrinks games toward normal, so it's the
tougher test of whether our values draft better.

## Context to read (only these)
- docs/evaluation/reports/DRAFT-009-draft-replay.md

## Pre-registered test (written 2026-09-28, before any result)
Identical to DRAFT-009 (same leak guards, 40 seat orders, seed 0, all-play scoring) with the baseline strategy
replaced by **Marcel (B1)** values. Report the difference (ours - Marcel) with the bootstrap 95 % CI and the share of
drafts ours wins. No ship decision (evaluation of the draft model).

## Acceptance criteria
- [x] AC1: `draft-replay --baseline B1` runs the same test against Marcel
      Verify: CLI option; a unit test of the baseline choice
- [x] AC2: The report is committed
      Verify: docs/evaluation/reports/DRAFT-010-draft-replay-vs-marcel.md

## Test requirements
Reuses DRAFT-009's tested replay; a test that the baseline method is selectable.

## Evaluation requirements
The pre-registered test above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + CLI | `draft-replay --baseline B1`; apps/pipeline/tests/test_draft_replay_run.py | ✅ |
| AC2 | report | docs/evaluation/reports/DRAFT-010-draft-replay-vs-marcel.md: ours - Marcel = **+0.089** (95 % CI +0.084 to +0.094), ours higher in 40/40 drafts; the gap is role growth (the minutes model + pre-season role); leak check: equal 2025-26 games (56.9 vs 56.8) | ✅ |

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
