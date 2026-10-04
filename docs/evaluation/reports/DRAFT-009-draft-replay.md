# DRAFT-009: our draft values vs last season's (2025-26, leak-free)

Generated 2026-09-27 23:31 UTC by `python -m fantasy_pipeline draft-replay`.
Re-run 2026-09-28 after DEC-008's snake tie-break fix: every number reproduced exactly.
Pre-registered in the task file (commit 3a2535d) before any result; it replaces the
hindsight table in DEC-007's report.

**Leak guards**: both strategies' values use seasons up to 2024-25 only (plus the 2025-26
pre-season for ours), opening-night teams for the minutes model, a pool of 2024-25
players + the 2025 draft class, and no injury overrides. The season is replayed on the
real 2025-26 games.

**Setup**: 40 random seat orders; 16-team snake, 14 rounds;
seats alternate the two strategies; daily lineups by the DEC-007 optimiser;
score = weekly all-play H2H share of the 9 categories.

## Result

| strategy | mean all-play category share | top 5 by its values |
|---|---|---|
| ours (H1+aging+M1pre) | 0.554 | Shai Gilgeous-Alexander, Nikola Jokić, Victor Wembanyama, Tyrese Haliburton, Anthony Edwards |
| last season (B0) | 0.446 | Nikola Jokić, Shai Gilgeous-Alexander, Tyrese Haliburton, Karl-Anthony Towns, James Harden |

**Difference (ours - last season): +0.107** (95 % CI +0.103 to +0.112, bootstrap over drafts [R-54]).
Ours averaged higher in **100%** of the drafts (per-draft differences +0.084 to +0.140).

0.500 is an average team. +0.01 is about one extra category won per opponent every 11 weeks.

## Why the gap is so large (diagnosis, run after the result)

- **The baseline punishes last season's injuries.** "Last season" values a player by his 2024-25
  totals, so a missed half-season looks like a bad player. Our method shrinks games played toward
  normal (Marcel games). The biggest disagreements are bounce-back players:

  | player | 2024-25 games | our rank | baseline rank | 2025-26 games |
  |---|---|---|---|---|
  | Chet Holmgren | 32 | 61 | 211 | 69 |
  | Kawhi Leonard | 37 | 77 | 177 | 65 |
  | Joel Embiid | 19 | 84 | 311 | 38 |

  The baseline instead reached for durable role players whose value came mostly from 80-game
  seasons (Keon Ellis, Royce O'Neale, Kris Dunn).
- **Leak check**: had our values seen 2025-26, our picks would have stayed healthier. They didn't:
  the top 150 by our values averaged **56.9** games in 2025-26 vs **56.7** for the baseline's. The
  edge comes from judging per-game quality and not over-reacting to one injury season.
- **Caveats**: "last season" is a weak baseline, and the 2025 rookies get the same draft-slot prior in
  both strategies. A tougher follow-up is Marcel (B1), which also shrinks games. Positions come from
  current rosters, and the minutes model's opening team is a player's first 2025-26 team (for the
  few players traded before their debut, that's slightly after opening night).
