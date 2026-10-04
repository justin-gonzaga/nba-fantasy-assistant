---
id: DISC-003
title: "Spike: stats.nba.com reachability, pacing, endpoints from home IP"
epic: EP-01 Discovery
phase: 0
component: ingest
status: done
ready: true
size: S
autonomy: auto
gate: G-05
depends_on: []
areas: [docs/research/**]
standards: [data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# DISC-003 — Spike: stats.nba.com reachability, pacing, endpoints from home IP

## Objective
Validate that nba_api endpoints needed for history work from the home connection and find safe pacing.

## Context to read (only these)
- `docs/research/2026-09-initial-research.md §2`

## Acceptance criteria
- [x] AC1: The endpoints needed for history work from the home IP: league-wide player game logs, team game logs, active players, team rosters, season per-game stats, the schedule, and advanced box scores.
      Verify: spike run → each endpoint ok (docs/research/nba-data.md table)
- [x] AC2: Success rate and latency measured for 200 requests at 0.6 s and 1.0 s spacing; the recommended pacing is recorded.
      Verify: spike results (100 + 100 requests) in docs/research/nba-data.md
- [x] AC3: The full 3-season backfill time is estimated.
      Verify: docs/research/nba-data.md backfill table
- [x] AC4: Sample payloads are saved as valid-JSON fixtures.
      Verify: packages/ingest/tests/fixtures/nba_stats/*.json (7 files; each parses)
- [x] AC5: The findings are written up.
      Verify: docs/research/nba-data.md §DISC-003

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | spike script (scratchpad, not merged) run via `uv run --no-project --with nba_api`, 2026-09-25 | 7/7 endpoints ok, 0.3–1.7 s each |
| AC2 | command | same run: 100 box-score requests at 0.6 s, 100 at 1.0 s | 100 % success at both; p50 0.68 s vs 0.29 s. Recommend 1.0 s |
| AC3 | report | docs/research/nba-data.md | core history for 3 seasons in minutes; advanced box scores ~80 min |
| AC4 | files | packages/ingest/tests/fixtures/nba_stats/ | 7 fixtures, all parse (ConvertFrom-Json) |
| AC5 | report | docs/research/nba-data.md | written |

## Implementation history
### 2026-09-25 — overnight loop
- Spike script in the scratchpad (discarded, per the spike DoD). Only the fixtures + the research doc are merged.
- The first schedule fixture was truncated mid-JSON (a 400 KB cut). It was rebuilt as the first 2 regular-season dates (44 KB, valid).
- Bonus finding: the 2026-27 regular season is 20 Oct 2026 → 11 Apr 2027 (1,274 games incl. preseason).
- Attempts: 1 (+ the fixture fix). Interventions: none.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
