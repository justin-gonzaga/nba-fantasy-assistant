---
id: MVP-001
title: "Rest-of-week projections for the daily brief"
epic: EP-12 In-season MVP
phase: 5
component: mvp
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [DATA-006, DATA-007]
areas: [packages/models/**, packages/ingest/**, apps/pipeline/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# MVP-001 — Rest-of-week projections for the daily brief

## Objective
Per player: games left this fantasy week, expected games (base availability or injury status), expected category totals. A thin slice of ANL-003 + ANL-006.

## Context to read (only these)
- docs/project/STATUS.md (MVP plan)

## Acceptance criteria
- [x] AC1: `fantasy_models.weekly.project`: games left, plays today, status today, exp_games and expected totals
      Verify: packages/models/tests/test_weekly.py
- [x] AC2: Injury names map to NBA ids by name + team; unmatched names are reported
      Verify: test_weekly.py::test_unmatched_injury_names_are_reported_not_dropped_silently
- [x] AC3: CLI `week-projection` reads the latest schedule, rosters, injury report and draft projections, and writes data/predictions/week_projection.parquet
      Verify: apps/pipeline/tests/test_week_projection.py; a live run

## Test requirements
TDD; offline tests with fixtures.

## Evaluation requirements
Baselines only (no new ML); anything measured is reported with CIs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | test_weekly.py (6): games left, today, base availability, the status override on its date only | ✅ |
| AC2 | test | unmatched names returned; accents/suffixes/"Last, First" normalised | ✅ |
| AC3 | tests + live | test_week_projection.py (4); live `week-projection --at 2026-10-21T14:00Z`: 589 players, 433 playing that day, games left 1/2/3 = 21/153/415; Jokić 2 games (exp 1.5), Curry 3 (exp 1.8) | ✅ |

## Implementation history
- 2026-09-28: `fantasy_models.weekly`, `fantasy_pipeline.week_projection`, CLI `week-projection`; `nba_cdn.teams` (team id, tricode, injury-report name). Status probabilities are a labelled PLACEHOLDER until MVP-002.

## Decisions
- MVP plan (owner, 2026-09-27): a daily Telegram brief from tip-off (20 Oct), baselines only.

## Known issues
- Base availability = season games / 82 from the draft model; it already includes an average injury rate, so a healthy star shows ~0.75 per game. MVP-002 and later in-season models refine it.
- A-30: the status probabilities are placeholders (MVP-002 replaces them).

## Follow-ups
_None._
