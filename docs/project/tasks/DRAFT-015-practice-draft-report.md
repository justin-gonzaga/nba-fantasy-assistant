---
id: DRAFT-015
title: "Draft simulator 3/3: the post-draft report and lessons"
epic: EP-15 Draft assistant
phase: 6
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-28
depends_on: [DRAFT-014]
areas: [apps/web/**, packages/decision/**]
standards: [frontend, design, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DRAFT-015 — Draft simulator 3/3: the report

## Objective
When a practice draft ends, show how the drafted team projects against the room and what to change, so every run
teaches something before 18 Oct. Every number and lesson comes from structured results (no invented text).

## Context to read (only these)
- DRAFT-013/014; `packages/decision/src/fantasy_decision/simulate.py` (the weekly category simulation)

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Draft complete | my roster with prices; $ spent vs value (surplus); category ranks vs the 15 rivals (1–16) from summed category strengths; projected category wins against the room (the share of rivals beaten in each category, summed over 9; season projections, weekly noise not modelled, said on screen); budget pace (spent by sale 50 / 100 / 150 vs the room's average); best buys and overpays | a team with a punted category: that rank is shown as punted |
| Lessons | 3 rule-based lessons from the numbers, e.g. "You spent 41 % on 2 players", "Your FT% ranks 15th: 3 of your top 5 shoot under .700" | a punt build: the punted category shows as intentional, not a weakness |
| Practise again | "Draft again" with the same seed (replay this room) or a new one; past runs listed with their score | storage blocked: still works, no history |
| Sharing | none: practice stays on this device | — |

## Acceptance criteria
- [x] AC1: surplus, category ranks, projected category wins and budget pace are computed correctly for a known
      room.
      Verify: `draftReport.test.ts` (a hand-built room → known ranks, surplus, wins and pace)
- [x] AC2: lessons are produced only by rules from the structured numbers; a punt build never flags the punted
      category.
      Verify: `draftReport.test.ts` › "lessons are rule-based", "punt is intentional"
- [x] AC3: the report page renders on phone and desktop and offers "Draft again" (same / new seed) and history.
      Verify: `DraftReport.test.tsx` + the e2e from DRAFT-014 extended to the report

## Plan
1. `report.ts` (pure): surplus, best buys/overpays, category ranks from summed strengths, projected category wins
   (Σ over categories of the share of rivals beaten), budget pace at sales 50/100/150 vs the room, rule-based
   lessons (spend concentration, weakest non-punted category, pace, surplus, money left), run history.
2. `DraftReport` replaces the done screen; history in localStorage.
3. Tests first; screenshot loop.

## Decisions
- Weekly variance isn't available in the browser (the Python simulation holds it); the report uses season
  projections and says so, rather than inventing a weekly win probability.

## Test requirements
Unit tests on the report maths; Vitest for the page; the §9 screenshot loop.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `draftReport.test.ts` (a hand-built 4-team room: spend, value, surplus, ranks, category wins, pace) | pass |
| AC2 | unit | `draftReport.test.ts` › lessons are rule-based (40 % concentration rule, pace, money left); a punt is never flagged; the 16-team weakest-category lesson | pass |
| AC3 | unit + e2e | `DraftReport.test.tsx` (9 ranks, pace table, 14-player team; history after a second run; draft again); `e2e/draft-practice.spec.ts` (category ranks after sim the rest) | Vitest 296; e2e 192 |

## Implementation history
- 2026-10-03 — Specified (split from DRAFT-013).
- 2026-10-03 — Built `report.ts` (pure) and the report screen (totals, lessons, category ranks with bars, budget
  pace, best buys / overpays, team, history). The screenshot loop found two real problems: (1) a full-page
  screenshot reset the draft to setup: the shell remounted pages across 840 px (fixed separately as WEB-028);
  (2) the report's own lesson said "You finished with $88 unspent" after "Sim the rest": the auto-piloted owner
  bid only to the helper's ceiling while rivals spend down, leaving $45–88 on real values in 20 of 20 rooms.
  The auto-pilot now uses the same spend-down factor (left $0–2 in 20 rooms; new test); the rival-only
  calibration is unchanged (top-50 1.024, spend 99.8 %).

## Decisions (approval)
- G-28 APPROVED (A, A, A), 2026-10-03.

## Known issues
_None._

## Follow-ups
_None._
