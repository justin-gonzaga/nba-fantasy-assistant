# Returners: games floor after a lost season (DRAFT-022, G-32)

Generated 2026-10-04 01:10 UTC by `python -m fantasy_pipeline returners-eval`.
Pre-registered in `docs/project/tasks/DRAFT-022-return-from-lost-season-games.md` and
`docs/architecture/ml-methodology-plan.md` section 25 (commit 4a4ee78) before any run.

## Decision: KEEP the current method (use cited override rows)

| Check | Result | Value | Rule |
|---|---|---|---|
| 1 Accuracy | pass | MAE current 0.307, R 0.228; CI of (current - R) +0.013 to +0.139 | CI lower bound > 0 |
| 2 Calibration | pass | gap 0.063 | <= 0.08 |
| 3 Non-inferiority (replay, IL) | FAIL | CI lower bound -0.0103 | > -0.005 |

## Folds (30 holdout cohort player-seasons, expanding window)

Games fraction (games played / team games). Bootstrap resamples player-seasons (paired),
2000 draws, seed 0 [R-54]. The folds are not independent of the Lillard observation and
partly reuse data seen when the cohort was counted (disclosed in the pre-registration).

| Fold season | n | realised | current | R |
|---|---|---|---|---|
| 2021-22 | 5 | 0.50 | 0.38 | 0.57 |
| 2022-23 | 10 | 0.73 | 0.37 | 0.56 |
| 2023-24 | 6 | 0.55 | 0.38 | 0.60 |
| 2024-25 | 4 | 0.70 | 0.39 | 0.59 |
| 2025-26 | 5 | 0.66 | 0.42 | 0.60 |

## Reported, not deciding
- Aged 33 or more: n = 3: realised 0.72, current 0.40, R 0.58.
- Lillard (a fact, not a target): rank 221, $1 before, rank 35, $26 with R.
- Players in two consecutive lost seasons are outside the cohort by definition.

---

# Replay and 2026-27 values: returners games floor (DRAFT-022, G-32)

Generated 2026-10-04 01:10 UTC by `python -m fantasy_pipeline returners-eval`.
Pre-registered in `docs/project/tasks/DRAFT-022-return-from-lost-season-games.md` before any run.

## Replay (2025-26, leak-free, 40 drafts, 16 teams, all-play share)
Strategy A = R (games floor for returners); B = current (H1+aging+M1pre). Difference = A - B.

| Replay | Difference | 95 % CI | A ahead |
|---|---|---|---|
| **with IL replacements (3 slots), decides** | +0.0047 | -0.0103 to +0.0192 | 50% of 40 |
| without replacements (reported only) | +0.0072 | -0.0078 to +0.0219 | 55% of 40 |

**Decision by the rule**: KEEP the current values (non-inferiority: check 3 passes if the CI lower bound with IL replacements is > -0.005).

Caveat: one season (2025-26). The 95 % CI is over draft-seat randomness within this single season's replay, not season-to-season variation; a different season could differ.

## 2026-27 values: top 25 with the candidate (A)
| Rank (A) | Player | $ (A) | Rank before | $ before |
|---|---|---|---|---|
| 1 | Victor Wembanyama | 71 | 1 | 74 |
| 2 | Nikola Jokić | 60 | 2 | 63 |
| 3 | Shai Gilgeous-Alexander | 60 | 3 | 63 |
| 4 | Luka Dončić | 47 | 4 | 49 |
| 5 | Tyrese Maxey | 43 | 5 | 45 |
| 6 | Scottie Barnes | 41 | 6 | 43 |
| 7 | Donovan Mitchell | 39 | 7 | 40 |
| 8 | Jamal Murray | 38 | 8 | 40 |
| 9 | Karl-Anthony Towns | 35 | 9 | 37 |
| 10 | Chet Holmgren | 34 | 10 | 36 |
| 11 | Donovan Clingan | 34 | 12 | 36 |
| 12 | Jalen Johnson | 34 | 13 | 36 |
| 13 | Cade Cunningham | 34 | 11 | 36 |
| 14 | Kevin Durant | 34 | 14 | 35 |
| 15 | Anthony Edwards | 33 | 15 | 35 |
| 16 | Derrick White | 33 | 16 | 34 |
| 17 | Tyrese Haliburton | 33 | 162 | 7 |
| 18 | Desmond Bane | 33 | 17 | 34 |
| 19 | LaMelo Ball | 31 | 18 | 33 |
| 20 | Amen Thompson | 31 | 19 | 33 |
| 21 | Kawhi Leonard | 31 | 21 | 32 |
| 22 | Jalen Duren | 31 | 20 | 33 |
| 23 | James Harden | 31 | 22 | 32 |
| 24 | Evan Mobley | 30 | 23 | 31 |
| 25 | Onyeka Okongwu | 29 | 25 | 31 |

Giannis Antetokounmpo (the trigger): rank 118 → 128, $10 → $9.
