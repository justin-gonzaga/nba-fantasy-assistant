# ANL-010 — Team and coach effects

Generated 2026-10-03 10:20 UTC. Residuals: the shipped pre-season method
(H1+aging+M1pre), leak-free, targets 2023-24, 2024-25, 2025-26; 1298 player-seasons with
≥ 20 games. Value = the 9-cat z-sum of per-game stats
(`preseason_backtest.value_score`), actual minus projected.

Flags (share of player-seasons): moved 20.9%, new coach 14.6%, mean
|pace change| among movers 2.03, mean usage freed 25.3%.

## Decision

Pre-registered: a flag explains ≥ 2 % of the value-residual variance, Holm p < 0.05.

**NO-GO**: no context flag meets the rule.

## Q5 — Do the model's errors line up with context changes? (OLS on the value residual)

| Flag | Effect on value residual [95 % CI] | Share of variance | p | Holm p |
|---|---|---|---|---|
| moved | -0.258 [-0.550, +0.034] | 0.23% | 0.0834 | 0.333 |
| new_coach | -0.091 [-0.422, +0.240] | 0.02% | 0.591 | 1 |
| pace_change | -0.016 [-0.116, +0.084] | 0.01% | 0.751 | 1 |
| usage_freed | +0.397 [-0.489, +1.283] | 0.06% | 0.38 | 1 |


### Sensitivity: without `new_coach` (added after review, not pre-registered)

`new_coach` compares end-of-season coaches, so a coach fired during t counts as new
for t: information from after the draft. Those firings follow bad seasons, so the leak
can only make the flag look more predictive. Refitting with the three draft-time flags
only:

| Flag | Effect [95 % CI] | Share of variance | p | Holm p |
|---|---|---|---|---|
| moved | -0.261 [-0.553, +0.030] | 0.24% | 0.079 | 0.237 |
| pace_change | -0.015 [-0.115, +0.084] | 0.01% | 0.761 | 0.817 |
| usage_freed | +0.371 [-0.510, +1.252] | 0.05% | 0.408 | 0.817 |

Decision without `new_coach`: **NO-GO**.

## Q1 — How much of the season-to-season per-36 change does the new team explain?

R² of team-season means on the change, against shuffled team labels (chance).

| Stat | R² | Chance | Excess | Player pairs |
|---|---|---|---|---|
| pts | 0.162 | 0.105 | +0.057 | 2868 |
| reb | 0.165 | 0.104 | +0.061 | 2868 |
| ast | 0.190 | 0.104 | +0.086 | 2868 |
| fg3m | 0.158 | 0.104 | +0.054 | 2868 |
| mpg | 0.132 | 0.104 | +0.028 | 2868 |

## Q2 — Movers vs stayers (value residual, mean difference [95 % bootstrap CI])

-0.236 [-0.512, +0.039], p = 0.0937.

## Q3 — New head coach, players who stayed (value residual, mean difference)

-0.118 [-0.482, +0.247], p = 0.536.

## Q4 — Pace change for movers (points-per-game residual per unit of pace change)

+0.023 [-0.113, +0.159] PTS per game per possession of pace,
p = 0.738.

## Caveats

- One head coach per team-season, the end-of-season one (DATA-038). A coach fired during
  season t therefore counts as a new coach for t, which was not known at the draft
  (see the sensitivity run); a summer change followed by a mid-season one is still
  flagged correctly. The 10 team-seasons whose coach was fired after the season have no
  coach and count as no change.
- Usage freed attributes a traded player's shots to his last team; contract-year
  effort (R-116-R-118) is not controlled.
- Three target seasons; small effects can hide in the noise. The rule above was fixed
  before running.
