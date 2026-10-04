---
id: DATA-030
title: "Ingest pre-season game logs 2015-16 onward (stats.nba.com, SeasonType=Pre Season)"
epic: EP-15 Draft assistant
phase: 1
component: ingest
status: review
ready: true
size: M
autonomy: auto
gate: G-24
depends_on: [RSCH-007]
areas: [packages/ingest/**, apps/pipeline/**, warehouse/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-26
completed:
---
# DATA-030 — Ingest pre-season game logs 2015-16 onward (stats.nba.com, SeasonType=Pre Season)

## Objective
Backfill pre-season player and team game logs as raw snapshots and stage them in dbt (with game dates, so a pre-draft cutoff can be applied per season). Unblocked by G-24 (D-57): player game logs + per-game box scores (starts), 2015-16 onward.

## Context to read (only these)
- docs/project/architecture-decisions.md D-55, D-56
- docs/evaluation/reports/DRAFT-007-backtest.md

## Acceptance criteria
- [ ] AC1: Pre-season logs for every season 2015-16…2026-27 stored as raw snapshots with observed_at
      Verify: manifest rows + `dbt build`
- [x] AC2: stg model with game_date and starter flag where available; tests for keys/ranges
      Verify: `just dbt build --select stg_nba_stats__preseason_player_game`

## Test requirements
TDD for package code; fixtures, no network in unit tests.

## Evaluation requirements
Rolling origin [R-50, R-51]; bootstrap CIs [R-54]; ship rules pre-registered before running.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | live backfill | `python -m fantasy_pipeline preseason-backfill --root data` → 22 pre-season log snapshots (11 seasons x P/T) + 881 box scores (v3), mirrored to gs://nbafa-hdfo-dev-raw. **2026-27 is not played yet** (exhibitions start in early October): run `preseason-backfill --first 2026-27 --last 2026-27` in draft week (by 17 Oct) | ⏳ (2015-16…2025-26 ✅) |
| AC2 | dbt build | `stg_nba_stats__preseason_player_game` (23,987 player-games, 881 games, 11 seasons), `stg_nba_stats__preseason_starter`, `int_preseason_role` (cutoff 2 days before each opening night; 2020-21 handled by its December opener). Tests PASS; warn: 5 source rows with negative minutes (nulled); starts missing before 2017-18 (the source lists a position for 10+ players per team; `assert_preseason_starts_reliable_from_2017`) | ✅ |
| Checks | just ci-local | 219 passed, coverage 96.90 % | ✅ |

## Implementation history
- 2026-09-26:
  - `nba_stats.league_game_log(..., season_type)` (regular-season keys unchanged) + `box_score_traditional` (v3); `fantasy_ingest.preseason.backfill`; `preseason-backfill` CLI.
  - dbt: v3 source; two staging models and `int_preseason_role`.
  - Found: negative minutes in 5 source rows (nulled, warn test); unreliable starts before 2017-18 (checked against v2 START_POSITION too), set to missing.

## Decisions
_None yet._

## Known issues
- Starts are missing for the 2015-16/2016-17 pre-seasons; DRAFT-008 must handle missing values explicitly (indicator + imputation).
- The 2026-27 pre-season must be fetched in draft week before the final projections.

## Follow-ups
_None._
