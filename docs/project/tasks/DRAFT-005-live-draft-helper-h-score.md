---
id: DRAFT-005
title: "Live draft helper: best pick for your build after each selection (H-score style)"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: review
ready: true
size: M
autonomy: auto
gate: G-21
depends_on: [DRAFT-003, DRAFT-004, RSCH-005]
areas: [packages/models/**, packages/ingest/**, apps/pipeline/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-25
completed:
---
# DRAFT-005 — Live draft helper: best pick for your build after each selection (H-score style)

## Objective
**Auction draft** (16 teams, $200 budget, 30 s nomination / 20 s bid; Sun 18 Oct 17:00 Sydney). Quick entry records **player, winning team, and price**. The helper tracks every team's remaining budget and max bid, and suggests bid ceilings and nominations for the owner's build.

During the draft: track taken players by **quick pick entry** (autocomplete on phone/laptop, ~2 s per pick; D-44). There's no Yahoo polling because the API is closed (ADR-0025), and recommend the best available players for the owner's current roster build, using a dynamic, team-aware valuation in the spirit of H-scoring [R-02]. The auction variant converts value to $ if the league is an auction.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-42 (draft assistant)
- `docs/research/ml-literature-review.md` R-01, R-02, R-11, R-13

## Acceptance criteria
- [x] AC1: After each entered pick, the recommendations update within 2 s
      Verify: integration test with recorded draft-result fixtures + a timing log
- [x] AC2: Recommendations account for the current roster's category profile, not static ranks
      Verify: `test_recs_change_with_roster_build` (property: adding a strong-REB player lowers the REB weight)
- [ ] AC3: Manual entry is the primary path (no Yahoo polling: API closed, ADR-0025); corrections and undo work
      Verify: `test_manual_entry_flow`
- [x] AC4: Mock-draft replay: a full 13-round replay runs with no errors
      Verify: `just draft-mock` log in Evidence (16 teams x 14 slots = 224 picks)

## Test requirements
Unit tests with fixtures (no network). Property tests where noted. TDD for the package code.

## Evaluation requirements
Mock-draft replay; compare the drafted team's projected category wins vs a draft by Yahoo rank [R-02 methodology].

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | timing | `just draft-mock` on the live values: advise p50 0.9 ms, max 7.7 ms per pick (target < 2 s). The page runs the same arithmetic in JS (`test_js_matches_python_through_a_draft`: identical ceilings, targets, hints; inflation/weights to 1e-9) | ✅ |
| AC2 | property test | `test_recs_change_with_roster_build`: adding a strong-REB player lowers the REB weight and the REB-heavy player's fit | ✅ |
| AC3 | unit test + page | `test_manual_entry_flow` (a correction replaces the entry). The page flow (tap → team + price → Save, Unsell, Undo, online save with a this-device fallback) is **not yet verified by a real run**; that happens in the DRAFT-006 dry run before this task is marked done | ⏳ |
| AC4 | mock replay | `just draft-mock`: `picks=224 rosters_full=True spent=$3170 advise_ms p50=0.9 max=7.7` | ✅ |
| Checks | tests | draft_live unit tests (7), JS parity, page scripts parse with node, sheet tests | ✅ |

## Implementation history
- 2026-09-26: Owner chose the board page with saved state (panel).
  - `fantasy_models.draft_live`: the Python reference, with max bid, inflation (U1), H-score-inspired fit capped at +/-25 % (U2, [R-02]) and nomination hints ([R-80, R-81]).
  - `draft_live.js`: the page mirror, with a parity test.
  - The live panel is on the auction board (db capability); `just draft-mock`.
  - Also touched, outside `areas:`: `justfile` (the draft-mock recipe) and `pyproject.toml` (tests may run node and use seeded random: S603/S311).
- 2026-09-26 review (FAIL → fixed):
  1. A full roster's leftover cash no longer inflates prices (Python + JS, with a new test and parity coverage).
  2. Unconfirmed picks/undos survive syncs and retry.
  3. Warns when a price is above the winning team's max bid (a second Save records it anyway).
  4. Picks are ordered by timestamp.
  5. `'` is escaped.
  6. AC3 is left unverified until the dry run.

## Decisions
_None yet._

## Known issues
- Team names are Team 1–16 (set 'My team' once); real manager names aren't stored (privacy).

## Follow-ups
_None._
