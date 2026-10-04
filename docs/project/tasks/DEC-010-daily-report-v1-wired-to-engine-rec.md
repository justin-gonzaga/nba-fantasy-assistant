---
id: DEC-010
title: "Daily brief wired to the engine: two-week add/drop (DEC-008)"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DEC-008, DEC-009]
areas: [packages/decision/**, apps/pipeline/**, apps/api/**, apps/web/src/**]
standards: [ml, evaluation, testing]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# DEC-010 — Daily brief wired to the engine: two-week add/drop (DEC-008)

## Objective
DEC-008 shipped method B: the brief's pickups use the simulation over this week + half of next week whenever next
week's opponent and projection exist; otherwise the this-week rule stays. Recommendation logging stays in EVAL-005.

## Context to read (only these)
- docs/evaluation/reports/DEC-008-moves.md

## Acceptance criteria
- [x] AC1: The week-projection job also writes next week's table (all of next week's games; no injury report)
      Verify: apps/pipeline/tests/test_week_projection.py::test_run_next_projects_next_week_from_the_schedule_without_todays_report
- [x] AC2: `moves.pickups` turns DEC-008's `best_moves` into the brief's pickups (names, games left, gain, helps)
      Verify: packages/decision/tests/test_moves.py::test_pickups_from_the_week_tables_rank_the_two_week_moves
- [x] AC3: The brief uses it when `opponent_next` is in the league file and next week's table exists, and says what
      the gain covers ("this week + half of next"); otherwise the text is unchanged (golden test)
      Verify: apps/pipeline/tests/test_daily_brief.py::test_two_week_pickups_when_next_weeks_opponent_and_table_exist; packages/decision/tests/test_brief.py
- [x] AC4: The API's waivers carry the horizon; the SPA shows it
      Verify: apps/api/tests/test_views.py; apps/web tests

## Test requirements
TDD; golden brief text unchanged on the this-week path.

## Evaluation requirements
DEC-008's replay is the evaluation of the method.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | test_week_projection.py (run_next) | passed (next week 26 Oct-1 Nov, no report) |
| AC2 | test | test_moves.py (pickups) | passed (the strong FA replaces the weak player) |
| AC3 | test | test_daily_brief.py (two-week path), test_brief.py golden | passed |
| AC4 | test | `uv run pytest -q apps/api` (test_views horizon); `just web test` (vitest) | passed; vitest 20 passed; full `just ci-local` 412 passed |

## Implementation history
- 2026-09-28: `week_projection.run_next` + `schedule_frame` helper, NEXT_OUT; `moves.players_from` / `pickups`;
  `Brief.horizon`; `League.opponent_next`; `daily_brief.compose(next_week=...)`, `next_week_table()`; the brief job
  and command pass it; snapshot `horizon`; API `Waivers.horizon`; SPA text. A test run briefly wrote a sample
  next-week table into the real data folder (the jobs test didn't redirect the new path); removed and fixed.

## Decisions
- Next week's table carries no injury report (it describes today), matching DEC-008's replay inputs.

## Known issues
- Until Yahoo's schedule is known, the owner adds `opponent_next` to data/league/league.json each week (or the
  brief stays on the this-week rule).

## Follow-ups
- EVAL-005: log each recommendation and its outcome.
