---
id: WEB-025
title: "Player detail anatomy: percentile bars, stat table, indicator list"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [WEB-023]
areas: [apps/web/**]
standards: [frontend, design]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-025 — Player detail anatomy

## Objective
The detail reads as a list of chips and sentences, the stat grid strands FT%, and the category picture sits below the
fold. Per design-language §9: identity → key figures → one percentile visual (9 categories vs the draft pool) → the
stat line with its 80 % range → indicators as a definition list → badge reasons.

## Context to read (only these)
- design-language §9 (anatomy, indicators); `PlayerDetail.tsx`, `DecisionPanel.tsx`, `format.ts`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| "Is he good, and at what?" | 9 percentile bars (0–100 vs the expected draft pool, from category strengths), the number at the bar end | TOV: a higher percentile means fewer turnovers (labelled); percentiles over in-pool players only; fewer than 20 pool players (the 10-player demo) → the standardized strength bars instead, labelled |
| The projected line | one compact table: G, MIN, PTS, REB, AST, STL, BLK, 3PM, TOV, FG%, FT% (one header row, one value row) | no projection → "No projection yet"; phone: the table scrolls inside its own box, never the page. Per-stat ranges are not in the API (value spread is the Range indicator) |
| Indicators | a definition list: icon + label, one short muted reason | none → section hidden |
| Badges | the chips sit under the name (≤ 3 + "+n" like the rows); their reasons follow the indicators | no badges → "No badges" plus any not-yet-published notes (WEB-018 contract: the owner sees why it is empty) |
| Key figures | Value, Rank, Healthy rank (only when published), Tier in one strip | strategy named under the strip |
| Phone | the same order in the sheet; bars full width | — |

## Acceptance criteria
- [x] AC1: percentile bars for 9 categories computed against in-pool players, TOV inverted and labelled.
      Verify: `percentiles.test.ts` (pure), `PlayerDetail.test.tsx`
- [x] AC2: section order matches §9; a key figures strip ($, rank, healthy rank); no orphan stat cells.
      Verify: `PlayerDetail.test.tsx` (heading order, one stat row)
- [x] AC3: indicators render as a definition list with short reasons; badge reasons follow.
      Verify: `PlayerDetail.test.tsx`

## Test requirements
Vitest; persona e2e green; the §9 visual QA loop with a before/after review.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `percentiles.test.ts` (5), `PlayerDetail.test.tsx` › percentile bars / small pool fallback | pass |
| AC2 | unit | `PlayerDetail.test.tsx` › §9 order + key figures; one row, eleven cells | pass |
| AC3 | unit | `PlayerDetail.test.tsx` › definition list; badges under the name, reasons after indicators | pass |

## Plan
1. `percentiles.ts` (pure) + test: in-pool share at or below; null under 20.
2. `PlayerDetail` rewrite in §9 order: identity (+ badges) → key figures → category profile (percentile bars or
   strength fallback) → projected line table → indicators `dl` → badge reasons; pass `players` from PlayersPage.
3. Tests: heading order, one stat row with 11 cells, dl for indicators, percentile bars with a big fixture.
4. Visual QA loop (`just web-screens`), before/after notes; e2e green.

## Implementation history
- 2026-10-03 — Specified from the owner's request and the screenshot review.
- 2026-10-03 — Built. Before: chip + sentence lists first, a 3-card value grid, a 4-column stat grid with FT% alone
  on its own line, category bars below the fold. After (screens phone + desktop): name with badges → one key-figures
  strip (Value · Rank · Healthy rank · Tier) → category profile (percentile meters vs the pool; strength bars in the
  10-player demo) → one 11-column stat row (fits a 390 px phone) → indicators as a two-column definition list →
  badge reasons. Vitest 240/240; e2e 176 pass (3 projects).

## Decisions
- Small-pool fallback instead of hiding the category picture (the demo has 10 players; hiding would blank it).
- No per-stat 80 % ranges: the API has none; adding them is an API change beyond this task (follow-up if wanted).

## Known issues
_None._

## Follow-ups
_None._
