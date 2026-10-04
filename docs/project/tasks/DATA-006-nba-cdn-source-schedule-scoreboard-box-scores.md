---
id: DATA-006
title: "NBA CDN source: schedule, scoreboard, box scores"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: done
ready: true
size: S
autonomy: auto
gate: G-05
depends_on: [DISC-004]
areas: [packages/ingest/**]
standards: [data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DATA-006 — NBA CDN source: schedule, scoreboard, box scores

## Objective
Ingest the season schedule and completed box scores from cdn.nba.com.

## Context to read (only these)
- `docs/research/nba-data.md`

## Acceptance criteria
- [x] AC1: Schedule snapshot job; box scores for all games final on a partition date
      Verify: test_nba_cdn.py::test_daily_stores_schedule_and_final_box_scores_and_is_idempotent; live `nba-daily` run
- [x] AC2: Contracts + fixture tests
      Verify: test_nba_cdn.py (shape contract raises ContractViolation), test_daily.py, test_cli.py::test_nba_daily_refresh
- [x] AC3: Idempotent re-run for a date
      Verify: the same test: a re-run never re-fetches a stored box score

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + live | 8 new tests pass; live `python -m fantasy_pipeline nba-daily --day 2026-09-26`: schedule 1,274 games (1,206 regular, 20 Oct 2026 to 11 Apr 2027), 2026-27 game logs stored (0 rows, pre-season) | ✅ |
| AC2 | tests | contract test on an unexpected shape; fixture tests | ✅ |
| AC3 | test | re-run: box scores fetched=1, skipped=2 | ✅ |

## Implementation history
- 2026-09-27: MVP piece 1. `fantasy_ingest.nba_cdn` (schedule + final box scores), `fantasy_ingest.daily.refresh` (plus a fresh current-season leaguegamelog snapshot, which the existing staging reads), and the CLI `nba-daily`. DATA-002 is covered by the existing `PacedClient`. Box scores are requested only for final games (the CDN answers 403 for missing files).

## Decisions
_None yet._

## Known issues
- The schedule has 6 NBA Cup knockout placeholder games with blank teams, and each team shows 80 of 82 games until the Cup fills in the last two; daily refreshes pick them up. Games-remaining logic must ignore blank-team games.
- CDN box scores are stored raw only; staging for them comes with DATA-013 (the MVP uses the leaguegamelog staging).

## Follow-ups
_None._
