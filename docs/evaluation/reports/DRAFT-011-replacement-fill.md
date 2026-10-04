# Missed games at replacement level (DRAFT-011, G-26 A)

Generated 2026-10-02 13:04 UTC by `python -m fantasy_pipeline repl-fill-replay`.
Pre-registered in `docs/project/tasks/DRAFT-011-replacement-fill-missed-games.md` before any run.

## Replay (2025-26, leak-free, 40 drafts, 16 teams, all-play share)
Strategy A = A (missed games at replacement); B = current (missed games = 0). Difference = A - B.

| Replay | Difference | 95 % CI | A ahead |
|---|---|---|---|
| **with IL replacements (3 slots), decides** | -0.0442 | -0.0501 to -0.0381 | 2% of 40 |
| without replacements (reported only) | -0.0521 | -0.0581 to -0.0461 | 0% of 40 |

**Decision by the rule**: KEEP the current values (ship only if the difference with IL replacements is > 0 and its CI lower bound > 0).

Caveat: one season (2025-26). The 95 % CI is over draft-seat randomness within this single season's replay, not season-to-season variation; a different season could differ.

## 2026-27 values: top 25 with replacement fill
| Rank (A) | Player | $ (A) | Rank before | $ before |
|---|---|---|---|---|
| 1 | Victor Wembanyama | 81 | 1 | 74 |
| 2 | Nikola Jokić | 67 | 2 | 63 |
| 3 | Shai Gilgeous-Alexander | 65 | 3 | 63 |
| 4 | Luka Dončić | 53 | 4 | 49 |
| 5 | Tyrese Maxey | 47 | 5 | 45 |
| 6 | Scottie Barnes | 40 | 6 | 43 |
| 7 | Donovan Mitchell | 40 | 7 | 40 |
| 8 | Jamal Murray | 38 | 8 | 40 |
| 9 | Chet Holmgren | 38 | 10 | 36 |
| 10 | Cade Cunningham | 37 | 11 | 36 |
| 11 | Jalen Johnson | 36 | 13 | 36 |
| 12 | Anthony Edwards | 36 | 15 | 35 |
| 13 | Karl-Anthony Towns | 35 | 9 | 37 |
| 14 | Kawhi Leonard | 35 | 21 | 32 |
| 15 | Cooper Flagg | 33 | 24 | 31 |
| 16 | Donovan Clingan | 34 | 12 | 36 |
| 17 | Kevin Durant | 33 | 14 | 35 |
| 18 | LaMelo Ball | 33 | 18 | 33 |
| 19 | Evan Mobley | 32 | 23 | 31 |
| 20 | Jalen Duren | 31 | 20 | 33 |
| 21 | Derrick White | 31 | 16 | 34 |
| 22 | Trey Murphy III | 31 | 27 | 30 |
| 23 | James Harden | 31 | 22 | 32 |
| 24 | Desmond Bane | 30 | 17 | 34 |
| 25 | Amen Thompson | 29 | 19 | 33 |

Giannis Antetokounmpo (the trigger): rank 118 → 66, $10 → $17.
