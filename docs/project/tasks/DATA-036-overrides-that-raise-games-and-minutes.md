---
id: DATA-036
title: "Source-backed overrides that raise games or minutes (the Giannis case)"
epic: EP-15 Draft assistant
phase: 6
component: pipeline
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DATA-031, DATA-035]
areas: [apps/pipeline/src/fantasy_pipeline/overrides.py, apps/pipeline/tests/**, warehouse/seeds/availability_overrides.csv, docs/runbooks/**, apps/api/**, apps/web/**]
standards: [data-engineering, testing, frontend]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DATA-036 — Overrides that raise games or minutes

## Objective
The owner (2026-10-03, "yes"): the model discounts players after an injury season (Giannis: 45 games, 27.8 min),
and both pre-registered model fixes lost the draft replay (DRAFT-011/012). When credible news says a player is
fully cleared (e.g. "no minutes restriction"), the owner should be able to raise his expected games and/or minutes,
with the same evidence rule as the existing absence overrides (DATA-031): a public source, its date, a verbatim
quote, reviewed by the owner. Today overrides can only cap games down.

## Context to read (only these)
- `apps/pipeline/src/fantasy_pipeline/overrides.py`, `warehouse/seeds/availability_overrides.csv`
- `docs/runbooks/draft-day.md` (overrides section), DATA-031

## User stories and edge cases
| Situation | Behaviour |
|---|---|
| Owner adds a `cleared` row with `expected_games` 68 for Giannis (source, date, quote) | his projected games become max(model, 68); values rebuild on the next daily run; his row shows an "Adjusted" badge with the source date |
| `expected_mpg` 33 | minutes become 33 and every per-game counting stat and attempt scales by 33 / model mpg (the model is per-minute rates × minutes); FG% / FT% unchanged |
| A raise above the plausible (`expected_games` > 82, `expected_mpg` > 40) | rejected with a clear error, nothing published |
| A `cleared` row without a source URL, date or quote | rejected (evidence rule) |
| A source dated after the draft | rejected (point in time, as today) |
| A cap row and a raise row for the same player | rejected (contradictory) |
| The publish guard | a handful of raises never trips it (top-10 / row-count checks) |

## Acceptance criteria
- [x] AC1: `status = cleared` rows with `expected_games` and/or `expected_mpg` raise games (never lower) and set
      minutes with per-game stats scaled; shooting percentages unchanged.
      Verify: `uv run pytest -q apps/pipeline/tests/test_overrides.py -k cleared`
- [x] AC2: validation rejects implausible values, missing evidence, late sources and contradictory rows.
      Verify: `test_overrides.py -k rejects`
- [x] AC3: the values file carries `adjusted` (the override status + source date) and the API shows an "Adjusted"
      badge with why "Cleared: <quote> (<source date>)"; absent column → no badge.
      Verify: `apps/api/tests/test_players.py::test_badges_adjusted_*`
- [x] AC4: runbook: how to add a raise row (columns, evidence, what changes, how to undo).
      Verify: `docs/runbooks/draft-day.md` § Overrides

## Test requirements
Unit tests with synthetic projections; API tests with seeded parquet; no network.

## Evaluation requirements
n/a: an owner-reviewed input with cited evidence (like DATA-031), not a model change; values are re-published by
the guarded daily step.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `test_overrides.py::test_cleared_raises_games_and_scales_stats_with_minutes`, `::test_cleared_never_lowers_games` | pass (13/13 file) |
| AC2 | unit | `test_overrides.py::test_rejects_bad_raises` (parametrised), `::test_rejects_future_sources_unknown_status_and_unmatched_names` | pass |
| AC3 | API + web | `test_players.py::test_badges_adjusted_shows_the_cited_source`, `::test_badges_adjusted_absent_without_the_column`; `PlayerBadges.test.tsx` | pass (2/2; web 228) |
| AC4 | doc | `docs/runbooks/draft-day.md` § Overrides (columns, evidence, what changes, undo) | written |

## Implementation history
- 2026-10-03 — Specified (owner said yes after DRAFT-011/012 didn't ship).
- 2026-10-03 — Built: `cleared` status + `expected_games`/`expected_mpg` (seed header extended; the real seed loads,
  3 rows), `_check_raises`, apply() floors games and scales counting stats by the mpg ratio, `adjustments()` joined
  into draft values as `adjusted`; API badge "Adjusted" (accent, why = "Cleared: quote (date)"); web pencil icon.
  No raise rows added: the owner adds them from cited news (runbook).
- 2026-10-03 — Review PASS; fixed its findings: a cleared row with cap fields is rejected
  (`test_rejects_bad_raises` +2 cases), and `test_draft_publish.py::test_check_tolerates_one_raised_player_jumping_to_first`
  covers the publish-guard edge case. 28/28 pass.

## Decisions
- Raises are owner-entered from cited news only; Claude may draft a row with its source for the owner to approve.

## Known issues
_None._

## Follow-ups
_None._
