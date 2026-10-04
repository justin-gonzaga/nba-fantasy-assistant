---
id: DEC-002
title: "Projection distributions (NegBin, makes/attempts) + PIT eval [R-30,R-44]"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: G-14
depends_on: [RSCH-004]
areas: [packages/decision/**]
standards: [ml, evaluation, testing]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DEC-002 — Projection distributions (NegBin, makes/attempts) + PIT eval [R-30,R-44]

## Objective
Calibrated per-stat distributions for simulation.

## Context to read (only these)
- docs/architecture/ml-methodology-plan.md §17 (approved, D-61)

## Pre-registered test (written 2026-09-28, before any result was seen)
- **Data**: player game logs 2023-24, 2024-25, 2025-26 regular season (stats.nba.com, stored snapshots).
- **Unit**: player-week (Monday-Sunday), for players with >= 5 earlier games that season and >= 1 game that week.
- **Mean (shared)**: the player's season-to-date per-game average for each stat, using only games before the week starts.
  Both models use it, so the test isolates the distribution shape. Weekly totals are scored given the games actually played.
- **Baseline**: Poisson per game (the weekly total is Poisson(n·mean)); FG/FT: attempts Poisson, makes Binomial(attempts, season-to-date %).
- **Candidate**: negative binomial per game with one dispersion per stat (method of moments); FG/FT: attempts NB, makes Beta-Binomial with one
  over-dispersion per percentage. All dispersions are estimated on **selection weeks only** (2023-24, 2024-25, and 2025-26 weeks starting before 19 Jan 2026).
- **Holdout**: 2025-26 weeks starting on or after **19 Jan 2026**, untouched until the ship test.
- **Scores**: CRPS per category (exact for counts, Monte Carlo for FG%/FT%); randomized PIT for calibration (the mean absolute deviation of
  the PIT decile histogram from 10 %).
- **Ship rule**: the candidate replaces the baseline if its mean CRPS is lower on **>= 6 of 9** categories with the week-block bootstrap
  95 % CI of the difference below 0 [R-55], **and** its PIT deviation is no worse on average. Either way, the report is committed.

## Acceptance criteria
- [x] AC1: Dispersion estimates per stat and per percentage from the selection weeks, with the method written down
      Verify: packages/models/tests/test_distributions.py; the report's dispersion table
- [x] AC2: Weekly total distributions (baseline and candidate) with exact CRPS for counts and MC CRPS for percentages, and randomized PIT
      Verify: tests with known distributions (Poisson limit, CRPS of a point mass)
- [x] AC3: The pre-registered holdout test is run and its report committed; the rule decides whether the simulation uses NB
      Verify: docs/evaluation/reports/DEC-002-distributions.md

## Test requirements
TDD for the distribution maths; the holdout test is the evaluation.

## Evaluation requirements
The pre-registered test above [R-30, R-31, R-41, R-43, R-44, R-55].

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests + report | test_distributions.py (9): moment estimators recover known NB size and beta-binomial rho; dispersion table in the report (pts r=3.87 … fta r=2.06; rho FG 0.004, FT 0.035) | ✅ |
| AC2 | tests | exact count CRPS = abs error for a point mass; the true model wins; the sample CRPS matches the exact value; randomized PIT uniform under the true model | ✅ |
| AC3 | report | docs/evaluation/reports/DEC-002-distributions.md: **SHIPS**, NB better on 7/9 (all counting stats, CIs below 0), mean PIT deviation 0.0225 → 0.0093; FT% slightly worse (noted, re-test on 2026-27) | ✅ |

## Implementation history
- 2026-09-28: pre-registration committed first (ac54390), then `fantasy_models.distributions`, `fantasy_evaluation.distribution_backtest`, CLI `dist-backtest`. The shipped parameters are used by the daily brief's win probabilities; the full simulation is DEC-003.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- Re-test the percentage component (FT% was slightly worse) on 2026-27 as a fresh holdout.
