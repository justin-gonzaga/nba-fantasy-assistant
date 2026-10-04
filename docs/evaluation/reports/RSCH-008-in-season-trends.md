# In-season trends and the fantasy-playoff schedule (RSCH-008)

Generated 2026-10-02 15:11 UTC. Pre-registered in `docs/project/tasks/RSCH-008-in-season-trends-and-playoff-schedule.md`
(with the pre-run amendments). Seasons 2015-16 to 2025-26; 2019-20, 2020-21 excluded from pooled estimates.

## Q1: is a "second-half player" a repeatable trait?
Consecutive-season pairs (>= 20 games each half): **827** player-pairs.

| Change measured | r (season s vs s+1) | 95 % CI |
|---|---|---|
| per-game 9-cat value (after minus before the break) | +0.081 | +0.017 to +0.146 |
| per-36 value (skill, not role) | +0.025 | -0.046 to +0.093 |

**Decision by the rule** (noise if the CI includes 0 or r < 0.15): **noise: don't model individual second-half tendencies.**

## Q2: late-season rest and tanking (after 1 Mar)
Extra games missed after 1 Mar relative to the player's own earlier share, and the mpg
change; bootstrap 95 % CIs. Material = >= 2 extra games or >= 3 mpg, CI excluding 0.

| Context on 1 Mar | Role | n | Extra games missed (95 % CI) | mpg change (95 % CI) | Material |
|---|---|---|---|---|---|
| bottom-6 | rotation | 218 | +3.72 (+2.84 to +4.69) | -0.57 (-1.31 to +0.14) | yes |
| bottom-6 | star | 62 | +6.18 (+4.57 to +7.72) | -0.70 (-1.48 to +0.08) | yes |
| bottom-6 | young | 286 | +0.34 (-0.49 to +1.17) | +4.33 (+3.69 to +4.99) | yes |
| contender | rotation | 147 | +0.25 (-0.43 to +0.96) | -0.94 (-1.54 to -0.31) | no |
| contender | star | 105 | +2.38 (+1.49 to +3.32) | -0.82 (-1.34 to -0.38) | yes |
| contender | young | 87 | +0.89 (-0.10 to +1.95) | +1.50 (+0.52 to +2.52) | no |
| mid-race | rotation | 837 | +1.31 (+0.90 to +1.70) | -1.06 (-1.36 to -0.76) | no |
| mid-race | star | 366 | +1.64 (+1.06 to +2.21) | -0.68 (-0.96 to -0.42) | no |
| mid-race | young | 615 | +0.16 (-0.32 to +0.65) | +1.59 (+1.08 to +2.10) | no |

## Q3: fantasy-playoff schedule (league weeks 18-20: 1-21 Mar 2027)
Team games in those weeks: 9 to 12 (mean 10.3).

| Playoff-week weight w | Top-150 players moving >= 10 ranks | Biggest risers |
|---|---|---|
| 1 | 0 | Victor Wembanyama +0, Nikola Jokić +0, Shai Gilgeous-Alexander +0 |
| 2 | 0 | Donovan Clingan +2, Jalen Johnson +2, Jalen Williams +2 |
| 3 | 0 | Kevin Porter Jr. +4, Royce O'Neale +4, Jaime Jaquez Jr. +3 |

**Decision by the rule** (w = 2 moving >= 15 of the top 150 by >= 10 ranks): **0 move: not material; no model change.**

## Literature
First/second-half splits regress strongly to the mean in baseball [R-106, R-107];
eliminated NBA teams rest healthy players more [R-108]. No peer-reviewed work on
fantasy-playoff schedule weighting exists (a gap; this report is the evidence).
See `docs/research/lit-in-season-trends.md`.
