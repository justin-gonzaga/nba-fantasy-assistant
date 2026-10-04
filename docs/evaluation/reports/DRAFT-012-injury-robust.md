# Injury-robust minutes and games (DRAFT-012, G-26 B)

Generated 2026-10-02 13:12 UTC by `python -m fantasy_pipeline robust-replay`.
Pre-registered in `docs/project/tasks/DRAFT-012-injury-robust-minutes-and-games.md` before any run.

## Replay (2025-26, leak-free, 40 drafts, 16 teams, all-play share)
Strategy A = B (injury-robust minutes + 3-season games); B = current (H1+aging+M1pre). Difference = A - B.

| Replay | Difference | 95 % CI | A ahead |
|---|---|---|---|
| **with IL replacements (3 slots), decides** | -0.1020 | -0.1076 to -0.0965 | 0% of 40 |
| without replacements (reported only) | -0.0894 | -0.0949 to -0.0838 | 0% of 40 |

**Decision by the rule**: KEEP the current values (non-inferiority: ship if the CI lower bound with IL replacements is > -0.005).

Caveat: one season (2025-26). The 95 % CI is over draft-seat randomness within this single season's replay, not season-to-season variation; a different season could differ.

## 2026-27 values: top 25 with the candidate (A)
| Rank (A) | Player | $ (A) | Rank before | $ before |
|---|---|---|---|---|
| 1 | Victor Wembanyama | 67 | 1 | 74 |
| 2 | Nikola Jokić | 62 | 2 | 63 |
| 3 | Shai Gilgeous-Alexander | 62 | 3 | 63 |
| 4 | Luka Dončić | 45 | 4 | 49 |
| 5 | Tyrese Maxey | 41 | 5 | 45 |
| 6 | Anthony Edwards | 37 | 15 | 35 |
| 7 | Scottie Barnes | 37 | 6 | 43 |
| 8 | Donovan Mitchell | 37 | 7 | 40 |
| 9 | Jamal Murray | 36 | 8 | 40 |
| 10 | Cade Cunningham | 34 | 11 | 36 |
| 11 | Derrick White | 33 | 16 | 34 |
| 12 | Karl-Anthony Towns | 33 | 9 | 37 |
| 13 | Kevin Durant | 33 | 14 | 35 |
| 14 | Chet Holmgren | 33 | 10 | 36 |
| 15 | James Harden | 32 | 22 | 32 |
| 16 | Jalen Duren | 32 | 20 | 33 |
| 17 | Amen Thompson | 31 | 19 | 33 |
| 18 | Bam Adebayo | 29 | 28 | 30 |
| 19 | Evan Mobley | 29 | 23 | 31 |
| 20 | Jalen Brunson | 29 | 26 | 30 |
| 21 | Onyeka Okongwu | 29 | 25 | 31 |
| 22 | Kawhi Leonard | 29 | 21 | 32 |
| 23 | Jalen Johnson | 29 | 13 | 36 |
| 24 | Alperen Sengun | 29 | 29 | 30 |
| 25 | Desmond Bane | 28 | 17 | 34 |

Giannis Antetokounmpo (the trigger): rank 118 → 60, $10 → $18.
