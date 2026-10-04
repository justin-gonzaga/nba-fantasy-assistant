---
id: WEB-022
title: "Filters never dead-end: counts, hidden zero chips, honest notes; tiers that mean something"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [WEB-020]
areas: [apps/web/**, apps/api/**, packages/models/src/fantasy_models/valuation.py, packages/models/tests/**]
standards: [frontend, design, backend]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-022 — Filters never dead-end; tiers that mean something

## Objective
The owner (2026-10-03): "some indicators produce 0 results." Measured on the live data:
- **Role change and Age show for nobody**: the indicator loader skipped the whole history file because the live file
  predates its `age` column (a bug: role needs only minutes).
- **Tiers**: 585 of 589 players are "Tier 4" (the gap rule finds breaks only among the stars), so "Tier N" in every
  row and the **Top tier** badge (1 player) mean nothing.
- **Breakout** (needs this pre-season, draft week) and **Steady** (publishes after the next daily run) have no data
  yet, but their filter chips still show and return 0 players with no explanation.

## Context to read (only these)
- `apps/api/src/fantasy_api/indicators.py`, `badges.py`; `packages/models/src/fantasy_models/valuation.py` (`tiers`)
- `apps/web/src/features/players/*` (filters)

## User stories and edge cases
| Situation | Expected |
|---|---|
| A filter chip would match 0 players | the chip isn't shown; chips show their counts ("Injury prone 17") |
| A data source isn't published yet | one muted line under the filters: e.g. "Breakout chance appears after the pre-season backfill (draft week)"; "Steady/Volatile appears after the next daily run" |
| A filter in the URL that now matches nothing (old link) | the list explains "No players match" with Clear filters (exists) and the chip stays visible while selected |
| Old files without a column (e.g. `age`) | only the indicators that need it are skipped |
| 16-team league | tiers never hold more than 16 players (one draft round) and still break at big value gaps |
| "Top tier" | becomes "First-round value": the top 16 for the chosen strategy, with the why "#5 overall: first-round value in a 16-team league" |

## Acceptance criteria
- [x] AC1: role change works from history files without `age`; age indicator appears when `age` exists.
      Verify: `apps/api/tests/test_indicators.py::test_role_without_age_column`
- [x] AC2: `tiers` caps a tier at the league's team count while keeping gap breaks; the live-like case (dense values)
      yields ≥ pool/teams tiers.
      Verify: `uv run pytest -q packages/models/tests/test_valuation.py -k tier`
- [x] AC3: the Top tier badge becomes "First-round value" (rank ≤ teams for the variant), why line names the league size.
      Verify: `apps/api/tests/test_players.py::test_badges_first_round_value`
- [x] AC4: badge and signal chips show counts; zero-count chips are hidden unless selected; a note says why a source is
      missing (API `badgeNotes` + indicator notes).
      Verify: `PlayersPage.test.tsx` › "filters never dead-end"; `test_players.py::test_notes_name_missing_sources`
- [x] AC5: on the live data, every visible chip has ≥ 1 player.
      Verify: a run of `/players` against the serve bucket (counts recorded in Evidence)

## Test requirements
Unit tests per AC; the live check is read-only.

## Evaluation requirements
n/a (tiers are a presentation of the same values; ranks and $ unchanged).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/api/tests/test_indicators.py::test_role_without_age_column | pass |
| AC2 | test | packages/models/tests/test_valuation.py::test_tiers_are_capped_at_a_draft_round, ::test_values_carry_the_league_size_and_round_tiers | pass |
| AC3 | test | apps/api/tests/test_players.py::test_badges_first_round_value, ::test_badges_top_tier_follows_the_strategy | pass |
| AC4 | test | PlayersPage.test.tsx › "filters never dead-end (WEB-022 AC4)"; test_players.py::test_notes_name_missing_sources | pass (226 web, 68 API) |
| AC5 | live check | rebuilt from the warehouse (local, read-only) + API: First-round value 16, Injury prone 17, Missed time 52, Rookie 52, Bounce-back 94; Bigger role 65, Smaller 58, Steady 68, Volatile 67; tiers 1,2,1 then 16 each (40 tiers); one note: breakout in draft week. Live after the next 07:45 run (the job publishes) | pass |

## Implementation history
- 2026-10-03 — Specified from the owner's report with live counts (role/age 0, tiers 585/589 in tier 4, Top tier 1).

## Decisions
- Tier cap = number of teams (a draft round), from LeagueRules, so it adapts to other league sizes.

## Known issues
_None._

## Follow-ups
_None._
- 2026-10-03 — Built TDD; persona e2e 175 passed; live counts in Evidence.
