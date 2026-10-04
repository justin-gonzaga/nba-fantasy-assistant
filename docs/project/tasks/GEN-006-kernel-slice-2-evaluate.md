---
id: GEN-006
title: "Extract the platform kernel, slice 2: evaluate"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-003]
areas: [packages/**, apps/pipeline/**, pyproject.toml, platform-manifest.yaml, tools/golden_eval.py]
standards: [software-engineering, testing]
assignee:
created: 2026-09-28
completed: 2026-09-28
---
# GEN-006 — Extract the platform kernel, slice 2: evaluate

## Objective
Move the domain-neutral evaluation machinery into `dikit.evaluate`: resampling (bootstrap indices, percentile CIs,
cluster/week-block ratio-of-sums bootstraps [R-55]) and scoring rules (exact and sample CRPS [R-41], randomized PIT
[R-43, R-44], Spearman over a bootstrap axis). Every copy in packages/evaluation and packages/models switches to
them. Ship gates stay domain code: each report pre-registers its own thresholds.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml
- docs/project/tasks/GEN-003-extract-the-platform-kernel-into-packages.md (the slice-1 pattern)

## Acceptance criteria
- [x] AC1: `dikit.evaluate.bootstrap` and `dikit.evaluate.scoring` exist; no bootstrap resampling or scoring-rule
      code is left in the domain packages
      Verify: packages/dikit/tests/test_evaluate_*.py; `grep -rn "rng.integers(0, len(" packages/evaluation/src`: 0 hits
- [x] AC2: The domain-term test and the dikit import-linter contract still pass
      Verify: `uv run pytest packages/dikit/tests/test_neutral.py`; `uv run lint-imports`
- [x] AC3: No behaviour change: on fixed inputs and seeds, every evaluation function that uses them returns
      identical outputs before and after the move
      Verify: a golden comparison script run before and after (outputs equal), recorded in Evidence; `just ci-local`

## Test requirements
TDD for new kernel code; moved tests move with their code; existing tests pass unchanged.

## Evaluation requirements
Golden-value tests: identical outputs on fixed inputs and seeds.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + grep | `uv run pytest packages/dikit/tests/test_evaluate_*.py`; `grep -rn "rng.integers(0, len(" packages/evaluation/src apps/pipeline/src` | 10 passed; 0 hits |
| AC2 | test + command | `uv run pytest packages/dikit/tests/test_neutral.py`; `uv run lint-imports` | passed; 4 kept, 0 broken |
| AC3 | golden script + CI | a golden capture of 10 evaluation outputs (sim, dist, inseason, moves, draft, avail, preseason fold + gate, minutes, breakout) on fixed inputs/seeds, before vs after; `just ci-local` | all 10 SAME; 358 passed, coverage 92.88 % |

## Implementation history
- 2026-09-28: golden capture first. Two runs of the unchanged code differed: the DEC-003 simulation backtest's
  CI changed per run because `group_by("week")` order is arbitrary (other diffs were float summation order,
  1e-16). Fixed first (sort clusters in simulation_backtest and availability), re-captured a stable baseline,
  then moved: `dikit.evaluate.bootstrap` (resample_idx, idx, ci, mean_ci, ratio_ci, clustered_mean_ci) and
  `dikit.evaluate.scoring` (crps_counts/samples, pit_counts/deviation, ranks, spearman); 3 identical
  week-bootstrap copies, 2 ratio bootstraps, 1 mean bootstrap and the preseason helpers removed.

## Decisions
- The neutrality test's term list dropped `stats`: it only existed to catch `nba_stats` (already caught by `nba`) and flagged `from scipy import stats`.
- `tools/golden_eval.py` is kept (domain tool) for GEN-007/008's before/after comparisons. Reviewer: PASS (both notes above were its low findings).

## Known issues
- The sort fix makes DEC-003's reported CI reproducible; its value may differ slightly from the committed report (same point estimate). GEN-008 re-runs the reports.
- preseason_backtest (rolling-origin folds) and breakout_backtest (precision@k, reliability bins) stay mixed.

## Follow-ups
_None._
