---
id: DRAFT-007
title: "Minutes-per-game model + breakout probability (D-53)"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: done
ready: true
size: M
autonomy: review
gate: G-23
depends_on: [DRAFT-002, RSCH-006]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, warehouse/**, docs/evaluation/**]
standards: [ml, testing, evaluation]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DRAFT-007 — Minutes-per-game model + breakout probability (D-53)

## Objective
Make the draft model anticipate role changes and breakouts. Build:
1. a pre-season minutes-per-game model that replaces last season's mpg in H1+aging if it wins the rolling backtest
2. a per-player breakout probability for the cheat sheet

The methods follow the G-23 plan amendment (verified refs from RSCH-006).

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md (§1, §4, §4a, and the G-23 amendment)
- docs/research/lit-breakouts.md
- docs/evaluation/reports/DRAFT-002-backtest.md

## Acceptance criteria
- [x] AC1: Every feature is built only from data before the target season (team membership = first game of season t); a leakage test raises `LeakageError` on violation
      Verify: `test_no_future_features`
- [x] AC2: Ridge and LightGBM minutes models are compared on folds 2018-19…2021-22 (pooled mpg MAE picks one). The winner is judged on 2022-23…2025-26 by the M1 ship rule (§7): MAE CI vs last-season mpg, and the season-total rank of H1+aging with M1 minutes vs H1+aging
      Verify: docs/evaluation/reports/DRAFT-007-backtest.md §Minutes
- [x] AC3: The breakout probability (logistic, class-weighted) is scored on rolling folds: base rate, precision@20/@50 with pooled CIs, cumulative gain, Brier vs a base-rate forecast, and a reliability table; sensitivity at 30/50/80 places; ship rule §8 applied
      Verify: same report §Breakouts
- [x] AC4: **Owner hindsight check**: the 2025-26 top-20 breakout flags from a model trained on <= 2024-25 data only, listed next to the actual 2025-26 breakouts (hits and misses)
      Verify: same report §Hindsight 2025-26
- [x] AC5: If a ship rule passes, the draft projections/values are regenerated with M1 minutes and/or breakout probabilities; if not, nothing changes and the report says why
      Verify: `predictions.preseason_projection` model_version + report decision

## Test requirements
TDD for the package code; fixtures, no network.

## Evaluation requirements
Rolling origin [R-50, R-51]; paired bootstrap CIs [R-54]; ship rules pre-registered in the G-23 amendment before running.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | leakage test | `test_no_future_features` (LeakageError when the target season is in history; the opening roster is a separate input, U10) | ✅ |
| AC2 | backtest | docs/evaluation/reports/DRAFT-007-backtest.md §M1. Selection 2018-22: ridge 3.819 vs LightGBM 3.852 mpg MAE → ridge. Holdout 2022-26: (a) mpg MAE vs last season −0.259 (95 % CI −0.377 to −0.138) PASS; (b) H1+aging+M1 vs H1+aging season-total rank +0.012 (95 % CI +0.007 to +0.018), 4/4 folds PASS → **M1 ships** | ✅ |
| AC3 | backtest | same report §M2a/§M2b. M2a (all players) passes: precision@20 − base +0.194 (95 % CI +0.126 to +0.271), Brier 0.0969 vs 0.0998. But 22/28 of its holdout top-20 hits were players returning from injury, so per the owner (D-55) it's shown as **bounce-back chance**. M2b growth test (pre-registered D-55, played >= 60 % of games) **fails**: +0.041 (−0.011 to +0.108), Brier 0.1031 vs 0.1021 → no growth flags. Sensitivity at 30/50/80 and reliability tables are in the report | ✅ |
| AC4 | hindsight | same report §Hindsight 2025-26. Trained on <= 2024-25 only. The bounce-back model's top 20 hit 6 (Brandon Miller, Zion Williamson, Chet Holmgren, Paul Reed, Tre Jones, Immanuel Quickley), all returning from injury. It missed role breakouts (Reed Sheppard, Collin Gillespie, Ryan Rollins, Neemias Queta, Jay Huff) | ✅ |
| AC5 | live outputs | `draft-projections` (default H1+aging+M1) → 589/589; `draft-values` → Wembanyama $74, Jokić $63, SGA $63; `predictions.breakout_probability` 468 rows, kind=bounce_back only | ✅ |
| Checks | just ci-local | 202 passed, coverage 97.48 %, contracts 3/3 | ✅ |

## Implementation history
- 2026-09-26:
  - `int_player_season` gained `first_nba_team_id` (the opening-roster proxy).
  - `fantasy_models.preseason.breakouts`: features, Ridge, LightGBM (native API; scikit-learn isn't in the approved stack), and a prior-corrected class-weighted logistic regression.
  - `fantasy_evaluation.breakout_backtest` and `breakout_report`.
  - `python -m fantasy_pipeline draft-breakouts`; the M1 method is wired into `draft-projections` and `draft-values`.
  - The first run showed M2's hits were mostly bounce-backs. The owner chose D-55, and the growth test was pre-registered (commit 71b5ed8) before it ran; it failed.

## Decisions
- D-54 (G-23): ridge vs LightGBM selection on early folds, ship rule on later folds. LightGBM had a lower holdout MAE, but ridge won the pre-registered selection, so ridge ships (not switched after seeing the holdout).
- D-55: M1 ships; M2 shows as bounce-back chance; growth flags only if the pre-registered test passes (it didn't).

## Known issues
- Genuine role/skill breakouts aren't predictable beyond chance from box-score history alone (M2b). Candidate signals for later: depth-chart/news, contract/role announcements (ties to the news research).
- M2a's high-probability bins are overconfident (few players); probabilities above 40 % should be read as "high", not literally.

## Follow-ups
_None._
