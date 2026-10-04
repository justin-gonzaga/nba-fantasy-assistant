---
id: DRAFT-008
title: "Pre-season minutes/starts as a breakout signal (M1/M2 features)"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: review
ready: true
size: M
autonomy: review
gate: G-24
depends_on: [DATA-030, DRAFT-007]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-26
completed:
---
# DRAFT-008 — Pre-season minutes/starts as a breakout signal (M1/M2 features)

## Objective
Add the pre-season features (minutes share, starts, change vs last season's role), using only games before the season-equivalent draft cutoff. Re-run the pre-registered M1 and growth-breakout tests plus the 2025-26 hindsight list.

## Context to read (only these)
- docs/project/architecture-decisions.md D-55, D-56
- docs/evaluation/reports/DRAFT-007-backtest.md

## Acceptance criteria
- [x] AC1: Features respect a per-season pre-draft cutoff (leakage test)
      Verify: dbt test `test_preseason_cutoff` (warehouse/tests)
- [x] AC2: M1 and M2b re-tested under G-24's pre-registered rules; report both outcomes
      Verify: docs/evaluation/reports/DRAFT-008-backtest.md
- [x] AC3: Hindsight 2025-26 growth flags vs actual breakouts
      Verify: same report

## Test requirements
TDD for package code; fixtures, no network in unit tests.

## Evaluation requirements
Rolling origin [R-50, R-51]; bootstrap CIs [R-54]; ship rules pre-registered before running.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | dbt leakage tests | `just dbt build` runs `test_preseason_cutoff` (no pre-season game after opening night − 2 days, per season) and `assert_every_preseason_has_an_opener` (no season silently loses its pre-season); both PASS. `test_add_preseason_features_and_missing_flags` covers unknown starts and players with no pre-season | ✅ |
| AC2 | backtest | docs/evaluation/reports/DRAFT-008-backtest.md (rules from G-24, PR #23). (a) M1 + pre-season vs M1, holdout mpg MAE −0.404 (95 % CI −0.492 to −0.321) PASS; season-total rank +0.020 (95 % CI +0.014 to +0.025), 4/4 folds PASS → **ships**. (b) Growth flags: precision@20 − base +0.135 (95 % CI +0.077 to +0.207), Brier 0.1008 vs 0.1021 → **ship**. Caveat: probabilities above 40 % are overconfident (reliability table) | ✅ |
| AC3 | hindsight | same report: 2025-26 top-20 growth flags hit 6 (Reed Sheppard #1 at 70 %, Ausar Thompson, Keyonte George, Donovan Clingan, Matas Buzelis, Jaime Jaquez Jr.) vs ~2.5 expected; missed Ryan Rollins (#26), Neemias Queta (#41) | ✅ |
| Production | wiring | `H1+aging+M1pre` method + growth predictions (`predictions.growth_probability`) wait for the 2026-27 pre-season (refuses with a clear message until then; `test_preseason_method_needs_the_target_preseason`) | ⏳ draft week |
| Checks | just ci-local | 221 passed, coverage 95.11 % | ✅ |

## Implementation history
- 2026-09-26: Started with the historical part of DATA-030 done (2015-16…2025-26). The CLI claim is blocked only on the 2026-27 fetch, which the backtest doesn't need; production outputs wait for it.

## Decisions
_None yet._

## Known issues
- The opening-night var for 2026-27 must be updated each new season (guarded by `assert_every_preseason_has_an_opener`).
- Growth probabilities above ~40 % are overconfident (observed ~22 %); show them as bands, not literal percentages.
- Production needs the 2026-27 pre-season: run preseason-backfill → dbt build → draft-projections --method H1+aging+M1pre → draft-values → draft-preseason → draft-sheet in draft week.

## Follow-ups
_None._
