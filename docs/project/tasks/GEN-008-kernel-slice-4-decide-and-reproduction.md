---
id: GEN-008
title: "Extract the platform kernel, slice 4: decide, splits, backtest reproduction"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-007]
areas: [packages/**, apps/pipeline/**, pyproject.toml, platform-manifest.yaml]
standards: [software-engineering, testing]
assignee:
created: 2026-09-28
completed: 2026-09-28
---
# GEN-008 — Extract the platform kernel, slice 4: decide, splits, backtest reproduction

## Objective
Move the domain-neutral decision pieces into `dikit.decide` (the lineup MILP over generic slots, the
matchup simulator over generic categories, the move screen contract), split the mixed settings and
gamedate modules (the loader and as-of day logic to the kernel; league/bot fields and the US/Eastern
day stay), and prove the whole extraction changed nothing by reproducing the backtest headlines.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml
- docs/project/tasks/GEN-003-extract-the-platform-kernel-into-packages.md (the slice-1 pattern)

## Acceptance criteria
- [x] AC1: `dikit.decide` holds the slot-assignment optimiser (with a named flex slot) and the category matchup
      simulator (categories passed as a spec); `dikit.settings` holds the base settings loader and
      `dikit.time.calendar` the time-zone day logic. fantasy_decision.lineup/simulate, fantasy_core.settings and
      gamedate keep their APIs as thin NBA bindings; settings.py and gamedate.py leave the manifest's mixed list
      Verify: packages/dikit/tests/test_decide_*.py, test_settings.py, test_calendar.py; `uv run python tools/manifest_check.py --summary`
- [x] AC2: The domain-term test and the dikit import-linter contract still pass
      Verify: `uv run pytest packages/dikit/tests/test_neutral.py`; `uv run lint-imports`
- [x] AC3: No behaviour change: identical golden outputs, and the committed evaluation reports reproduce their
      headline numbers (DRAFT-002/007/008, MVP-002, DEC-002, DEC-003, DEC-007, DEC-008, ANL-005), except the
      DEC-003 CI, which GEN-006 made deterministic. DRAFT-009/010 are out of scope: DEC-008's snake tie-break
      fix changed their rosters (disclosed there)
      Verify: `tools/golden_eval.py` before/after; re-run each report command, `git diff docs/evaluation/reports`

## Test requirements
TDD for new kernel code; moved tests move with their code; existing tests pass unchanged.

## Evaluation requirements
Backtest reproduction is the evaluation.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests + manifest | `uv run pytest packages/dikit/tests/test_decide_assign.py test_decide_simulate.py test_settings.py test_calendar.py`; `tools/manifest_check.py --summary` | 10 new kernel tests pass; settings.py and gamedate.py left the mixed list (mixed 12 -> 10) |
| AC2 | test + command | `test_neutral.py`; `uv run lint-imports` | passed; 4 kept, 0 broken |
| AC3 | golden + report re-runs | `tools/golden_eval.py` before/after; all 9 in-scope report commands re-run (DRAFT-007/008 via `run()` without their warehouse writes), numbers compared token by token against the committed reports | golden 10/10 SAME. 7 of 9 reports: every number reproduced (incl. DEC-003's CI). MVP-002: rates identical, CI bounds shift <= 0.2 pt (GEN-006's cluster sort, expected). DRAFT-007: GBM MAEs and 3 CIs differ by <= 0.03; the pre-refactor code (worktree at a45fe28) gives the same new numbers today, so the drift is from warehouse changes since 25 Sep (DATA-030/031, FND-017), not the refactor; verdicts unchanged. `just ci-local` 375 passed, coverage 93.07 % |

## Implementation history
- 2026-09-28: `dikit.decide.assign` (Candidate(id, value, eligible, available), optional `flex` slot) and
  `dikit.decide.simulate` (Categories/Ratio spec, Side(units), Result(p_win)); fantasy_decision.lineup and
  .simulate are thin NBA bindings with unchanged APIs (only `p_win_week` -> `p_win` and `games=` -> `units=` in one
  test). `dikit.settings.BaseAppSettings` + `load(cls)`; `dikit.time.calendar` (local_date, day_bounds_utc);
  fantasy_core.settings and gamedate bind them. Reports regenerated for AC3 then restored (the committed ones keep
  their hand-written notes).

## Decisions
_None yet._

## Known issues
- The move screen (`moves.best_moves`) stays in fantasy_decision: it is written over NBA player-weeks.
- Ten modules remain mixed (draft_pool, daily, preseason/breakout backtests, breakouts GBM, valuation, brief, cli, warehouse, overrides): a later generalisation task, best driven by what GEN-005 (Sydney housing) actually needs.
- The committed DRAFT-007 report predates later warehouse changes (numbers drift <= 0.03, verdicts same).

## Follow-ups
_None._
