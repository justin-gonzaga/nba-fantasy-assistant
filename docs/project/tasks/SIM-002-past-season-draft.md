---
id: SIM-002
title: "Draft practice on a past season"
epic: EP-17 Season replay
phase: 7
component: web
status: done
ready: true
size: S
autonomy: auto
gate: G-31
depends_on: [DRAFT-015]
areas: [apps/web/**]
standards: [frontend, testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-04
---
# SIM-002 — Draft practice on a past season

## Objective
The practice setup gains a season choice: "This season (2026-27)" or a replay season. A replay draft runs the same
calibrated room on that season's leak-free pre-season values, and the finished draft is kept so the season's
matchups can be played (SIM-004).

## Context to read (only these)
- SIM-001 (data); `apps/web/src/features/draft/{practice.ts, DraftPracticePage.tsx}`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner picks 2024-25 | the room uses 2024-25 pre-season values and names; the report says "2024-25 replay" | the season's data not published → the choice is disabled with why |
| After the draft | "Play the 2024-25 season" opens the matchup simulator with this draft's rosters | the draft is saved in the browser; a new replay draft replaces it after a confirm |
| Calibration | rooms on a replay season still price players like the published values (DRAFT-013 rules) | — |

## Acceptance criteria
- [x] AC1: the setup offers this season and every published replay season; a replay draft runs on that season's
      values and records the season with the result.
      Verify: `DraftPractice.test.tsx` › "replay season"
- [x] AC2: a finished replay draft is saved (league: 16 rosters, season) and offers "Play the season".
      Verify: `DraftReport.test.tsx` › "play the season"

## Plan
1. `features/replay/season.ts`: parse a season file (`GET /replay/{season}`, SIM-001) into draft players
   (id, value, z) and display rows (name, team, position), plus the lookups SIM-004 needs (lines by day,
   weeks). Only the file's pre-season values reach the draft room: no in-season numbers are shown.
2. `features/replay/league.ts`: the saved replay league `{season, rosters by team, savedAt}` in
   localStorage (one at a time), written when a replay draft finishes.
3. Practice setup: a season choice (this season + `GET /replay/seasons`; the three G-31 seasons listed, the
   unpublished ones disabled with why). `Settings.season`; the report names the season; "Play the
   <season> season" links to SIM-004's route (`/replay`), with a confirm before replacing a saved league.
4. Depends on SIM-001's API (PR #121). Its files appear after the first daily run, so until then every
   replay season shows as not published yet (the disabled-with-why case).

## Test requirements
Vitest with a fixture season.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | component | `DraftPractice.test.tsx` › replay season (SIM-002 AC1): published season enabled, unpublished disabled "(not published yet)", the room runs on that season's file ("2024-25 replay · Sale 1 of 224", the file's names), the resume save keeps the season; a failed load says why and stays on setup. Unit: `replay/season.test.ts` (columnar lines, pool, weeks), `league.test.ts` | 2/2 + 5/5 pass |
| AC2 | component | `DraftReport.test.tsx` › a past-season draft (SIM-002 AC2): "Play the 2024-25 season" saves 16 rosters × 14 and opens `/replay`; with a saved league it asks in-page first ("Keep the old one" keeps it) | 2/2 pass; web suite 319/319, eslint + tsc clean; e2e draft + a11y (pixel-7) 23/23 |

## Implementation history
- 2026-10-04 — Specified from the owner's request (season replay).
- 2026-10-04 — Refined: plan; the dependency on SIM-001 is its API (merging), not its first publish.
- 2026-10-04 — Built: `replay/season.ts` (parse, pool, weeks), `replay/league.ts` (saved league), `replay/rows.ts`
  (pre-season rows only: no badges/projection/status, so the draft can't see the season), the season choice in
  setup, the replay pool loaded on start/resume, the season in the room, report and history, "Play the season"
  with an in-page confirm, and a `/replay` placeholder that SIM-004 replaces. Optional `replaySeasons`/
  `replaySeason` on the API client (the demo has none: every replay season shows as not published).

## Decisions
- G-31 APPROVED (all A), 2026-10-04: published per-season files, the browser simulates; daily lineups with
  auto-start; rivals auto-start, no pickups; pickups play from the next day; seasons 2023-24, 2024-25, 2025-26.

## Known issues
_None._

## Follow-ups
- SIM-006 syncs the saved league and the run history to the account (owner, 2026-10-04).
