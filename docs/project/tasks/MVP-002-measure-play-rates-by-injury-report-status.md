---
id: MVP-002
title: "Measure play rates by injury-report status"
epic: EP-12 In-season MVP
phase: 5
component: mvp
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [DATA-007]
areas: [packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# MVP-002 — Measure play rates by injury-report status

## Objective
Replace the placeholder status probabilities with rates measured from our own injury-report history joined to game logs (RSCH-002 fallback), with bootstrap CIs. A thin slice of EVAL-004 + DATA-010.

## Context to read (only these)
- docs/project/STATUS.md (MVP plan)

## Acceptance criteria
- [x] AC1: Report sample: one pre-game report per game day across two seasons, parsed
      Verify: docs/evaluation/reports/MVP-002-availability.md sample table
- [x] AC2: Play rate per status with 95 % CIs; the weekly model uses the measured table
      Verify: the report; test on the loaded table

## Test requirements
TDD; offline tests with fixtures.

## Evaluation requirements
Baselines only (no new ML); anything measured is reported with CIs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | backfill | 327 of 327 regular-season game days (2024-25, 2025-26): the ~5:30 PM ET report stored in bronze (PDF + rows), 0 missing, 0 unparseable | ✅ |
| AC2 | report | docs/evaluation/reports/MVP-002-availability.md: Available 82.7 % (80.7-84.6), Probable 91.8 % (90.1-93.4), Questionable 48.9 % (47.0-50.9), Doubtful 1.1 % (0.2-2.2), Out 0.1 % (0.1-0.2); 25,809 scored rows; stable across both seasons. `fantasy_models.weekly.STATUS_PLAY_PROB` now uses them (test_weekly.py) | ✅ |
| Tests | pytest | test_availability.py (3), test_availability_study.py (2), injury_report backfill test; 196 passed | ✅ |

## Implementation history
- 2026-09-28: `fantasy_evaluation.availability` (outcome join + day-clustered bootstrap), `availability_study` + CLI; `injury_report.fetch_latest(latest=)` keeps the real fetch time as observed_at; `stored_report`. Found and fixed a snapshot-store bug on the way (PR #44).

## Decisions
- MVP plan (owner, 2026-09-27): a daily Telegram brief from tip-off (20 Oct), baselines only.

## Known issues
- 7 % of rows unscored (players with no NBA minutes that season, a few name spellings). Doubtful is effectively Out (1.1 %).
- One snapshot per day (~5:30 PM ET); the Sydney-morning brief sees an earlier report.

## Follow-ups
_None._
