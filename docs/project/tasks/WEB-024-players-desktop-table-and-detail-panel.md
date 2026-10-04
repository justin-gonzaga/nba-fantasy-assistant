---
id: WEB-024
title: "Players on desktop: sortable stat table, compact toolbar, right detail panel"
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
# WEB-024 — Players: desktop table and detail panel

## Objective
On desktop the Players page is a list of mostly empty cards under three rows of filter chips. Per design-language §9:
a sortable data table with the projected stat line, a one-row toolbar, and the player detail in a right panel
(≥ 1200 px).

## Context to read (only these)
- design-language §9 (tables, badges, panel); `apps/web/src/features/players/*`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner drafting on a laptop | a table: #, Player (avatar, name, team · pos, ≤ 3 badges), $, PTS REB AST STL BLK 3PM FG% FT% TO; sortable by any column | 589 rows: paging kept; sticky header; subtle zebra; tabular numbers right-aligned; `aria-sort` |
| Filtering | one toolbar row: search · strategy · position · a Filters popover (badges + signals with counts) | active filters shown as removable chips; URL state unchanged |
| Opening a player | the detail opens in a right panel (≥ 1200 px); the table stays visible and the row highlighted | < 1200 px: the existing sheet; Escape closes; focus returns |
| Phone | today's rows (no table) | — |

## Acceptance criteria
- [x] AC1: ≥ 840 px shows the table; a header click sorts asc/desc with `aria-sort`; numbers right-aligned, tabular.
      Verify: `PlayersTable.test.tsx`
- [x] AC2: filters live in one toolbar with a Filters popover (counts, zero hidden) and removable active-filter chips.
      Verify: `PlayersTable.test.tsx` › "Players desktop toolbar"
- [x] AC3: ≥ 1200 px the detail opens in a right panel; < 1200 px the sheet; keyboard/focus behaviour kept.
      Verify: tests with matchMedia stubs; e2e `draft-prep.spec.ts`
- [x] AC4: the phone layout is unchanged.
      Verify: `just web-e2e` (phone personas)

## Plan
1. `PlayersTable` (≥ 840 px): #, Player (avatar, name, team · pos, row badges), $, the 9 category columns from the
   projection. Header buttons sort; `aria-sort` on the active `th`; a second click flips direction (URL `dir`).
   Category columns sort by fantasy impact (the strength the Sort menu already uses), so FG%/FT% weigh volume and
   TO sorts fewest first; a caption says so.
2. Desktop toolbar: search · Strategy · position segmented · Sort · Filters popover (badge + signal toggles with
   counts, zero hidden unless active); active filters as removable chips under it. URL params unchanged.
3. ≥ 1200 px: the detail renders as a sticky right panel (complementary landmark, not modal), the selected row
   highlighted; Escape / Close closes and focus returns to the row. 840–1199: the existing sheet.
4. Phone: untouched (all existing tests run at phone width).
5. Tests first with matchMedia stubs at 1280 / 1000 / 390; e2e desktop; screenshot loop.

## Test requirements
Vitest; persona e2e green; the §9 visual QA loop with a before/after review.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `PlayersTable.test.tsx` › table columns at 1280; sort + flip + `aria-sort` | pass |
| AC2 | unit | `PlayersTable.test.tsx` › Filters popover (counts, zero hidden, Escape) + removable chip | pass |
| AC3 | unit + e2e | `PlayersTable.test.tsx` › panel at 1280 (focus returns), sheet at 1000; `desktop.spec.ts`, `draft-prep.spec.ts`, `keyboard.spec.ts` | pass |
| AC4 | unit + e2e | `PlayersTable.test.tsx` › phones keep cards + chips; `just web-e2e` iPhone 13 / Pixel 7 | 177 pass |

## Implementation history
- 2026-10-03 — Specified from the owner's request and the screenshot review.
- 2026-10-03 — Built `PlayersTable`, `FiltersPopover` + `ActiveFilters`, `Panel` (non-modal, focuses Close like the
  sheet), `PlayerDetail layout`, direction-aware sort (`dir` in the URL), e2e helpers `playerRows` / `playerDetail` /
  `filterChip` so persona specs run on every layout. axe caught translucent status badges at 4.19–4.42:1 on tinted
  rows → opaque `badge-*` fills (color-mix with the surface). Screens: before — cards under three chip rows; after —
  one toolbar row, a 12-column table with right-aligned tabular figures, the panel beside it. Vitest 235; e2e 177.
- 2026-10-03 — Merged WEB-025 (panel shows the new anatomy). Review PASS; fixed: AC2 Verify line, a URL `dir`
  round-trip test, Escape-ordering comment, and the popover Escape no longer closes the panel (test). `just ci-local`
  exit 0 (573 passed); players vitest 69/69.

## Decisions
- Beside an open panel below 1600 px the table drops the 9 stat columns (#, Player, $ stay; the panel carries the
  line), the master-detail pattern; ≥ 1600 px it keeps every column. Avoids a horizontally scrolling table at 1280.
- Category columns sort by the strength (fantasy impact) the Sort menu already used, not the raw projection;
  a caption says so. TO therefore sorts fewest-first.
- Status badge fills are opaque so contrast holds on any row background (fold into design-language §9 with WEB-026).

## Known issues
_None._

## Follow-ups
_None._
