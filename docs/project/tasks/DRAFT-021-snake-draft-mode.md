---
id: DRAFT-021
title: "Snake (and linear) draft mode in the practice room"
epic: EP-15 Draft assistant
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DRAFT-017, DRAFT-020]
areas: [apps/web/**, apps/api/**]
standards: [frontend, testing]
assignee:
created: 2026-10-04
completed:
---
# DRAFT-021 — Snake and linear draft

## Objective
The owner asked for "different types of draft settings … and different league types." Auction is the only mode today.
Add a **snake** draft (and **linear**, same order every round) so the same room can practise the more common Yahoo
format: pick order from the seat, on-the-clock timer per pick, auto-pick on expiry, and bots that choose by
value-over-replacement plus roster need, with no budget.

## Context to read (only these)
- DRAFT-017 (preset `drafting`, `seat`), `room.ts` (`createRoom`, bots), the existing needs/recommendation code

## User stories and edge cases
| Situation | Expected |
|---|---|
| Seat 3 of 12, 13 rounds | pick numbers follow the snake: 3, 22, 27, 46 … ; "you're up in N picks" is shown |
| Linear draft | same order each round |
| Timer expires on my pick | auto-pick the best available recommendation and say so |
| I pick fast | bots advance on their clocks; "Pause" and "Sim to my next pick" exist |
| Roster full at a position | bots and recommendations skip players that cannot start (when the format has positions) |
| Pool exhausted before all rosters are full | the room ends with a message, no infinite loop |
| Auction-only controls (budget, nominate) | hidden in snake; the settings page greys budget |
| Resume | an unfinished snake resumes at the same pick |
| Keeper/trade picks | out of scope (listed in follow-ups) |

## Acceptance criteria
- [ ] AC1: the pick-order function is correct for snake and linear across team counts 4–20 and rounds 5–25, at
      boundaries (first/last seat, round 1 and 2, last round).
      Verify: `order.test.ts` › "snake and linear"
- [ ] AC2: a full seeded bot-only snake draft completes with every team at `spots` players, no player twice, and no
      auction-only state in the snapshot.
      Verify: `draftRoom.test.ts` › "snake full draft"
- [ ] AC3: the user's clock and auto-pick work (fake timers): expiry picks the top recommendation; Pause stops all
      clocks; "Sim to my next pick" stops exactly at the user's turn.
      Verify: `DraftPractice.test.tsx` › "snake clock, auto-pick, pause, sim to my turn"
- [ ] AC4: the report works without budget (value over pick slot: "got $X of value at pick N"), and the supported
      combinations constant includes `snake` only when this task ships.
      Verify: `DraftReport.test.tsx` › "snake report"; `test_draft_settings.py` › "snake accepted"
- [ ] AC5: phone fit and a11y for the pick list and "on the clock" banner; the same DRAFT-020 clock/sounds apply.
      Verify: e2e `draft-snake.spec.ts` (iPhone 13, axe)

## Test requirements
Pure order function tests; seeded draft tests; fake timers; Playwright.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified. Priority P2, after the real draft (18 Oct).

## Decisions
- Reuse the room state machine; only order, clock source and bot choice differ by `drafting`.

## Known issues
_None._

## Follow-ups
- Keepers, trades, third-round reversal.
