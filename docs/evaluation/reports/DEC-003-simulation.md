# DEC-003: Monte Carlo simulation vs the normal approximation

Generated 2026-09-27 23:08 UTC by `python -m fantasy_pipeline sim-backtest`.
The test was pre-registered in the task file (commit 8684b8a) before any result.

**Setup**: 2025-26 holdout weeks (from 19 Jan 2026), 100 random matchups per
week of two 10-player teams from the top 224 by season-to-date points per game:
**1,200 matchups**, 10,800 category outcomes. Both methods
share the means (season-to-date averages x games played); the outcome is who actually won each
category. Brier score [R-40]; 95 % CI from a bootstrap over whole weeks (2,000 resamples) [R-55].

## Verdict

**Does not ship**: the brief keeps the normal approximation.
Pooled Brier difference (simulation - normal) **-0.0001**
(95 % CI -0.0003 to +0.0000); rule: CI entirely below 0.

## Brier by category (lower is better; a coin flip scores 0.25)

| category | normal approx. | simulation | difference |
|---|---|---|---|
| ast | 0.1270 | 0.1271 | +0.0001 |
| blk | 0.1673 | 0.1674 | +0.0001 |
| fg3m | 0.1535 | 0.1533 | -0.0002 |
| fg_pct | 0.2218 | 0.2215 | -0.0003 |
| ft_pct | 0.2209 | 0.2206 | -0.0004 |
| pts | 0.1351 | 0.1350 | -0.0001 |
| reb | 0.1242 | 0.1239 | -0.0003 |
| stl | 0.1874 | 0.1872 | -0.0002 |
| tov | 0.1707 | 0.1709 | +0.0002 |

## Reliability of the simulation's probabilities

| predicted bin | mean predicted | observed win rate | outcomes |
|---|---|---|---|
| 0.0-0.1 | 0.042 | 0.051 | 1,149 |
| 0.1-0.2 | 0.151 | 0.155 | 950 |
| 0.2-0.3 | 0.250 | 0.276 | 1,019 |
| 0.3-0.4 | 0.350 | 0.378 | 1,097 |
| 0.4-0.5 | 0.452 | 0.461 | 1,254 |
| 0.5-0.6 | 0.549 | 0.530 | 1,273 |
| 0.6-0.7 | 0.648 | 0.660 | 1,165 |
| 0.7-0.8 | 0.749 | 0.757 | 979 |
| 0.8-0.9 | 0.849 | 0.839 | 899 |
| 0.9-1.0 | 0.958 | 0.962 | 1,015 |

## Monte Carlo precision (U14)

Mean standard error of expected categories won at 2,000 draws: **0.0271**
(target < 0.02 at 10,000 draws; at 2,000 draws the target scales to < 0.045).

## What it means

- **A tie.** With DEC-002's negative-binomial variances, the normal approximation is already
  well calibrated: a 10-player weekly total sums many draws, so it's close to normal. The
  simulation's reliability is also good (e.g. predicted 0.958 vs observed 0.962 in the top bin).
- **The brief keeps the normal approximation** for single-category win chances (faster, same accuracy).
- **The simulator stays** for what the approximation can't do: the chance of winning the week
  (joint outcomes), and comparing two lineups or add/drops on the same random draws (common random
  numbers, DEC-007/008).
- U14: the Monte Carlo standard error at 2,000 draws is 0.027 categories, within the target.
