# MVP-002: how often listed players actually play

Generated 2026-09-27 14:22 UTC by `python -m fantasy_pipeline availability-study`.
Replaces the placeholder status probabilities (A-30) used by the rest-of-week projections.

**Method**: for each regular-season game day, the latest official injury report published by
5:35 PM ET (stored in bronze), joined to that season's game logs: a listed player "played" if he
has a game-log row that day. Players who never appear in the season's logs can't be scored
(e.g. two-way players who never played) and are excluded. 95 % intervals: bootstrap over game
days (2,000 resamples) [R-54].

**Coverage**: 327 game days; 327 reports used; 0 days with no
report found at that slot; 0 unparseable; 1,913 rows unmatched.

## Pooled

| status | n | played | 95 % CI |
|---|---|---|---|
| Available | 2,139 | 82.7% | 80.7% to 84.6% |
| Probable | 1,288 | 91.8% | 90.1% to 93.4% |
| Questionable | 3,201 | 48.9% | 47.0% to 50.9% |
| Doubtful | 533 | 1.1% | 0.2% to 2.2% |
| Out | 18,648 | 0.1% | 0.1% to 0.2% |

## By season

### 2024-25

| status | n | played | 95 % CI |
|---|---|---|---|
| Available | 923 | 81.8% | 78.6% to 84.8% |
| Probable | 713 | 91.0% | 88.7% to 93.2% |
| Questionable | 1,760 | 47.4% | 45.1% to 49.9% |
| Doubtful | 229 | 1.7% | 0.0% to 4.0% |
| Out | 9,466 | 0.2% | 0.1% to 0.3% |

### 2025-26

| status | n | played | 95 % CI |
|---|---|---|---|
| Available | 1,216 | 83.3% | 80.6% to 86.0% |
| Probable | 575 | 92.7% | 90.3% to 94.9% |
| Questionable | 1,441 | 50.7% | 47.8% to 53.9% |
| Doubtful | 304 | 0.7% | 0.0% to 1.6% |
| Out | 9,182 | 0.1% | 0.0% to 0.1% |

## What it means

- **Doubtful is effectively Out**: 1.1 % played (95 % CI 0.2-2.2 %), far below the 15-25 % often
  assumed. The brief treats Doubtful like Out.
- **Questionable is a coin flip**: 48.9 % (47.0-50.9 %), stable across both seasons.
- **Probable plays 92 % of the time**, more often than **Available** (83 %). The Available list
  includes returning players and two-way players the team often doesn't use.
- The rates are stable between 2024-25 and 2025-26, so pooling is reasonable.
- These replace the placeholder table in `fantasy_models.weekly` (A-30 closed).

## Caveats

- 1,913 of ~27,700 rows (7 %) couldn't be scored: mostly two-way/G League players with no NBA
  minutes that season, plus a few name spellings that differ between the report and the logs.

- One snapshot per day at ~5:30 PM ET. Earlier reports (the Sydney-morning brief runs around
  3:30-4:30 PM ET) carry more uncertainty: a later downgrade or upgrade isn't seen here.
- "Played" means any minutes; a return on a minutes restriction counts as played.
