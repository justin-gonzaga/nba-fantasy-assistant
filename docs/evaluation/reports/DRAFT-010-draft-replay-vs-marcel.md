# Draft replay: our draft values vs Marcel (B1) (2025-26, leak-free)

Generated 2026-09-28 00:27 UTC by `python -m fantasy_pipeline draft-replay`; re-run 2026-09-28 after DEC-008's
snake tie-break fix (ties to the lowest player id): the numbers below moved by <= 0.003, same verdict.
Pre-registered before any result: DRAFT-009 (commit 3a2535d, baseline B0) and DRAFT-010
(commit b94f839, baseline B1).

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
| ours (H1+aging+M1pre) | 0.545 | Shai Gilgeous-Alexander, Nikola Jokić, Victor Wembanyama, Tyrese Haliburton, Anthony Edwards |
| Marcel (B1) | 0.455 | Nikola Jokić, Shai Gilgeous-Alexander, Tyrese Haliburton, Jayson Tatum, Victor Wembanyama |

**Difference (ours - Marcel (B1)): +0.090** (95 % CI +0.085 to +0.095, bootstrap over drafts [R-54]).
Ours averaged higher in **100%** of the drafts
(per-draft differences +0.052 to +0.139).

0.500 is an average team. +0.01 is about one extra category won per opponent
every 11 weeks.

## Why ours still wins against Marcel (diagnosis, run after the result)

Marcel also shrinks games toward normal, so the injury-season effect from DRAFT-009 mostly disappears.
The remaining gap is **role growth**. Our values come from the minutes model with the pre-season role
signal (DRAFT-007/008) and an age curve, so they rank rising young players much higher:

| player | our rank | Marcel rank | 2025-26 games |
|---|---|---|---|
| Donovan Clingan | 78 | 190 | 77 |
| Matas Buzelis | 95 | 211 | 77 |
| Kel'el Ware | 98 | 166 | 77 |
| Jalen Johnson | 101 | 170 | 72 |

Marcel keeps ageing veterans higher (Bradley Beal, Al Horford, Dejounte Murray, Kyle Kuzma, Bogdan
Bogdanović). **Leak check**: both top-150s played the same 2025-26 games (56.9 vs 56.8), so the edge
isn't foreknowledge of health.
