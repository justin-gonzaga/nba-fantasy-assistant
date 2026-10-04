---
id: SIM-001
title: "Season replay data: daily player lines and leak-free draft values per past season"
epic: EP-17 Season replay
phase: 7
component: pipeline
status: review
ready: true
size: M
autonomy: auto
gate: G-31
depends_on: []
areas: [apps/pipeline/**, apps/api/**, apps/web/src/api/schema.gen.ts, packages/evaluation/**, warehouse/**]
standards: [data, testing]
assignee: claude
created: 2026-10-04
completed:
---
# SIM-001 — Season replay data

## Objective
The owner (2026-10-04): practise a draft on a **past season**, then play that season's weekly head-to-head matchups
against the drafted rivals, setting lineups and making up to 4 waiver pickups a week, scored on what really
happened. The warehouse already has every player's game log with dates (2015-16 → 2025-26). This task turns it into
compact, fast-loading files per replay season: the draft values **as they would have been before that season**
(leak-free, the DRAFT-009 replay method) and every player's daily stat lines, plus the league's week calendar.

## Context to read (only these)
- D-69 (G-31 choices); `apps/pipeline/src/fantasy_pipeline/draft_replay_run.py` (leak-free values)
- `warehouse/models/staging/nba_stats/stg_nba_stats__player_game.sql`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner picks "2024-25" | the draft room loads that season's pre-season values and names (no later information) | a player traded mid-season keeps his lines (team per game) |
| A simulated week | every player's lines for the dates in that week load instantly | All-Star break week; the season's first and last weeks (partial); a player who never played (no lines) |
| Size | one season's lines download fast on a phone | ~27k player-games × 9 stats: compressed target ≤ 1 MB per season |
| Privacy | public NBA box scores only; no league data | — |

## Acceptance criteria
- [x] AC1: a pipeline step builds, per replay season, `values` (leak-free pre-season $, ranks, strengths, names,
      positions) and `lines` (player, date, 9-cat stat line incl. FGM/FGA/FTM/FTA) and `weeks` (Monday–Sunday
      matchup weeks of that season); the files carry the season and the method.
      Verify: `test_season_replay.py` (synthetic season → files with the expected shapes; values use only earlier
      seasons)
- [x] AC2: the API serves them read-only (`GET /replay/seasons`; `GET /replay/{season}`: one compact document with
      values, lines and weeks, as the browser always needs all three) with caching headers; unknown season → 404.
      Verify: `apps/api/tests/test_replay.py`
- [ ] AC3: the published files for the G-31 seasons exist in dev and their sizes are recorded.
      Verify: Evidence (sizes, row counts)

## Plan
1. `fantasy_pipeline.season_replay`: leak-free values for each G-31 season (the DRAFT-009 `_leak_free` path with the
   shipped method), names/team/position, daily lines from `stg_nba_stats__player_game`, Mon–Sun weeks (week 1 runs
   from opening night to the first Sunday); a columnar JSON (`replay/<season>.json`).
2. A daily-chain step `season-replay` (optional, like `draft-values`) builds a season only when its file is missing,
   so the cloud job publishes it with no manual upload.
3. API: `GET /replay/seasons`, `GET /replay/{season}` (auth like the other views; long cache).

## Test requirements
Synthetic seasons; leakage test (values for season t must not change when season t's games change); no network.

## Evaluation requirements
n/a (data). The leak-free values reuse the tested replay method.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit + real build | `apps/pipeline/tests/test_season_replay.py` (weeks, columnar lines, positions from that season's rosters, build-once job); a real 2024-25 build against the dev warehouse | 5/5; 2024-25: 699 players (224 valued), 26,306 games, 163 game days, 25 weeks, 1.36 MB raw / 0.24 MB gzip, built in 24 s; top 5 Jokić, Wembanyama, SGA, Davis, Dončić |
| AC2 | API | `apps/api/tests/test_replay.py` (lists published seasons, serves a season with `private, max-age=86400`, 404 for unknown / unpublished / path tricks, sign-in required) | 4/4; OpenAPI + TS types regenerated |
| AC3 | publish | the daily job's new `season-replay` step builds the three seasons on its first run after merge (no manual upload) | pending the next 07:45 run |

## Implementation history
- 2026-10-04 — Specified from the owner's request (season replay).
- 2026-10-04 — Built `season_replay` (pure weeks/compact/positions + the BigQuery build), the optional daily step and
  the `/replay` routes. The first real build left 323 players without a position: the values table already had an
  `nba_position` column (today's profile), so the join put the season's position in `nba_position_right`; fixed to
  prefer that season's rosters (31 left: fringe players on no end-of-season roster; they'll be Util-only in
  SIM-003). 130 pool players have no team: they were projected but didn't play that season (correct).

## Decisions
- G-31 APPROVED (all A), 2026-10-04: published per-season files, the browser simulates; daily lineups with
  auto-start; rivals auto-start, no pickups; pickups play from the next day; seasons 2023-24, 2024-25, 2025-26.

## Known issues
- 31 players (2024-25) have no position: not on any end-of-season roster up to that season; Util-only in the
  lineup engine.
- AC3 completes on the first daily run after merge.

## Follow-ups
_None._
