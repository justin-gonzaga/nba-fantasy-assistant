---
id: DRAFT-013
title: "Draft simulator 1/3: a simulated auction room, calibrated to real prices"
epic: EP-15 Draft assistant
phase: 6
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-28
depends_on: []
areas: [apps/web/src/features/draft/**, packages/models/**, apps/pipeline/**]
standards: [testing, ml]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DRAFT-013 — Draft simulator 1/3: the simulated room

## Objective
The owner (2026-10-03): "a draft simulator to help practise for the real thing". The simulator is three tasks:
**1/3 the room** (this: 15 simulated managers who nominate and bid), **2/3 the practice page** (DRAFT-014), **3/3
the post-draft report** (DRAFT-015). The league: auction, 16 teams, $200, 14 roster spots (224 sales); draft Sun
18 Oct.

A practice room is only useful if it prices players like a real room, so this task's core is **calibration**. It
builds on `draft_live` (the helper engine, Python + the board's JS, parity-tested) and `draft_mock` (a random room:
70 % follow the helper's top target, price × U(0.8, 1.2)). The approach choices (surface, opponent model, pace) are
open in **G-28 / D-67**; the owner chose the ★ options (a client-side TypeScript room in the web app, rule-based
styles calibrated to the published $).

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-42, D-67
- `packages/models/src/fantasy_models/draft_live.py`, `apps/pipeline/src/fantasy_pipeline/draft_mock.py`

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| A simulated manager bids | bids up to a private value = published $ × room inflation × positional/category need × its style × noise; never above its max bid (budget − $1 × (open spots − 1)) | a team with 1 spot and $1 left can only bid $1; a full team never bids |
| A simulated manager nominates | by style: best available, a budget drain (a player it values below the room), or a cheap end-of-draft filler | late draft: only $1 players left |
| Styles | balanced, stars-and-scrubs, punter (one category, chosen per seed), value hunter; a seed fixes the room | the owner can choose "random mix" or one style for all |
| Bidding war | increments of $1; the sale goes to the highest bidder at second-highest ceiling + $1 (an English auction) | ties broken by nomination order, deterministically by seed |
| End of the room | every team has 14 players and spent ≤ $200 | a team that cannot fill gets $1 players |

## Acceptance criteria
- [x] AC1: for 50 seeds a full room completes: 224 sales, every team at 14 players and ≤ $200, no bid above a
      team's max bid.
      Verify: `draftRoom.test.ts` › "rooms always complete" (property test, 50 seeds)
- [x] AC2: calibrated prices: across 50 seeds the mean sale price of the top 50 players by published $ is within
      ±15 % of those $ values, and each room spends ≥ 97 % of $3,200.
      Verify: `draftRoom.test.ts` › "price calibration" (numbers in Evidence)
- [x] AC3: the room's advice for any state equals `draft_live.advise` (shared parity fixtures with the Python
      engine), so practice uses draft-night numbers.
      Verify: `draftRoom.test.ts` › "parity with draft_live" + the existing Python parity test fixtures
- [x] AC4: deterministic: the same seed and the same owner actions replay the same room.
      Verify: `draftRoom.test.ts` › "seeded replay"

## Test requirements
Property tests (50 seeds); calibration; parity fixtures shared with `draft_live`; no network.

## Evaluation requirements
AC2 is the evaluation. Report the per-seed spread of top-50 prices and total spend; a room that underprices stars
teaches the wrong lessons.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | property | `draftRoom.test.ts` › rooms always complete (50 seeds, real 2026-27 values, 589 players) + auto-piloted owner | 224 sales, 14 each, ≤ $200, 0 bids over max |
| AC2 | calibration | `draftRoom.test.ts` › price calibration (50 seeds) | top-50 price/value **1.024**; spend min **3194**, mean **3197** of 3200 |
| AC3 | parity | `draftRoom.test.ts` › parity (fixture owned by `apps/pipeline/tests/test_draft_room_parity_fixture.py`) | inflation, weights, max bid, targets, hints, every adj/fit/ceiling equal |
| AC4 | determinism | `draftRoom.test.ts` › seeded replay | same seed equal; other seed differs |

## Implementation history
- 2026-10-03 — Specified from the owner's request; split into 3 tasks (room, page, report) to stay M-sized.
- 2026-10-03 — Built `live.ts` (TS port of `draft_live`), `room.ts` (styles, walk-aways, nominations, English
  auction at second-highest + $1, `rivalBid` for DRAFT-014, `simulate` with an auto-piloted owner) and fixtures
  (`advise-parity.json` from the Python engine; `values-2026-27.json` = ids, $ and strengths from the published
  values, no names). First calibration spent only 94.5 % (rich teams finished with cash) → richer-than-average
  teams bid up (cash per open spot ÷ the room's, capped 1.6×). First run took 80 s: NBA ids are numeric strings,
  so plain-object lookups went into V8's sparse mode; a `Map` index brought the suite to ~10 s. Vitest 268.

## Decisions
- Depends on DRAFT-005's `advise` engine, which is done and parity-tested; DRAFT-005 stays in review only for its
  manual-entry undo (AC3), which the simulator doesn't use, so the dependency is dropped (2026-10-03).
- G-28 APPROVED (A, A, A), 2026-10-03: web app; calibrated rule-based styles (base switches to Yahoo market
  prices when DATA-034 lands); real timers + fast-forward.

## Known issues
- Opponents are simulated, not learned from this league's managers (there is no history of their auction bids).
  The practice page says so.

## Follow-ups
- DRAFT-014 (the practice page), DRAFT-015 (the report); after 18 Oct: learn opponent tendencies from the real
  draft log for next season.
