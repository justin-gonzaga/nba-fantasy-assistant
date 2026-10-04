---
id: DISC-004
title: "Spike: cdn.nba.com schedule & box score coverage"
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
# DISC-004 — Spike: cdn.nba.com schedule & box score coverage

## Objective
Validate A-03: cdn.nba.com schedule and box scores are available for current + previous season games.

## Context to read (only these)
- `docs/research/2026-09-initial-research.md §2`

## Acceptance criteria
- [x] AC1: The scheduleLeagueV2 file is fetched, and the 2026-27 regular-season game count and ID format are recorded.
      Verify: docs/research/nba-data.md §DISC-004 table
- [x] AC2: Box scores for 20 random 2025-26 games and 5 preseason 2026-27 games are attempted, and the availability rate is recorded.
      Verify: same table (20/20 ok; preseason 0/5 because not yet played)
- [x] AC3: A field inventory of the fantasy stats is recorded.
      Verify: docs/research/nba-data.md §fields
- [x] AC4: The cloud test is optional: recorded as not done (no cloud host yet), deferred to INFRA-004.
      Verify: table row "Cloud reachability"
- [x] AC5: Findings are in docs/research/nba-data.md, and the A-03 status is updated.
      Verify: nba-data.md + initial-research A-03 row

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | spike (scratchpad, stdlib urllib), 2026-09-25 | 200; 1,274 games (1,206 regular); IDs 00226xxxxx; first tip 2026-10-20T19:00Z |
| AC2 | command | same run | 2025-26: 20/20 ok (p50 0.54 s); 2026-27 preseason: 5/5 → 403, games scheduled 3–5 Oct (not played) |
| AC3 | report | nba-data.md | all 9-cat + points-league stats present; minutes are ISO-8601 durations |
| AC4 | report | nba-data.md | cloud test deferred to INFRA-004 (no host yet) |
| AC5 | report | nba-data.md, initial-research A-03 | updated |

## Implementation history
### 2026-09-25 — overnight loop
- Attempt 1: every URL → 403. Root cause: the CDN requires browser-style headers (User-Agent, Referer and Origin nba.com). Attempt 2 with the headers: all OK.
- Key finding for the ingest design: the CDN answers **403 for files that don't exist yet**, so 403 alone doesn't mean "blocked". Check the schedule's game status first.
- Attempts: 2. Interventions: none.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- DATA-006: the client must send browser-style headers, and interpret 403 together with the schedule status.
- INFRA-004: verify cdn.nba.com reachability from Cloud Run.
