---
id: SIM-004
title: "Matchup simulator page: pick a week and opponent, set lineups, make pickups, play it"
epic: EP-17 Season replay
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-31
depends_on: [SIM-002, SIM-003]
areas: [apps/web/**]
standards: [frontend, design, testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-03
---
# SIM-004 — Matchup simulator page

## Objective
After a replay draft, the owner plays the season week by week: choose the week and one of the 15 drafted rivals,
see both rosters and each player's games that week, set lineups (or auto), make up to 4 waiver pickups, then play
the week and see the result day by day, scored on what really happened.

## Context to read (only these)
- SIM-003 (engine), design-language §9

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner picks week 3 vs Team 7 | both rosters with games-this-week counts, the projected category picture, the waiver pool sorted by value with games this week | a week with few games (All-Star break) |
| Making pickups | "Add" on a waiver player → choose who to drop; a counter "2 of 4 adds left this week" | 4 used → adds disabled with why |
| Lineups | auto by default; tap a player to bench/start for a day | an illegal move is refused with why |
| Play the week | the result (e.g. 5-3-1) with category totals and a day-by-day view; the season record updates | replay the same week with different moves (no saved changes until "Keep") |
| Honesty | rivals follow the stated rule (G-31); results are real box scores | — |
| Phone | one column: the matchup summary, then my roster, then waivers | — |
| Owner checks the schedule (owner, 2026-10-04: "some teams play more") | a week grid: each player × Mon–Sun with a mark on game days, games per player, and each side's total starts possible (games that fit the slots); waivers sortable by games left this week; the NBA teams' game counts for the week (e.g. 4 vs 2) | a back-to-back; a traded player (his team on each day); a day already played vs to come |
| Honesty about the future | the schedule comes from **team** game dates, so a player who sat out (injury, rest) still shows a game until that day is played; box scores show only for played days | a player with no line on a team game day = DNP, scored 0 |

## Acceptance criteria
- [x] AC1: choose any week and rival; rosters, games-this-week and the waiver pool render.
      Verify: `MatchupSim.test.tsx` › "choose week and rival"
- [x] AC2: pickups (4 a week, add + drop) and lineup changes go through the engine and refuse illegal moves with why.
      Verify: `MatchupSim.test.tsx` › "pickups", "lineup"
- [x] AC3: playing a week shows the result, category totals and day-by-day, and updates the season record.
      Verify: `MatchupSim.test.tsx` › "play the week"; e2e `season-replay.spec.ts` (phone + desktop, axe)
- [x] AC4: the schedule grid and games counts come from team game dates (no DNP leak); waivers sort by games left;
      the engine's auto lineup starts by schedule, not by who played (a DNP starter scores 0, as in Yahoo).
      Verify: `schedule.test.ts` (team-day schedule, traded player, DNP shows a game); `schedule.test.ts` › "the engine by schedule:
      a scheduled player who sat out still takes the slot"

## Test requirements
Vitest; persona e2e + axe; the §9 screenshot loop.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | component | `MatchupSim.test.tsx` › choose week and rival (both grids, 14 rows, Tue-Sun columns, rival switch, waiver pool with games, games by NBA team); › projections (none before any games, then from earlier games only); › without a saved league | pass |
| AC2 | component + unit | › pickups (4 a week, counter, adds off with why, undo); › lineup (bench / start again, `aria-pressed`); `week.test.ts` (free agents in move order: a dropped-then-re-added player is held; keep carries pickups) | pass |
| AC3 | component + e2e | › play the week (result, 9 categories, day by day, keep → season record + saved); e2e `season-replay.spec.ts` on iphone-13, pixel-7, desktop-chrome with axe (week view and result) | 3/3 pass, 0 serious/critical axe |
| AC4 | unit | `schedule.test.ts` (team-day schedule, DNP still has a game, traded player, team games and names, projections only from earlier games, the engine starts by schedule: a scheduled starter who sat out takes the slot and scores 0) | pass; web suite 334+ pass, eslint + tsc clean |

## Implementation history
- 2026-10-04 — Specified from the owner's request (season replay).
- 2026-10-04 — Added the schedule view (owner: "some teams play more") and AC4; found that SIM-003's auto lineup
  treats "had a line" as "had a game" (leaks DNPs): fixed here by passing the team schedule to the engine.
- 2026-10-04 — Built `schedule.ts`, `week.ts`, `ScheduleGrid.tsx`, the `/replay` page (WIDE). Found and fixed: free
  agents applied drops after all adds (a dropped-then-re-added player showed as free); axe: the sideways-scrolling
  grid must be a focusable named region; week 1 now says there's nothing to project from instead of 0-0-9.
  Screens (§9) checked on pixel-7 and desktop. The draft e2e from SIM-002 now lands on this page.
- 2026-10-04 — Review PASS; fixes: AC4's test reference, removed `season.gamesOn` (counted lines, the DNP-leaking
  way; `schedule.gamesInWeek` replaces it), board regenerated, STATUS updated.

## Decisions
- G-31 APPROVED (all A), 2026-10-04: published per-season files, the browser simulates; daily lineups with
  auto-start; rivals auto-start, no pickups; pickups play from the next day; seasons 2023-24, 2024-25, 2025-26.

## Known issues
- A traded player is assumed on his old team until his first game for the new one (schedule, not hindsight).
- Kept weeks carry pickups forward; replaying an earlier kept week starts from today's roster (practice only).

## Follow-ups
- Saving results to the account: SIM-005/SIM-006 (owner, 2026-10-04: view previous sims when signed in).
