# DEC-002: negative-binomial vs Poisson weekly totals

Generated 2026-09-27 22:11 UTC by `python -m fantasy_pipeline dist-backtest`.
The test was pre-registered in the task file (commit ac54390) before any result: see DEC-002,
"Pre-registered test".

**Setup**: player-weeks (Mon-Sun) of 2023-24, 2024-25, 2025-26 with >= 5 earlier games that season.
Both models share the mean (season-to-date per-game average x games played that week), so only
the distribution shape differs. Dispersions come from **20,783 selection
player-weeks** (before 19 Jan 2026); scores are on **4,616 holdout player-weeks**
(from 19 Jan 2026). CRPS [R-41]; randomized PIT [R-43, R-44]; 95 % CIs from a bootstrap over
whole weeks (2,000 resamples) [R-55]. ✅ = CI entirely below 0.

## Verdict

**SHIPS**: the simulation uses negative-binomial totals.
NB is better (CI below 0) on **7 of 9** categories (rule: >= 6); mean PIT deviation
Poisson 0.0225 vs NB 0.0093 (rule: NB no worse).

## Holdout scores (lower is better)

| category | holdout player-weeks | CRPS Poisson | CRPS NB | NB - Poisson (95 % CI) | PIT dev. Poisson | PIT dev. NB |
|---|---|---|---|---|---|---|
| pts | 4,616 | 7.0981 | 6.6316 | -0.4665 (-0.5258 to -0.4108) ✅ | 0.0755 | 0.0260 |
| reb | 4,616 | 2.5696 | 2.5301 | -0.0395 (-0.0485 to -0.0303) ✅ | 0.0299 | 0.0071 |
| ast | 4,616 | 1.8361 | 1.8170 | -0.0191 (-0.0291 to -0.0085) ✅ | 0.0249 | 0.0103 |
| stl | 4,616 | 0.8648 | 0.8611 | -0.0037 (-0.0055 to -0.0017) ✅ | 0.0126 | 0.0056 |
| blk | 4,616 | 0.5887 | 0.5862 | -0.0025 (-0.0041 to -0.0007) ✅ | 0.0086 | 0.0057 |
| fg3m | 4,616 | 1.1381 | 1.1272 | -0.0109 (-0.0153 to -0.0068) ✅ | 0.0199 | 0.0077 |
| tov | 4,616 | 1.1097 | 1.1064 | -0.0032 (-0.0060 to -0.0009) ✅ | 0.0153 | 0.0086 |
| fg_pct | 4,486 | 0.0854 | 0.0855 | +0.0001 (-0.0001 to +0.0003) | 0.0050 | 0.0055 |
| ft_pct | 3,503 | 0.1256 | 0.1262 | +0.0006 (+0.0004 to +0.0007) | 0.0106 | 0.0070 |

## Dispersions (selection weeks)

Per-game negative-binomial size r (variance = m + m²/r; ∞ = Poisson), and the
beta-binomial correlation for makes given attempts.

| parameter | estimate |
|---|---|
| pts | 3.872 |
| reb | 4.663 |
| ast | 4.225 |
| stl | 2.666 |
| blk | 2.266 |
| fg3m | 3.103 |
| tov | 5.343 |
| fg_pct_attempts | 6.865 |
| fg_pct_rho | 0.004 |
| ft_pct_attempts | 2.057 |
| ft_pct_rho | 0.035 |

## Notes

- All seven counting categories improve, points most (CRPS 7.10 → 6.63), and calibration improves
  in 8 of 9 (the PIT deviation roughly halves). Poisson is too narrow: players' weeks vary more
  than a Poisson count allows.
- **FT%** is slightly worse with the beta-binomial (+0.0006, CI above 0) and FG% is unchanged. The
  pre-registered rule decides for the model as a whole, so it ships as registered; choosing per
  category after seeing the holdout would be selection on the holdout. Follow-up: re-test the
  percentage component on 2026-27 data (a new holdout).
- The fitted parameters live in `fantasy_models.distributions` (NB_SIZE, MAKES_RHO). The daily
  brief's category win chances now use these variances.
