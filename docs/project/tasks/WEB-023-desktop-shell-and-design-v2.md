---
id: WEB-023
title: "Design v2: desktop shell (sidebar, breakpoints), number type, visual QA harness"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-017]
areas: [apps/web/**, docs/standards/design-language.md, justfile, .claude/skills/work-task/SKILL.md, docs/research/ux-modern-interface.md]
standards: [frontend, design]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-023 — Desktop shell and design v2

## Objective
The owner: the frontend looks barebones, especially on desktop. Screens (2026-10-03) show the phone column centred at
1280 px with a phone tab bar. Adopt design-language §9 (from the UX research): a real desktop shell, figures in the UI
face, and the screenshot-review loop every later UI task uses.

## Context to read (only these)
- `docs/standards/design-language.md` §9; `docs/research/ux-modern-interface.md` (Proposed additions)
- `apps/web/src/App.tsx` (Shell), `components/ui/TabBar.tsx`, `index.css`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner on a laptop (1280–1600 px) | a left sidebar (brand, 5 destinations with icons, the signed-in account or sample badge at the bottom) and a wide content area | content capped at 1200 px; the active item is clear; keyboard reachable |
| Tablet / small window (840–1199) | the sidebar still shows | no horizontal scroll |
| Phone (< 840) | unchanged bottom tab bar | the sidebar never renders on phones |
| Resizing across 840 px | navigation swaps without losing the page state | — |
| Numbers everywhere | Geist with tabular figures | the mono face only for code |

## Acceptance criteria
- [x] AC1: ≥ 840 px renders a sidebar nav ("Main", 5 links, aria-current) and no bottom tab bar; < 840 px the reverse.
      Verify: `App.test.tsx` › "desktop shell" (matchMedia stub both ways); persona `desktop.spec.ts`
- [x] AC2: the content column is ≤ 1200 px wide at a 1600 px viewport and fills the space at 1280 px.
      Verify: e2e `desktop.spec.ts` (bounding box)
- [x] AC3: stat figures use the UI face with tabular numerals (no `font-mono` on figures).
      Verify: `design.test.ts` › "figures use tabular UI numerals"
- [x] AC4: `just web-screens` captures every route on phone + desktop; the before/after review is recorded.
      Verify: the recipe + Implementation history notes

## Test requirements
Vitest for structure; the persona e2e suite stays green; the §9 visual QA loop with a before/after review.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit + e2e | `App.test.tsx` › desktop shell (WEB-023); `e2e/desktop.spec.ts` | 11/11 pass; desktop-chrome 61 pass |
| AC2 | e2e | `desktop.spec.ts` › content capped at 1200 px (1600 viewport); fills to 1270+ at 1280 | pass |
| AC3 | unit | `design.test.ts` › figures use tabular UI numerals | pass (16 `font-mono` usages → `tabular-nums`) |
| AC4 | recipe + review | `just web-screens` (12 shots, phone + desktop); review below | pass |

## Implementation history
- 2026-10-03 — Specified from the owner's request and the screenshot review. Before (desktop 1280): the 448 px phone
  column centred with the bottom tab bar; Players: three rows of filter chips, cards without stats; detail: chip +
  sentence lists, an orphan FT% cell, monospace figures, category bars below the fold.

- 2026-10-03 — Built: `useMediaQuery` (EXPANDED 840 / LARGE 1200), `Sidebar` (brand, 5 destinations, account at
  the foot; sticky inner column inside a full-height aside), Shell switch (240 px + content; 760 px reading column,
  1200 px for `/players`), `hairline-r`, figures on tabular Geist. `just web-screens` exports `$SCREENS` (PowerShell
  has no inline env). After review: desktop now uses the width with a clear nav; phones unchanged. Remaining
  (WEB-024/025/026): Players still cards + chip rows, the detail sheet still chip lists with an orphan FT% cell, the
  Today home single-column. Vitest 229/229; e2e full suite green on all 3 projects.

## Decisions
- Sample badge stays in page headers only (two on desktop broke the demo persona's single-badge check).
- Tier B because it changes the harness (work-task skill) and a standard (design-language §9).

## Known issues
_None._

## Follow-ups
- WEB-024 Players table + panel; WEB-025 player detail anatomy; WEB-026 home + landing.
