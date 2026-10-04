---
id: GEN-007
title: "Extract the platform kernel, slice 3: methods"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-006]
areas: [packages/**, apps/pipeline/**, pyproject.toml, platform-manifest.yaml]
standards: [software-engineering, testing]
assignee:
created: 2026-09-28
completed: 2026-09-28
---
# GEN-007 — Extract the platform kernel, slice 3: methods

## Objective
Move the domain-neutral statistical methods into `dikit.methods`: empirical-Bayes shrinkage and the
prior/data blend (choose k), ridge and class-weighted logistic, count distributions (NB size,
beta-binomial, CDF/sampling), delta-method aging. NBA stat names and constants stay in fantasy_models.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml
- docs/project/tasks/GEN-003-extract-the-platform-kernel-into-packages.md (the slice-1 pattern)

## Acceptance criteria
- [x] AC1: `dikit.methods` provides count distributions (counts), EB priors + blend + choose_k (shrinkage) and
      ridge/logistic (regression); fantasy_models imports them and keeps only NBA parameters (NB_SIZE, MAKES_RHO,
      K_SHIPPED) and NBA-shaped code
      Verify: packages/dikit/tests/test_methods.py; packages/models tests
- [x] AC2: The domain-term test and the dikit import-linter contract still pass
      Verify: `uv run pytest packages/dikit/tests/test_neutral.py`; `uv run lint-imports`
- [x] AC3: No behaviour change: identical evaluation outputs on fixed inputs
      Verify: `uv run python tools/golden_eval.py` before/after `--compare`; `just ci-local`

## Test requirements
TDD for new kernel code; moved tests move with their code; existing tests pass unchanged.

## Evaluation requirements
Golden-value tests on fixed inputs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest packages/dikit/tests/test_methods.py packages/models` | 7 new kernel tests passed; model tests pass via dikit |
| AC2 | test + command | `uv run pytest packages/dikit/tests/test_neutral.py`; `uv run lint-imports` | passed; 4 kept, 0 broken |
| AC3 | golden + CI | `tools/golden_eval.py` before vs after | 10/10 SAME; `just ci-local` 365 passed, coverage 92.94 % |

## Implementation history
- 2026-09-28: an AST-based move of whole top-level blocks (MAX_SIZE, nb_size, betabin_rho, weekly_size, count_cdf,
  sample_makes, sample_counts; K_GRID, blend, choose_k; RatePrior, PctPrior, fit_rate_prior, fit_pct_prior;
  NEWTON_TOL, Regressor, Ridge, Logistic). Domain vocabulary neutralised in the kernel: games -> units,
  weekly_size -> total_size, choose_k(week_games, week_actual) -> (next_units, next_actual) (no keyword callers).
  An alias clash (`cn` was already a local variable in distribution_backtest) was caught by mypy.

## Decisions
_None yet._

## Known issues
- `inseason.update_long` re-implements the blend formula in polars (long format) instead of calling `shrinkage.blend`; same formula, left as is.
- Delta-method aging (`fit_aging`) stays in fantasy_models: it is written over the season DataFrame (ages, seasons), not a generic array API; extracting it needs a redesign, not a move. Reviewer: PASS.
- GBM stays in fantasy_models (it would add an optional LightGBM dependency to the kernel); valuation.py (z/G-score) is still mixed.

## Follow-ups
_None._
