---
id: WEB-028
title: "Crossing the 840 px breakpoint must not reset the page"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [WEB-023]
areas: [apps/web/**]
standards: [frontend, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-028 — Crossing the 840 px breakpoint must not reset the page

## Objective
Found while capturing DRAFT-015's screenshots: a full-page screenshot (which resizes the viewport) sent an
in-progress practice draft back to its setup screen. Cause: WEB-023's `Shell` returns a different element tree on
each side of 840 px, so crossing it remounts the routed page and every page loses its local state (an open player
sheet, a typed search before it reaches the URL, a practice draft). WEB-023's spec promised "navigation swaps
without losing the page state"; it had no test for it.

## Context to read (only these)
- `apps/web/src/App.tsx` (Shell), `apps/web/src/App.test.tsx` › desktop shell

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner rotates a tablet / resizes the window mid-practice draft | the draft stays where it was; only the navigation swaps (tab bar ↔ sidebar) | crossing several times; crossing during a lot |
| Any page with local state (an open sheet) | stays open across the swap | — |

## Acceptance criteria
- [x] AC1: flipping the 840 px media query keeps the routed page mounted (a practice draft in progress stays in
      its room).
      Verify: `App.test.tsx` › "crossing 840 px keeps the page"
- [x] AC2: the sidebar / tab bar still swap as before (WEB-023 tests unchanged and green).
      Verify: `App.test.tsx` › desktop shell; `just web-e2e`

## Test requirements
Vitest with a controllable matchMedia stub; persona e2e green.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `App.test.tsx` › crossing 840 px keeps the page (a practice draft stays at "Sale 1 of 224" through 1280 → 390 → 1280) | failed before the fix (room lost), passes after |
| AC2 | unit + e2e | `App.test.tsx` › desktop shell (unchanged); `just web-e2e` | Vitest 285; e2e 191 passed + 1 flaky (see Known issues) |

## Implementation history
- 2026-10-03 — Specified from the DRAFT-015 screenshot finding (a full-page screenshot reset the practice draft).
- 2026-10-03 — Test first (a matchMedia stub that changes width and notifies listeners), then `Shell` renders one
  tree for every width: `<main>` stays the second child, the sidebar / tab bar / account lines toggle around it.

## Decisions
_None yet._

## Known issues
- One run of `a11y.spec.ts` › demo build, dark theme › /today failed on Pixel 7 and passed on rerun; 96/96 passed
  with `--repeat-each=8` (iPhone 13 + Pixel 7). Rare and unrelated to this change; watch for it in CI.

## Follow-ups
_None._
