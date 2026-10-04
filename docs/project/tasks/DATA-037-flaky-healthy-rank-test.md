---
id: DATA-037
title: "Fix the flaky healthy-rank test (order- and float-sensitive comparison)"
epic: EP-15 Draft assistant
phase: 6
component: pipeline
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [apps/pipeline/tests/**]
standards: [testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DATA-037 — Fix the flaky healthy-rank test

## Objective
CI on main failed once (run 37095951098) in `test_draft_values.py::test_healthy_rank_ignores_projected_games` and
passed on the next runs. The test compares two valuation outputs with `DataFrame.equals`, which is sensitive to row
order and exact float bits; `valuation.value_all` goes through polars group-bys whose row order and summation order
are not guaranteed. The behaviour under test (healthy ranks ignore projected games) is correct; the comparison is not.

## Context to read (only these)
- `apps/pipeline/tests/test_draft_values.py`, `draft_values.healthy_ranks`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| CI on any commit | the test passes every time when the behaviour holds | rows in any order; dollars equal within 1e-9 |
| A real regression (games leak into healthy ranks) | the test still fails | a different rank for the hurt star |

## Acceptance criteria
- [x] AC1: the comparison ignores row order and tolerates float summation noise, but still fails on a real change.
      Verify: `uv run pytest -q apps/pipeline/tests/test_draft_values.py -k healthy` (+ a mutation check: the star's
      rank differs when `healthy_ranks` keeps the projected games)
- [x] AC2: 30 repeated runs pass.
      Verify: `uv run pytest -q apps/pipeline/tests/test_draft_values.py -k healthy_rank_ignores --count 30` or a loop

## Test requirements
Unit only.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit + mutation | `test_draft_values.py -k healthy` pass; with `healthy_ranks` keeping projected games the test fails (1 failed) | pass |
| AC2 | repeat | 30 fresh `pytest -p no:cacheprovider` runs of the test | 30/30 |

## Implementation history
- 2026-10-03 — Specified from the failed main run.
- 2026-10-03 — `assert_frame_equal(check_row_order=False, rel_tol=abs_tol=1e-9)` replaces `DataFrame.equals`.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
