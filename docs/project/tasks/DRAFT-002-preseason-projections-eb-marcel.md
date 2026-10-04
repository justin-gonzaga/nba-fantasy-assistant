---
id: DRAFT-002
title: "Preseason projections v0: Marcel-weighted, EB-shrunk rates + games played + rookie priors"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: done
ready: true
size: M
autonomy: auto
gate: G-21
depends_on: [DRAFT-001, RSCH-005, DATA-029]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DRAFT-002 — Preseason projections v0: Marcel-weighted, EB-shrunk rates + games played + rookie priors

## Objective
Season projections per player for every stat Yahoo can score: 5/4/3 recency weights [R-13], empirical-Bayes shrinkage of rates [R-11, R-12], an age adjustment, an expected games-played distribution, and a team-change minutes adjustment. Rookies get draft slot/age/position priors (D-40 reduced form).

## Context to read (only these)
- `docs/architecture/ml-methodology-plan.md` §1, §4, §5 (approved, G-21 / D-49)
- `docs/project/architecture-decisions.md` D-42 (draft assistant)

## Acceptance criteria
- [x] AC1: Projections exist for 100 % of the 2026-27 draft pool (`int_player_profile`), with a per-game mean and sd per stat, expected games, and ratio stats projected as makes/attempts
      Verify: `test_projection_schema` + `python -m fantasy_pipeline draft-projections` coverage line
- [x] AC2: Backtest per plan §4: B0 (last season), B1 (Marcel [R-13]) and C1 (EB [R-11, R-12]) on rolling folds (primary Fold A = 2025-26 from ≤ 2024-25). Per-stat MAE, a 9-cat value rank correlation, and paired player-bootstrap CIs [R-54]. The gate picks the shipped method (C1 only if it beats B1 on rank correlation with a CI excluding 0; both must beat B0 on MAE for ≥ 2/3 of stats)
      Verify: docs/evaluation/reports/DRAFT-002-backtest.md (gate amended by G-21b / D-51: H1 candidate, season-total value, rank criterion pooled over folds)
- [x] AC3: No leakage: the backtest build reads no data with season at or after the target season
      Verify: `test_no_future_seasons` (LeakageError on violation)

## Test requirements
Unit tests with fixtures (no network). Property tests where noted. TDD for the package code.

## Evaluation requirements
A backtest report vs the last-season baseline, with CIs. Grounding [R-11, R-12, R-13].

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + live run | `test_projection_schema` (100 % pool, mean + sd per stat, makes <= attempts, pts identity); live `python -m fantasy_pipeline draft-projections --method H1+aging` → `players=589/589 coverage=100.0% rows=8246` → BigQuery `nbafa-hdfo-dev.predictions.preseason_projection` + data/predictions/preseason_projection.parquet | ✅ |
| AC2 | backtest report | docs/evaluation/reports/DRAFT-002-backtest.md: 8 rolling folds 2018-19…2025-26. H1 passes the D-51 gate (11/11 stats better MAE than B0; pooled season-total rank +0.013, 95 % CI +0.006 to +0.020, 8/8 folds). The pre-registered D-52 challenger **H1+aging replaces it and ships** (vs H1: pooled +0.002, 95 % CI +0.001 to +0.003, 8/8 folds; MAE as good or better on 10/11). C1 and B1 alone do not beat B0 (pooled CIs include 0; report's pooled table). Rookie prior beats a league-average rookie on 12/12 stats. 80 % intervals cover 75–85 % | ✅ |
| AC3 | leakage tests | `test_no_future_seasons` (6 functions raise LeakageError when the target season is present) + `test_no_future_seasons_in_rookie_priors_and_pool` | ✅ |
| Checks | just ci-local | 166 passed, coverage 98.92 %, import contracts 3/3 kept | ✅ |

## Implementation history
- 2026-09-25 plan:
  1. `fantasy_models.preseason`: pure Polars/NumPy functions over the `int_player_season` / `int_player_profile` schemas, split into
     - `history_before(target)` guard (LeakageError)
     - B0, B1 Marcel (5/4/3, regression to the mean, Marcel age factor)
     - C1 EB (method-of-moments Gamma–Poisson prior per per-minute stat, Beta–Binomial per shooting %, estimated from our data, U5)
     - aging (delta method with harmonic-mean minute weights, compared by ablation, U6)
     - rookie prior by draft-pick bucket (U4)
     - games and minutes
  2. `fantasy_evaluation.preseason_backtest`: rolling folds, metrics, paired bootstrap over players
  3. `fantasy_pipeline` CLI: `draft-backtest` (reads BigQuery → report) and `draft-projections` (→ `predictions.preseason_projection` + local parquet)
- 2026-09-25: built test-first (a synthetic league with known true rates checks EB recovers prior spreads and beats raw rates).
  - Backtest v1: the gate picked B0. A diagnostic showed the rates are better (with realised minutes: 0.94 vs 0.91) and the 3-year minutes are the weak part.
  - Owner panels (G-21b / D-51): H1 hybrid, season-total metric, pooled folds. v2 → H1 ships.
  - Found in the live insights: old draft picks were feeding rookie priors (a 2015 #5 pick back from Europe). Fixed with `this_draft_pick` (this year's draft only) + a test.

## Decisions
- D-52 (owner: test age; rule pre-registered in commit 0bb557d before running): **H1+aging** ships.
- G-21b / D-51 (owner): ship **H1** = C1 rates × last season's mpg × Marcel games; gate on season-total 9-cat value; rank criterion pooled over folds.
- Priors are league-wide (not position-specific) in v0.

## Known issues
- The fitted age curve is mild (e.g. Durant 5 → 6, Flagg 42 → 33). The delta method underestimates decline because players who decline badly stop playing (survivor bias [R-71]), so treat 35+ players cautiously.
- Games are Marcel-regressed. Players with an injury-shortened last season rise sharply (e.g. 16 → 36 projected games), so the availability-overrides file (D-47 Q2) must cover known long absences before the draft.
- All players in a draft bucket share one rookie line (e.g. picks 1–5); R-78 says outcomes are right-skewed, so this is widened via sd × 1.5 only.

## Follow-ups
1. Survivor-bias-corrected aging (regression + imputation per [R-71]), Part 2.
2. A real minutes model (RSCH-002 literature gap), Part 2.
3. Availability overrides CSV (D-47 Q2) before DRAFT-004.
