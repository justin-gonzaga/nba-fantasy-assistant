---
id: WEB-027
title: "Low-minute players sort last in category views (TO, FG%, FT% …)"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [WEB-024, WEB-025]
areas: [apps/web/**]
standards: [frontend, design]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-027 — Low-minute players sort last in category views

## Objective
The owner (2026-10-03): "exclude players who have very few mins from contributing to stuff like ft%, fg%,
turnovers". On the published values (2026-27, all categories) FG%/FT% impact is already volume-weighted (Duren,
Jokić, Giannis top FG%; SGA, Booker, Maxey top FT%), but **TO** rewards not playing: the six best TO players are
ranks 557–589 (Flagler, J. Johnson …), and inside the pool low-usage players (Kornet, Hauser) lead. The owner chose
the display fix (not a valuation change): category views rank only rotation players; $ values are unchanged.

## Context to read (only these)
- `features/players/PlayersPage.tsx` (sorted), `PlayersTable.tsx`, `percentiles.ts`, `format.ts`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Sort by TO (or any category: header click or "Best X") | players in the expected draft pool **and** projected ≥ 20 min/game first, by impact; the rest after them in rank order | both directions keep the rest last; no projection = under the bar |
| Rank, $ and healthy-rank sorts | unchanged | — |
| Table on desktop | a low-minute player's category figures are muted with a tooltip "Under 20 min/game projected" | — |
| Percentile bars | the pool is in-pool players projected ≥ 20 min/game | pool < 20 → strength bars (unchanged rule) |
| Caption | "… players outside the draft pool or under 20 min/game sort last." | — |

## Acceptance criteria
- [x] AC1: category sorts put players outside the draft pool or under 20 projected min/game after everyone else
      (both directions); rank, $ and healthy sorts unchanged.
      Verify: `PlayersPage.test.tsx` › "low minutes" (phone sort select) + `PlayersTable.test.tsx` › "low minutes"
- [x] AC2: the percentile pool excludes players under 20 min/game.
      Verify: `percentiles.test.ts` › "minutes"
- [x] AC3: the table mutes a low-minute player's category figures and says why.
      Verify: `PlayersTable.test.tsx` › "low minutes"

## Test requirements
Vitest; persona e2e green.

## Evaluation requirements
n/a: display ordering only; values untouched.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `PlayersPage.test.tsx` › low minutes (phone, pool + minutes); `PlayersTable.test.tsx` › low-minute players (both directions; rank order untouched) | pass |
| AC2 | unit | `percentiles.test.ts` › leaves players under 20 projected minutes out | pass |
| AC3 | unit | `PlayersTable.test.tsx` › muted figures with the title | pass |

## Implementation history
- 2026-10-03 — Specified from the owner's request; checked on the published values (TO top 6 = ranks 557–589).
- 2026-10-03 — Built (`MIN_MPG`, `inRotation`, partitioned category sort, percentile pool, muted cells, caption);
  rule widened to pool + minutes after the real-data check (Decisions). Vitest 255; e2e green.

## Decisions
- Owner chose the display fix over a valuation change (2026-10-03).
- 20 min/game: a rotation player's floor; one constant (`MIN_MPG`) to tune.
- Real-data check (published 2026-27 values + projections): a minutes floor alone still put fringe players on top
  of TO (Hinson #402, Poulakidas #411 at ~21 min) because turnovers track usage. Requiring the draft pool too gives
  Hauser, Merrill, K. Murray, Hardaway Jr., Hachimura, Barnes: real low-turnover rotation players. FG%/FT% leaders
  unchanged (Duren, Jokić, Giannis / SGA, Booker, Maxey). 345 of 589 players are ≥ 20 min; 14 pool players are
  under it.

## Known issues
_None._

## Follow-ups
_None._
