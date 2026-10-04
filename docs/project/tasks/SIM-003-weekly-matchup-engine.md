---
id: SIM-003
title: "Weekly matchup engine: daily lineups, 4 adds a week, 9-cat H2H scoring on real lines"
epic: EP-17 Season replay
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-31
depends_on: []
areas: [apps/web/src/features/replay/**]
standards: [testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-03
---
# SIM-003 — Weekly matchup engine

## Objective
A pure, tested engine that plays one week of a replayed season under this league's rules (Yahoo H2H, 9 categories,
roster G G G F F F C Util Util Util + 4 bench + 3 IL, lineups set daily, **at most 4 acquisitions per week**) and
scores both teams on the players' real game lines that week.

## Context to read (only these)
- `packages/ingest/tests/fixtures/yahoo_import/league_settings_h2h9cat_auction.txt` (roster positions, max acquisitions per week, waiver rules)
- D-69 (G-31 choices: lineup granularity, rival behaviour, waivers)

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner sets a lineup | per day, only players with a game that day score, only if started in an eligible slot | positions F-C fill F or C; a player on two teams that week (traded) |
| "Auto lineup" | each day the best eligible players by projected value start (Yahoo's start-active-players behaviour) | more players with games than slots |
| Owner adds a player | from the undrafted pool (and players rivals dropped); counts against 4 per week; drops one; the add plays from the next day (waivers per G-31) | a 5th add is refused with why; dropping an IL player |
| Scoring | per category weekly totals (FG%/FT% from made/attempted), wins/losses/ties per category, the result like 5-3-1 | TO: lower wins; a tie on equal totals |
| Rival | sets its lineup by the G-31 rule; no hidden information used for the owner's advice | — |

## Acceptance criteria
- [x] AC1: lineup legality: slot eligibility from positions; a started player without a game scores nothing; the
      auto lineup maximises started value per day.
      Verify: `matchup.test.ts` › "slots (SIM-003 AC1)"
- [x] AC2: acquisitions: at most 4 per week, add + drop keeps 14 (+IL), an added player scores from the day the
      G-31 waiver rule allows.
      Verify: `matchup.test.ts` › "acquisitions (SIM-003 AC2)"
- [x] AC3: scoring matches a hand-computed week (category totals, percentages from makes/attempts, TO lower wins,
      ties).
      Verify: `matchup.test.ts` › "scoring (SIM-003 AC3)"

## Test requirements
Pure TypeScript, hand-built fixtures; no network.

## Evaluation requirements
n/a (it replays real results; the hand-checked week is the check).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `apps/web/src/features/replay/matchup.test.ts` › slots: G-F/F-C eligibility, unknown position = Util only; the auto lineup uses augmenting-path matching (a G-F most-valuable player doesn't strand a third G), only players with a game and not benched start | 2/2 pass |
| AC2 | unit | › acquisitions: an add made on day d plays from d+1 (day −1 = from Monday), the dropped player stops scoring; 4 adds allowed, the 5th refused; a rostered/rival player is not a free agent; a dropped player is a free agent again | 3/3 pass |
| AC3 | unit | › scoring: hand-checked two-day week: PTS tie 30–30, REB 16–3 win, FG% 12/21 vs 12/28 win, TO 5–1 loss (lower wins), FT% 0/0 tie; record 2-1-6 | 1/1 pass |

## Implementation history
- 2026-10-04 — Specified from the owner's request (season replay).
- 2026-10-04 — Built `features/replay/matchup.ts` (pure): `eligible`, `autoLineup` (value-ordered augmenting
  paths: optimal for a transversal matroid), `rosterOn`, `addPlayer`, `playWeek`. Lineup value is pre-season
  value only, never the day's actual line (no hindsight). Traded players need nothing special: lines are keyed by
  player and date. IL slots are left to SIM-004's UI (no injury data in the replay file).

## Decisions
- G-31 APPROVED (all A), 2026-10-04: published per-season files, the browser simulates; daily lineups with
  auto-start; rivals auto-start, no pickups; pickups play from the next day; seasons 2023-24, 2024-25, 2025-26.

## Known issues
- No IL handling: the replay file has no injury designations, so every rostered player is bench-or-start.

## Follow-ups
- The 9 categories and TO-lower-wins are a TS copy of the Python decision package's constants (review): if a
  second format is ever replayed, feed them from the published file (ADR-0018 `ScoringObjective`).
