---
id: DRAFT-011
title: "Value missed games at replacement level, not zero (G-26 A)"
epic: EP-15 Draft assistant
phase: 6
component: models
status: done
ready: true
size: M
autonomy: auto
gate: G-26
depends_on: [DRAFT-010]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, testing]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# DRAFT-011 — Replacement-filled missed games

## Objective
The owner saw Giannis Antetokounmpo at #118 ($10). Cause: the season-total value (D-51) counts every projected
missed game as zero, and his games forecast (45) and minutes (27.8) lean on one injury year (36 games). In a real
league a missed game is filled from waivers or covered by an IL slot. G-26 (owner, option A): value missed games at
**replacement level** (the best freely available players beyond the drafted pool [R-83]), and judge it with a draft
replay that also lets teams replace injured players, so the evaluation doesn't carry the assumption being fixed.

## Context to read (only these)
- `packages/models/src/fantasy_models/valuation.py` (`weekly`, `score`, `value_variant`)
- `packages/evaluation/src/fantasy_evaluation/draft_replay.py`; DRAFT-009/010 task files (pre-registration)
- `docs/project/architecture-decisions.md` D-49, D-51, D-65

## Pre-registration (written before any result is seen)
- **Replacement line**: the mean per-game stat line (all counting stats and FG/FT makes and attempts) of the 16
  players ranked just outside the drafted pool (ranks `pool_size+1 … pool_size+16` by the current variant's
  value), recomputed inside the pool iteration.
- **Fill**: weekly value uses `games × own line + (season_games − games) × replacement line`; one fill rate, 1.0
  (every missed game filled: IL slots + 16-team waivers). No other value is tried.
- **Replay with replacements** (both strategies get it): at each week start, a rostered player with no game in the
  previous 7 days (while the season was under way) goes to IL, up to the league's IL slots (3); for each, the team
  adds the best undrafted, unowned player by its own values for that week. IL players return when they play again.
- **Ship rule**: on the replacement replay (40 drafts, seed 0, as DRAFT-009), A − current all-play share > 0 with
  the 95 % bootstrap CI above 0 → ship A. Otherwise keep the current values and report. The no-replacement replay is
  reported alongside, for transparency, but doesn't decide.

## Acceptance criteria
- [x] AC1: `valuation.weekly` (or a sibling) fills missed games with the replacement line; a player projected for all
      games is unchanged, and two players identical except games differ by exactly `(g1 − g2) × (own − repl)`.
      Verify: `uv run pytest -q packages/models/tests/test_valuation.py -k replacement`
- [x] AC2: the replacement line is the mean of the 16 players just outside the pool, per the pre-registration.
      Verify: `test_valuation.py::test_replacement_line_is_just_outside_the_pool`
- [x] AC3: the replay supports IL replacements per the pre-registration (unit tests: an absent week sends a player to
      IL and adds the best free agent; at most 3 IL; the player returns when he plays).
      Verify: `uv run pytest -q packages/evaluation/tests/test_draft_replay.py -k il`
- [x] AC4: report committed: both replays (with and without replacements), the ship decision by the rule, and a
      top-25 before/after table with Giannis's rank and $ disclosed.
      Verify: `docs/evaluation/reports/DRAFT-011-replacement-fill.md`
- [x] AC5: if shipped, `auction_values` is rebuilt and published to the serve bucket, and `/players` shows the new
      ranking.
      Verify: `/players` against `gs://nbafa-hdfo-dev-serve` → method stamp includes `repl-fill`; the rank in the report matches

## Test requirements
Unit tests with tiny synthetic pools (TDD); the replay tests use hand-built day maps. No real data in unit tests.

## Evaluation requirements
The pre-registered replay above; [R-83] for replacement level; bootstrap CI as in DRAFT-009 [R-54].

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | packages/models/tests/test_valuation.py::test_replacement_fill_leaves_full_season_players_unchanged, ::test_replacement_fill_credits_missed_games_at_replacement_level, ::test_an_injured_star_ranks_higher_with_replacement_fill | pass |
| AC2 | test | test_valuation.py::test_replacement_line_is_just_outside_the_pool | pass |
| AC3 | test | packages/evaluation/tests/test_draft_replay.py::test_il_absent_player_is_replaced_by_the_best_free_agent, ::test_il_is_capped_by_slots_and_free_agents_are_not_shared, ::test_no_il_slots_keeps_the_drafted_squads | pass |
| AC4 | report | docs/evaluation/reports/DRAFT-011-replacement-fill.md: A − current with IL = **−0.0442** (95 % CI −0.0501 to −0.0381), A ahead in 2 % of 40 drafts; without IL −0.0521; Giannis #118→#66 under A | KEEP (rule not met) |
| AC5 | n/a | not shipped by the pre-registered rule; published values unchanged | n/a |

## Implementation history
- 2026-10-02 — Specified and pre-registered after the owner picked G-26 A.
- 2026-10-02 — Built TDD: `valuation.weekly(repl)`, `replacement_line`, `score/value_all(fill=)`; replay
  `weekly_rosters` (IL) + `run(il_slots=)`; CLI `repl-fill-replay`. **Incident**: the first run's report labelled the
  comparison backwards (the values dict put the current method first, so the replay computed current − A, but the
  report called the first strategy "A") and printed "SHIP A". Caught on reading the numbers, before anything shipped.
  Fixed: the candidate is listed first and `fill_report` refuses any other order (tests
  `test_fill_report_keeps_current_values_when_the_candidate_loses`, `test_fill_report_refuses_a_swapped_comparison`).
  Re-run: −0.0442 [−0.0501, −0.0381] → KEEP. (The two runs differ slightly in size because swapping the labels
  changes which seats each strategy gets; both say the current values win clearly.) Lessons: lesson 37.

## Decisions
- Result caveat: one season; the CI covers draft-seat randomness, not season-to-season variation (stated in the report).

## Known issues
_None._

## Follow-ups
- Option B (3-season smoothing of games/minutes) stays available if A doesn't fix the star-injury case.
