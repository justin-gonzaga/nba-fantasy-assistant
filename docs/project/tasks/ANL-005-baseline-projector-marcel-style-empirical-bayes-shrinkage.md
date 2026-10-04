---
id: ANL-005
title: "Baseline projector: Marcel-style + empirical-Bayes shrinkage [R-11,R-13]"
epic: EP-31 Baselines
phase: 3
component: models
status: done
ready: true
size: M
autonomy: auto
gate: G-19
depends_on: [RSCH-004, DRAFT-009]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml]
assignee: claude
created: 2026-09-24
completed: 2026-09-28
---
# ANL-005 — Baseline projector: Marcel-style + empirical-Bayes shrinkage [R-11,R-13]

## Objective
First Projector implementation; the incumbent every model must beat.

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md §14 (approved, D-61)

## Pre-registered test (written 2026-09-28, before any result)
- **Priors**: leak-free pre-season per-game projections (the shipped H1+aging+M1pre method, built as in
  DRAFT-009) for **2023-24, 2024-25 and 2025-26**, each using only earlier seasons + that season's pre-season.
- **Unit**: player-week (Mon-Sun) with a prior and >= 1 earlier game that season; outcome = the week's totals
  given the games played (as in DEC-002).
- **Methods** (per counting stat, and makes/attempts for FG%/FT%):
  - **Baseline (live)**: the frozen prior per game.
  - **Season-to-date only** (reported for context).
  - **Candidate (EB update)**: per-game = (k·prior + season-to-date total) / (k + games so far), with one k per stat
    chosen on the **selection weeks** (2023-24, 2024-25, 2025-26 before 19 Jan) by minimising weekly MAE over a grid
    [R-12]. Percentages blend makes and attempts separately.
- **Holdout**: 2025-26 weeks from **19 Jan 2026**, untouched until the ship test.
- **Metric**: weekly MAE per category; paired week-block bootstrap of the difference [R-55].
- **Ship rule**: the candidate replaces the frozen prior if its MAE is lower on **>= 6 of 9** categories with the
  95 % CI of the difference below 0, and no category is worse by more than 2 %.

## Acceptance criteria
- [x] AC1: `fantasy_models.inseason.update`: the EB blend of prior and season-to-date, per stat, with k chosen by grid
      on selection data only
      Verify: packages/models/tests/test_inseason.py (k=0 → season-to-date; k→∞ → prior; no holdout rows used to pick k)
- [x] AC2: The pre-registered test is run and its report committed; if it ships, the brief's week projection uses it
      Verify: docs/evaluation/reports/ANL-005-inseason-update.md

## Test requirements
TDD for the blend and the k search.

## Evaluation requirements
The pre-registered test above.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | packages/models/tests/test_inseason.py (4): k=0 → season-to-date, k→∞ → prior, weight grows with games, choose_k beats both extremes; `update_long`; k chosen on selection weeks only (inseason_backtest.run) | ✅ |
| AC2 | report | docs/evaluation/reports/ANL-005-inseason-update.md: **SHIPS**, 9/9 categories better (pts MAE 10.68 → 8.95); `week-projection` now blends (test_week_projection.py::test_the_season_so_far_updates_the_projection) | ✅ |

## Implementation history
- 2026-09-28: pre-registered (f6e1775); `fantasy_models.inseason`, `fantasy_evaluation.inseason_backtest`, `fantasy_pipeline.inseason_run` + CLI `inseason-backtest` (leak-free priors for 3 seasons). Wired into the live week projection.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- Measure the early-season gain directly (weeks 2-8) on 2026-27 as it arrives.
