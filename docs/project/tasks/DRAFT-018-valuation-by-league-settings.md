---
id: DRAFT-018
title: "Value players for any league settings: valuation endpoint and per-season projections feed"
epic: EP-15 Draft assistant
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-33
depends_on: [APP-011, PERF-001]
areas: [apps/api/**, apps/pipeline/**, packages/decision/**, packages/models/**]
standards: [backend, testing, performance]
assignee:
created: 2026-10-04
completed:
---
# DRAFT-018 — Valuation for any league settings

## Objective
The board's dollar values and z-scores are computed for the one league (9 categories, 16 teams, $200, 14 spots) and
published as a file. A different team count, budget, roster size, category set or scoring format needs different
values. `fantasy_models.valuation.value_all` already takes `LeagueRules` and supports the five `ScoringFormat`s
(ADR-0018). This task exposes it: the API computes values **on demand for a league shape**, from the projection
distributions the pipeline already publishes. **Gated (G-33 / D-70)**: where the computation lives is the owner's call.

## Context to read (only these)
- D-70 (options A TS port · B server on demand with cache · C precomputed presets), D-71 (scale targets)
- `packages/models/src/fantasy_models/valuation.py`, `packages/core/src/fantasy_core/league.py`
- `apps/pipeline` projection publishing; `apps/api` players routes; PERF-001 (the latency budget this must meet)

## Design (recommendation B; changes if the owner picks differently)
1. **Feed**: the pipeline additionally publishes `projections_for_valuation.parquet` (or compact JSON) per season: the
   per-player mean and variance of every stat the formats need (counting stats, attempts for the percentage
   categories, games, minutes, position eligibility). No new model; the same numbers that produced today's board.
2. **Endpoint** `POST /valuation` with `{ league: LeagueSpec, season, positionsFilter? }` → `{ players: [{id, value, z[], rank}], version }`.
   `LeagueSpec` is the preset's `league` block (APP-011) plus the category set (for category formats).
3. **Cache**: results are keyed by `(season, hash(league), projectionsVersion)` in process memory (LRU, bounded) and in
   a shared object (GCS or Firestore) so cold instances do not recompute; identical requests are coalesced
   (single-flight). Deterministic: the same inputs give the same output.
4. **Fallback**: if the endpoint fails or exceeds its budget, the web app uses the published default board when the
   league equals the default; for other shapes it falls back to DRAFT-017's labelled "approximate values" rescale for
   category-auction leagues, and for formats that rescale cannot serve (points, roto, custom categories) it tells the
   user values are unavailable (never a silently wrong number).

## User stories and edge cases
| Situation | Expected |
|---|---|
| Default league (16 × $200 × 14, 9-cat) | identical to today's published values (golden test) — and served from the published file, not computed |
| 12 teams, $260, 13 spots | values re-scaled; sum of values over the drafted pool ≈ teams × budget (within $1) |
| Different category set (drop TO, add DD) | z-scores use the chosen set only; the percentage categories keep attempts weighting |
| Points league (DRAFT-019) | values come from `ScoringObjective` for the preset's points weights |
| Two users ask the same league at once | computed once (single-flight), both get the result |
| Projections updated mid-day | a new `projectionsVersion` changes the key; old entries expire; clients refetch on version change |
| Invalid league (teams = 1, budget < spots) | 422 problem with the field path; no computation |
| Abuse: many distinct leagues in a burst | per-user and global rate limits; cache bounded; 429 with `Retry-After` |
| Cold instance | first request within the cold-start budget from PERF-001, or the fallback applies |

## Acceptance criteria
- [ ] AC1: `POST /valuation` for the default league returns values equal (±$0, z ±1e-9) to the published board for
      every player.
      Verify: `uv run pytest -q apps/api/tests/test_valuation.py -k "default_equals_published"`
- [ ] AC2: for three other shapes (12 × $260 × 13, 8 × $150 × 12, 20 × $200 × 15) the money invariant holds: the sum of
      auction values of the top `teams × spots` players = `teams × budget` within $1, and every value ≥ $1.
      Verify: `uv run pytest -q apps/api/tests/test_valuation.py -k "money_invariant"`
- [ ] AC3: the category set and `ScoringObjective` are honoured: a points weight vector and a custom category set each
      change the ranking in the expected direction on a synthetic pool.
      Verify: `uv run pytest -q apps/api/tests/test_valuation.py -k "objective or categories"`
- [ ] AC4: cache and single-flight: 50 concurrent identical requests run one computation; distinct requests are bounded
      by the LRU; a new `projectionsVersion` misses the cache.
      Verify: `uv run pytest -q apps/api/tests/test_valuation_cache.py`
- [ ] AC5: the measured latency meets the PERF-001 budget (p95 per the SLO, warm and cold, cached and uncached) on the
      load profile, recorded in the task.
      Verify: `just load-test --scenario valuation` report in `docs/evaluation/reports/perf-valuation.md`
- [ ] AC6: the feed is published by the daily run and contains no field that is not in the projections (no leakage of
      outcomes); the build is as-of safe.
      Verify: `uv run pytest -q apps/pipeline/tests -k valuation_feed`; as-of test mutates future data and sees no change
- [ ] AC7: the web client uses the endpoint through TanStack Query with the fallback rules above; an outage shows the
      explicit "values unavailable" state.
      Verify: `useValuation.test.tsx` (MSW: ok, 422, 429, 500, timeout; fallback to approximate for category auction,
      unavailable for points)

## Test requirements
Golden test against the published board; synthetic-pool property tests; concurrency test with asyncio; no network.

## Evaluation requirements
No model change, so no accuracy evaluation. The equivalence (AC1) and money invariant (AC2) are the correctness
checks.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified; waits for G-33 (D-70/D-71) and the PERF-001 baseline. Not required for the 18 Oct draft: the
  default league uses the published board.

## Decisions
- Pending D-70. Recommendation B because the code and its tests already exist in Python, avoids a second implementation
  in TypeScript, and the cache bounds cost; A is faster per request but duplicates and can drift; C is cheapest but
  limited to a few presets.

## Known issues
_None._

## Follow-ups
- DRAFT-019 uses this for non-category formats.
