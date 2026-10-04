---
id: DRAFT-003
title: "League-aware valuation: G-score, punt variants, tiers (all Yahoo formats)"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: done
ready: true
size: M
autonomy: auto
gate: G-21
depends_on: [DRAFT-002, RSCH-005]
areas: [packages/models/**, packages/ingest/**, packages/core/src/fantasy_core/league.py, apps/pipeline/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DRAFT-003 — League-aware valuation: G-score, punt variants, tiers (all Yahoo formats)

## Objective
Value players under the owner's league settings: category leagues use G-score [R-01] (Z-score as a reference), with volume-weighted ratio stats and turnovers negative; points leagues use expected fantasy points. Punt-strategy variants and value tiers. **The league is a 16-team $200 auction** (owner settings, 2026-09-25), so values are converted to **auction dollars**: value above replacement for a 16×14-man pool → a $ allocation of the 16×$200 budget. The method must be grounded or explicitly flagged in RSCH-004.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-42 (draft assistant)
- `docs/research/ml-literature-review.md` R-01, R-02, R-11, R-13

## Acceptance criteria
- [x] AC1: Valuation reads categories/modifiers from the Yahoo settings (or a golden fixture per format) and handles all 5 formats
      Verify: golden tests `test_valuation_formats` (5 fixtures)
- [x] AC2: Ratio categories are weighted by volume (FG% impact = makes minus league% x attempts); TO is negative
      Verify: `test_ratio_and_negative_categories` (property test)
- [x] AC3: Punt variants re-rank correctly: punting category c removes its contribution and leaves the others unchanged
      Verify: `test_punt_variant_invariants`

## Test requirements
Unit tests with fixtures (no network). Property tests where noted. TDD for the package code.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | golden tests | `apps/pipeline/tests/test_draft_values.py::test_valuation_formats` × 5 fixtures (real scrubbed H2H 9-cat auction + 4 synthetic: one-win snake, roto auction, H2H points, season points) parse → value end to end; `packages/ingest/tests/test_yahoo_import.py` (10 tests) + `packages/models/tests/test_valuation.py::test_valuation_formats_all_five` | ✅ |
| AC2 | property test | `test_ratio_and_negative_categories` (hypothesis, 40 examples): more attempts at an above-league % raise the FG% score; more TO lower the TO score | ✅ |
| AC3 | invariant test | `test_punt_variant_invariants`: every punt variant equals "all" minus exactly that category; the other 8 category scores are identical | ✅ |
| Live | `python -m fantasy_pipeline draft-values` | real settings paste → `format=h2h_categories teams=16 pool=224`, 5,890 rows (10 variants × 589) → BigQuery `predictions.auction_values` + parquet. $ sum = 3,200.0 over 224 drafted; top: Jokić $61, SGA $56, Wembanyama $53. Punt FT% lifts Giannis +$12, Gobert +$9, Zion +$7 (domain sanity) | ✅ |
| Checks | just ci-local | 193 passed, coverage 98.66 %, contracts 3/3 kept | ✅ |

## Implementation history
- 2026-09-25:
  - `fantasy_core.league` (LeagueRules, ScoringFormat, Category): the minimum ANL-001 extends.
  - `fantasy_ingest.yahoo_import.parse_league_settings`: the settings slice of DISC-011.
  - `fantasy_models.valuation`:
    - G-score per category [R-01], with within-week variance measured from the 2025-26 game logs; Rotisserie uses it with weight 0 (a z-score)
    - points formats use modifiers
    - greedy positional pool fill → replacement by pool size [R-83] → VOR → $ (U1 practitioner)
    - punt variants and natural-break tiers
  - `python -m fantasy_pipeline draft-values`.

## Decisions
- Category scores are computed once on the converged "all" pool; punts only drop columns. This makes AC3's invariant exact, and a punt re-ranks without redefining the pool.
- Auction values are written to `predictions.auction_values` (a Python decision output), not a dbt mart; DRAFT-004 reads it.
- Unsupported categories (DD/TD, A/T, OREB…) fail loudly with ContractViolation until ANL-001.

## Known issues
- Positions are derived from NBA listings (D-47 Q1); a pasted Yahoo player list should override them before the draft.
- Values use the H1+aging projections; they re-run after DRAFT-007 (minutes/breakouts) and the availability overrides.

## Follow-ups
_None._
