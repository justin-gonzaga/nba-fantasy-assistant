---
id: DRAFT-016
title: "Draft practice: headshots, glanceable signals, recommendations, every roster"
epic: EP-15 Draft assistant
phase: 6
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DRAFT-015]
areas: [apps/web/**]
standards: [frontend, design, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DRAFT-016 — Draft practice: glanceable, roster-aware advice

## Objective
The owner (2026-10-03): "include profile pictures in the player, signals/indicators I can read easily within the
time pressure. For the draft assist, we should be recommending players based on the current players we have."

The engine already adapts to the roster: after every sale `categoryWeights` re-weights the 9 categories from the
owner's players (strong categories count less, weak ones more, a punt counts zero) and each player's fit moves his
ceiling by up to ±25 % and re-ranks the targets. None of that is visible. This task makes the practice room
readable in two seconds: a headshot, the verdict ("Bid up to $34"), why (fits your needs / overlaps your team), and
the player's badges, plus a live "Your needs" panel.

Added the same day: "the UI should let me easily see each team's roster" and "recommendations of who to pick
during the draft sim" — so recommendations are visible on every lot, not only on the owner's nomination turn.

## Context to read (only these)
- `apps/web/src/features/draft/{live.ts, practice.ts, DraftPracticePage.tsx}`; design-language §9

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| A lot opens, 20 s on the clock | headshot, name, team · pos; a big verdict "Bid up to $X" (your ceiling) with a coloured state: green "Good buy" while the price is ≤ 85 % of the ceiling, amber "Near your limit" up to the ceiling, grey "Pass" above it or when you can't afford him | ceiling 0 (no money / roster full) → "You can't bid"; a punt build |
| Why this verdict | one line: "Fits your needs: REB, BLK" (his strongest categories that are among your needs) or "Overlaps your team: PTS" (strong where you're already strong), from the engine's fit (> 1.03 fits, < 0.97 overlaps, else "Neutral fit") | a player strong in a punted category: that category is never listed as a need |
| His signals | up to 3 badges (injury prone, breakout chance, missed time, adjusted …) as on Players | none → no row |
| Your needs (live) | a panel listing your 3 neediest categories (highest weights) and your strongest 2 ("covered"), updating after each sale; before any pick: "Draft anyone: no needs yet" | a punt shows as "Punted: FT%" |
| Your targets / nomination ideas | headshots and the same fit line per player, so the list explains itself | — |
| "Who should I get?" during any lot | a "Recommended for you" panel, always visible: the top 5 available targets with headshot, ceiling and fit line; on a lot for someone else: "If you pass: next best is X, up to $Y" | the player on the block is excluded from "if you pass"; no money left → "You're done buying" |
| "What has everyone got?" | every rival row opens their roster (headshot, name, price) in place; one team open at a time; my own team as before | an empty roster → "No players yet"; keyboard: the row is a button with aria-expanded |
| Your team, recent sales | headshots | missing image → initials (Avatar's fallback) |
| Phone | the verdict and bid buttons stay above the fold; the needs panel collapses to one line under the budget | — |
| Accessibility | the verdict is text (colour is never the only signal); headshots are decorative (alt="") | — |

## Acceptance criteria
- [x] AC1: the lot shows a headshot, the verdict with its state (good buy / near limit / pass / can't bid), the fit
      line and up to 3 badges; the state follows the price vs the ceiling.
      Verify: `DraftPractice.test.tsx` › "glanceable lot" (each state)
- [x] AC2: `needs()` (pure) returns the 3 neediest non-punted categories and the 2 strongest from the engine's
      weights; `fitLine()` names a player's best categories among the needs, or the overlap; the panel updates
      after a sale.
      Verify: `practice.test.ts` › "needs follow the roster", "fit line"
- [x] AC3: targets, nomination ideas, my team and recent sales show headshots and (for targets/ideas) the fit line.
      Verify: `DraftPractice.test.tsx` › "targets explain themselves"
- [x] AC4: phone keeps the verdict and bid buttons above the fold at 390 × 844; axe clean.
      Verify: e2e `draft-practice.spec.ts` (bounding box) + `a11y.spec.ts` draft room

- [x] AC5: the "Recommended for you" panel shows the top 5 available targets (headshot, ceiling, fit line) on every
      lot and nomination, and a lot shows the next best target if you pass.
      Verify: `DraftPractice.test.tsx` › "recommendations on every lot"
- [x] AC6: each rival row opens that team's roster (players and prices); the toggle is a button with aria-expanded.
      Verify: `DraftPractice.test.tsx` › "rival rosters"

## Test requirements
Vitest (pure helpers + page); persona e2e + axe; the §9 screenshot loop.

## Evaluation requirements
n/a (presentation of existing advice; the numbers are the engine's, parity-tested in DRAFT-013).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `DraftPractice.test.tsx` › glanceable lot (headshot, verdict text + state, fit line); `practice.test.ts` › verdict (good / near / pass / can't) | pass |
| AC2 | unit | `practice.test.ts` › needs follow the roster, fit line; `DraftPractice.test.tsx` › needs panel fills once you own players | pass |
| AC3 | unit | targets / ideas / recommendations use `PickRow` (headshot + fit line + ceiling); team and recent sales show headshots | pass |
| AC4 | e2e + axe | `draft-practice.spec.ts` (verdict and bid button inside the viewport on iPhone 13, Pixel 7, desktop); `a11y.spec.ts` › draft room | 192 e2e pass |
| AC5 | unit | `DraftPractice.test.tsx` › recommendations on every lot (5, the lot's player excluded) and "If you pass: next best …" | pass |
| AC6 | unit | `DraftPractice.test.tsx` › each rival opens its roster (button, aria-expanded, roster list) | pass |

## Implementation history
- 2026-10-03 — Specified from the owner's request. Thresholds (85 % good buy; fit 0.97/1.03) are presentation
  choices, adjustable.
- 2026-10-04 — Built: pure `needs` / `fitLine` / `verdict`; the lot card (headshot, badges, verdict block, fit line,
  "If you pass"), "Recommended for you" on every lot, a live "Your needs" panel, headshots in every list, rival
  rows that open their rosters; panels are now labelled regions. Screens: the first layout put recommendations
  at the bottom of a long right column; moved under the lot (left), leaving needs, team, rivals and sales right.
  Before any purchase every fit reads "Neutral fit" (all weights 1), which is accurate. Vitest 304; e2e 192.
- 2026-10-04 — Review PASS with should-fixes, applied: the fit line names only the Needs panel's top-3 needs (the
  two can't disagree); the engine's advice is computed once per render and shared (was 3-4x); rival rows 44 px.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- The draft-night board (`draft_sheet.html`) could show the same needs panel; separate task if wanted.
