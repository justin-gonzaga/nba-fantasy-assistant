---
id: WEB-019
title: "Healthy rank: per-game value rank next to the risk-adjusted rank"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [WEB-005]
areas: [apps/pipeline/src/fantasy_pipeline/draft_values.py, packages/models/**, apps/api/**, apps/web/**]
standards: [frontend, design, backend]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# WEB-019 — Healthy rank

## Objective
The owner (2026-10-02, on Giannis): show what a player is worth *if healthy*, next to the main (availability-
adjusted) rank, so the owner can weigh injury risk themselves. The healthy value is the same valuation with every
player at the same games count (72): a different view of stored projections, no new model.

## Context to read (only these)
- `packages/models/src/fantasy_models/valuation.py` (`value_all`), `apps/pipeline/src/fantasy_pipeline/draft_values.py`
- `apps/api/src/fantasy_api/players.py`; `apps/web/src/features/players/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases |
|---|---|---|
| Owner pre-draft | "Who's elite when healthy but discounted for risk?" | a "Healthy rank" sort; rows show "Healthy #17" when it differs from the rank by ≥ 10 places |
| Owner reading a player | Detail shows both ranks with one plain sentence | "Ranked #118 after expected missed games (45 of 82); #17 if he plays 72." |
| Punt strategies | Healthy rank per strategy | computed per variant, like the main rank |
| Old values file without the column | API before the pipeline re-runs | `healthyRank: null`, UI hides it (no error) |

## Acceptance criteria
- [x] AC1: `draft-values` writes `healthy_rank` and `healthy_dollars` per variant (games = 72 for everyone).
      Verify: `apps/pipeline/tests/test_draft_values.py::test_healthy_rank_*`
- [x] AC2: `/players` returns `healthyRank`/`healthyDollars` (null when absent) and the projected games.
      Verify: `apps/api/tests/test_players.py::test_healthy_rank*`
- [x] AC3: Players page: "Healthy rank" sort; the row hint when the gap ≥ 10; the detail sentence; hidden when null.
      Verify: `PlayersPage.test.tsx` (sort, hint threshold, detail, null)

## Test requirements
Synthetic pools for the valuation; seeded parquet for the API; fixtures for the page.

## Evaluation requirements
n/a (a view of existing projections; the main rank stays the decision value).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/pipeline/tests/test_draft_values.py::test_healthy_rank_values_everyone_at_the_same_games, ::test_healthy_rank_ignores_projected_games; local rebuild: 5,890 rows, 0 rank differences vs the current values, max $ diff 3e-14 | pass |
| AC2 | test | apps/api/tests/test_players.py::test_healthy_rank_is_served_when_published, ::test_healthy_rank_is_null_for_older_values_files | pass |
| AC3 | test | PlayersPage.test.tsx › "healthy rank (WEB-019 AC3)" (hint, sort, detail sentence, hidden when null) | pass (134 web tests) |

## Implementation history
- 2026-10-02 — Specified (owner: "do both").
- 2026-10-02 — Built TDD (pipeline, API, page). `just ci-local`: 453 passed, coverage 93.38 %. The data file with
  the new columns is not yet published; the page hides the healthy rank until it is (owner decision pending).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
