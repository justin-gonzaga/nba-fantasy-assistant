---
id: DRAFT-014
title: "Draft simulator 2/3: the practice page (nominate, bid, timers, fast-forward)"
epic: EP-15 Draft assistant
phase: 6
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-28
depends_on: [DRAFT-013, WEB-024]
areas: [apps/web/**]
standards: [frontend, design, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DRAFT-014 — Draft simulator 2/3: the practice page

## Objective
A "Draft practice" page where the owner runs a full auction against DRAFT-013's simulated room, with the same advice
as draft night (max bid, ceilings, targets, nomination hints, punt fit), in the Courtside design (§9). As approved
in G-28 (web page, real timers with fast-forward).

## Context to read (only these)
- DRAFT-013 (the room API); `docs/standards/design-language.md` §9; `docs/runbooks/draft-day.md`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner, a week out: "let me practise" | Start: choose a strategy (all cats / a punt), opponent style (random mix / one style), pace (real / untimed); the room opens | an unfinished draft offers "Resume" (saved in the browser) |
| Owner's nomination (order rotates) | search any available player; the helper's nomination hints shown | 30 s timer (real pace): on expiry the top hint is nominated |
| Bidding on a lot | +$1 / +$5 / custom and Pass; current price and high bidder; each rival's max bid; the helper's ceiling for this player and my max bid | a bid above my max bid is blocked with the reason; the 20 s bid timer resets on each bid |
| Undo | undo the last sale the owner took part in (practice only) | nothing further back |
| Fast-forward | "Sim to my next nomination" and "Sim the rest": I bid up to the helper's ceilings meanwhile (said on the button) | — |
| Entry points | /draft: a sidebar item on desktop; a "Practise the draft" button on Players (phones keep 5 tabs) | — |
| Phone | one column in reading order: my budget, the lot and bid buttons, fast-forward controls, my team, rivals, recent sales | bid buttons ≥ 44 px; DOM order = visual order (no CSS `order`) |
| Desktop | the lot and its controls left; my team, rivals and recent sales in a right column | 1280 × 800 without scrolling the bidding area |
| Values not published yet | WEB-016's not-ready card; no practice | — |
| Sample mode (WEB-026) | the sample has 10 players and a practice auction sells 224: a card explains that practice needs the full pool and to sign in | no crash, no fake players |
| Keyboard and screen readers | B = +$1, Shift+B = +$5, P = pass, N = nominate; the timer is announced at 10 s and 5 s; reduced motion: no countdown animation | — |

## Acceptance criteria
- [x] AC1: a full practice draft can be played start to finish on phone and desktop.
      Verify: e2e `draft-practice.spec.ts` (sim the rest after 5 owner sales; the report link appears) on iPhone 13
      and desktop + axe
- [x] AC2: the ceiling and max bid shown equal the room's `advise` output for that state; over-budget bids are
      blocked with the reason.
      Verify: `DraftPractice.test.tsx` › "same advice as draft night", "blocks a bid over max"
- [x] AC3: timers (expiry nominates or passes), undo, fast-forward and resume behave as specified.
      Verify: `DraftPractice.test.tsx` with fake timers
- [x] AC4: practice only reads the published player values; it never writes to the API or touches the real
      draft log.
      Verify: `DraftPractice.test.tsx` › "reads values only" + review

## Plan
1. `practice.ts` (pure): lot state machine over the immutable `Room`: open lot (rivals settle among themselves
   against cached walk-aways), owner bid / pass, timer expiry, nominate, undo stack, save/restore.
2. `DraftPracticePage.tsx`: setup (strategy, opponents, pace, resume) → room (lot centre, my team right,
   rivals + log left; phones stacked) → done (roster, spent, surplus; the full report is DRAFT-015).
3. Tests first: `practice.test.ts` (pure) + `DraftPractice.test.tsx` (fake timers); e2e phone + desktop; screens.

## Test requirements
Vitest with fake timers; persona e2e (phone + desktop, axe); the §9 screenshot loop.

## Evaluation requirements
n/a (DRAFT-013 holds the calibration).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | e2e + axe | `e2e/draft-practice.spec.ts` (5 lots by hand, then sim the rest → 14-player team; no sideways scroll) on iPhone 13, Pixel 7, desktop; `a11y.spec.ts` › draft practice setup + room | pass (189 e2e; axe clean) |
| AC2 | unit | `DraftPractice.test.tsx` › same ceiling and max bid as `myAdvice`; blocks a bid over max ($187) with the reason; `practice.test.ts` | pass |
| AC3 | unit | `DraftPractice.test.tsx` (fake timers: an expired bid timer sells; sim the rest; resume) + `practice.test.ts` (nomination expiry → top target, undo, sim to next nomination, resume) | pass |
| AC4 | unit + review | `DraftPractice.test.tsx` › reads values only: the only API call is `players:all` | pass |

## Implementation history
- 2026-10-03 — Specified (split from DRAFT-013).
- 2026-10-03 — Built `practice.ts` (a pure lot state machine: rivals settle against walk-aways fixed per lot, owner
  bid/pass, timer expiry, undo stack, save/resume) and `DraftPracticePage` (setup → room → done), the /draft route,
  a sidebar "Tools" item and a Players link. Screens: the desktop room has rivals left, the lot centre and my team
  right; on phones the lot follows the budget line and the fast-forward controls move below it (first shot had
  them above the fold); the timer bar is neutral until the last 5 s. Vitest 284; e2e 189.

## Decisions
- G-28 APPROVED (A, A, A), 2026-10-03.

## Known issues
- On the real 2026-27 values the top 8 sell ~15 % above value with a narrow spread (e.g. $73.9 → $81–88 over 20
  rooms) while the mid-tier sells below value (top-50 overall 1.02×). Plausible (stars draw a premium), but rival
  rooms vary less than real ones. Revisit with Yahoo market prices (DATA-034) or this league's real draft log.
- The 10-player sample can't run a 224-sale auction; sample mode explains this instead.
- Resuming a saved draft starts with an empty undo history (undo covers the current session only).
- Review (2026-10-03): the first phone layout reordered sections with CSS `order`, so focus and screen-reader
  order disagreed with what was shown (WCAG 1.3.2 / 2.4.3). Fixed by making the DOM order the visual order;
  rivals stack below my team rather than in a sheet.

## Follow-ups
- DRAFT-015 (the report).
