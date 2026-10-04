# DRAFT-002 backtest: preseason projections

Generated 2026-09-25 05:33 UTC by `python -m fantasy_pipeline draft-backtest` from `intermediate.int_player_season` (BigQuery dev).
Design: docs/architecture/ml-methodology-plan.md §4 (G-21), amended by G-21b / D-51. Every fold builds projections only from seasons before its target (rolling origin [R-50, R-51]).

Methods:
- **B0**: last season per game (naive baseline [R-52]).
- **B1**: Marcel [R-13] (practitioner). 5/4/3 recency weights, regression of 1,000 minutes to the league rate, Marcel age factor, Marcel games.
- **C1**: empirical Bayes [R-11, R-12]. Gamma-Poisson per per-minute stat and Beta-Binomial per shooting %, prior strengths estimated from the 5 prior seasons; 3-year weighted minutes; Marcel games.
- **C1+aging**: C1 with a per-stat age curve estimated from our data (delta method, U6 ablation).
- **H1**: C1 per-minute rates x last season's minutes per game x Marcel games (G-21b / D-51).

**Primary metric (G-21b)**: Spearman rank correlation between projected and realised **season-total** 9-cat value (per game x games; z-sum, FG%/FT% as volume-weighted impact, TO negative), over every player who played the target season and has a projection from every method. Per-game MAE uses players with >= 20 games. CIs: paired bootstrap over players, 2,000 resamples [R-54].

## Decision (primary fold 2025-26): ship **H1+aging**

- H1 vs B0 (2025-26): season-total rank +0.014 (95 % CI -0.004 to +0.032); better MAE on 11/11 stats (need 8); pooled over 8 folds +0.013 (95 % CI +0.006 to +0.020), positive in 8/8 folds -> PASS
- H1+aging vs H1: pooled season-total rank +0.002 (95 % CI +0.001 to +0.003), positive in 8/8 folds; MAE as good or better on 10/11 stats (need 6) -> REPLACES H1

## Pooled over all folds: season-total value rank difference (every comparison)

Bootstrap stratified by fold (players resampled within each fold, fold means averaged) [R-54]. Positive = the first method ranks realised value better.

| comparison | mean diff | 95 % CI | folds positive |
|---|---|---|---|
| B1 vs B0 | +0.003 | -0.006 to +0.012 | 4/8 |
| C1 vs B0 | +0.001 | -0.008 to +0.009 | 3/8 |
| C1+aging vs B0 | +0.005 | -0.004 to +0.013 | 4/8 |
| H1 vs B0 | +0.013 | +0.006 to +0.020 | 8/8 |
| H1+aging vs B0 | +0.016 | +0.009 to +0.023 | 8/8 |
| C1 vs B1 | -0.002 | -0.005 to +0.000 | 0/8 |
| C1+aging vs B1 | +0.002 | -0.000 to +0.004 | 6/8 |
| H1 vs B1 | +0.010 | +0.005 to +0.015 | 7/8 |
| H1+aging vs B1 | +0.013 | +0.007 to +0.018 | 8/8 |
| H1 vs C1 | +0.012 | +0.008 to +0.017 | 7/8 |
| H1+aging vs H1 | +0.002 | +0.001 to +0.003 | 8/8 |

## All folds: season-total value rank correlation (primary)

| target | players | B0 | B1 | C1 | C1+aging | H1 | H1+aging | H1 - B0 (95 % CI) |
|---|---|---|---|---|---|---|---|---|
| 2018-19 | 412 | 0.650 | 0.664 | 0.664 | 0.669 | 0.662 | 0.664 | +0.013 (-0.017, +0.044) |
| 2019-20 | 400 | 0.691 | 0.683 | 0.682 | 0.686 | 0.698 | 0.699 | +0.007 (-0.010, +0.025) |
| 2020-21 | 435 | 0.707 | 0.724 | 0.723 | 0.726 | 0.733 | 0.734 | +0.026 (+0.007, +0.050) |
| 2021-22 | 450 | 0.734 | 0.734 | 0.732 | 0.738 | 0.741 | 0.746 | +0.007 (-0.011, +0.024) |
| 2022-23 | 433 | 0.712 | 0.723 | 0.717 | 0.722 | 0.734 | 0.737 | +0.021 (+0.000, +0.046) |
| 2023-24 | 450 | 0.791 | 0.787 | 0.782 | 0.784 | 0.795 | 0.796 | +0.004 (-0.011, +0.019) |
| 2024-25 | 447 | 0.756 | 0.755 | 0.753 | 0.756 | 0.770 | 0.772 | +0.014 (-0.002, +0.031) |
| 2025-26 | 464 | 0.651 | 0.647 | 0.646 | 0.651 | 0.665 | 0.668 | +0.014 (-0.004, +0.032) |

## All folds: per-game value rank correlation (secondary)

| target | players | B0 | B1 | C1 | C1+aging | H1 | H1+aging |
|---|---|---|---|---|---|---|---|
| 2018-19 | 361 | 0.708 | 0.690 | 0.690 | 0.697 | 0.702 | 0.703 |
| 2019-20 | 347 | 0.744 | 0.720 | 0.721 | 0.726 | 0.736 | 0.738 |
| 2020-21 | 374 | 0.770 | 0.766 | 0.768 | 0.773 | 0.773 | 0.775 |
| 2021-22 | 374 | 0.767 | 0.742 | 0.735 | 0.745 | 0.763 | 0.770 |
| 2022-23 | 380 | 0.769 | 0.756 | 0.754 | 0.762 | 0.772 | 0.778 |
| 2023-24 | 386 | 0.785 | 0.773 | 0.772 | 0.778 | 0.794 | 0.798 |
| 2024-25 | 390 | 0.839 | 0.815 | 0.811 | 0.816 | 0.837 | 0.840 |
| 2025-26 | 390 | 0.745 | 0.710 | 0.717 | 0.722 | 0.734 | 0.737 |

## Diagnostic: per-minute rates x the realised minutes (rate quality alone)

This isolates the per-minute rate model from the minutes projection: with the true minutes, the shrunk rates rank far better than last season's, so minutes are the weak component (why H1 takes last season's minutes).

| target | players | B0 | B1 | C1 | C1+aging | H1 | H1+aging |
|---|---|---|---|---|---|---|---|
| 2018-19 | 361 | 0.890 | 0.938 | 0.931 | 0.931 | 0.931 | 0.931 |
| 2019-20 | 347 | 0.904 | 0.938 | 0.932 | 0.934 | 0.932 | 0.934 |
| 2020-21 | 374 | 0.885 | 0.930 | 0.920 | 0.923 | 0.920 | 0.923 |
| 2021-22 | 374 | 0.918 | 0.951 | 0.941 | 0.945 | 0.941 | 0.945 |
| 2022-23 | 380 | 0.931 | 0.958 | 0.953 | 0.955 | 0.953 | 0.955 |
| 2023-24 | 386 | 0.924 | 0.959 | 0.955 | 0.956 | 0.955 | 0.956 |
| 2024-25 | 390 | 0.930 | 0.949 | 0.949 | 0.951 | 0.949 | 0.951 |
| 2025-26 | 390 | 0.920 | 0.947 | 0.940 | 0.943 | 0.940 | 0.943 |

## Primary fold 2025-26: per-stat MAE (per game; lower is better, best in bold)

| stat | B0 | B1 | C1 | C1+aging | H1 | H1+aging | H1 - B0 (95 % CI) | C1 - B0 (95 % CI) | H1 - C1 (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|
| pts | 2.821 | 2.752 | 2.819 | 2.748 | 2.731 | **2.683** | -0.090 (-0.179, +0.005) | -0.002 (-0.145, +0.138) | -0.088 (-0.190, +0.017) |
| reb | 0.961 | 1.029 | 0.959 | 0.944 | 0.950 | **0.938** | -0.010 (-0.044, +0.022) | -0.002 (-0.063, +0.054) | -0.008 (-0.056, +0.044) |
| ast | 0.719 | 0.767 | 0.748 | 0.730 | 0.708 | **0.693** | -0.010 (-0.040, +0.017) | +0.030 (-0.012, +0.071) | -0.040 (-0.065, -0.013) |
| stl | 0.230 | 0.213 | 0.209 | **0.207** | 0.212 | 0.211 | -0.019 (-0.031, -0.006) | -0.022 (-0.036, -0.007) | +0.003 (-0.005, +0.012) |
| blk | 0.168 | 0.164 | 0.157 | **0.156** | 0.161 | 0.161 | -0.006 (-0.015, +0.002) | -0.011 (-0.022, -0.002) | +0.005 (-0.001, +0.011) |
| fg3m | 0.373 | 0.402 | 0.377 | 0.379 | **0.363** | 0.367 | -0.009 (-0.027, +0.010) | +0.004 (-0.017, +0.027) | -0.014 (-0.029, +0.000) |
| tov | 0.378 | 0.356 | 0.363 | 0.358 | 0.354 | **0.352** | -0.025 (-0.040, -0.008) | -0.016 (-0.037, +0.006) | -0.009 (-0.022, +0.004) |
| fgm | 1.024 | 0.987 | 1.016 | 0.985 | 0.985 | **0.968** | -0.038 (-0.074, -0.003) | -0.008 (-0.059, +0.042) | -0.030 (-0.068, +0.009) |
| fga | 2.062 | 1.988 | 2.061 | 2.022 | 1.986 | **1.971** | -0.076 (-0.144, -0.008) | -0.000 (-0.106, +0.102) | -0.076 (-0.157, +0.009) |
| ftm | 0.599 | 0.606 | 0.600 | 0.586 | 0.592 | **0.583** | -0.007 (-0.035, +0.022) | +0.001 (-0.036, +0.036) | -0.007 (-0.023, +0.009) |
| fta | 0.734 | 0.737 | 0.733 | **0.714** | 0.727 | 0.718 | -0.007 (-0.041, +0.029) | -0.001 (-0.043, +0.041) | -0.006 (-0.025, +0.015) |
| fg3a | 0.942 | 1.010 | 0.949 | 0.959 | **0.923** | 0.939 | -0.019 (-0.062, +0.024) | +0.007 (-0.049, +0.065) | -0.026 (-0.066, +0.013) |
| mpg | **4.603** | 4.760 | 4.760 | 4.760 | **4.603** | **4.603** | +0.000 (+0.000, +0.000) | +0.158 (-0.092, +0.395) | -0.158 (-0.395, +0.092) |
| games | 16.803 | **14.203** | **14.203** | **14.203** | **14.203** | **14.203** | -2.599 (-3.428, -1.772) | -2.599 (-3.428, -1.772) | +0.000 (+0.000, +0.000) |

Top-224 overlap on season-total value (share of the realised top 224 that each method also ranks top 224), 2025-26: B0 0.73, B1 0.74, C1 0.73, C1+aging 0.73, H1 0.73, H1+aging 0.74

## Players with no NBA history (U4: rookie prior by draft bucket vs one league-average rookie line)

57 players, 2025-26.

| stat | rookie_prior | league_avg_rookie |
|---|---|---|
| fgm | 0.983 | 1.402 |
| fga | 2.231 | 3.088 |
| fg3m | 0.459 | 0.487 |
| fg3a | 1.274 | 1.336 |
| ftm | 0.537 | 0.646 |
| fta | 0.648 | 0.802 |
| reb | 1.201 | 1.468 |
| ast | 0.953 | 1.096 |
| stl | 0.244 | 0.263 |
| blk | 0.235 | 0.255 |
| tov | 0.435 | 0.535 |
| pts | 2.671 | 3.687 |

## Calibration: 80 % interval coverage (sds from the previous fold's residuals; target 75-85 %)

ast 85%, blk 84%, fg3a 83%, fg3m 81%, fga 78%, fgm 77%, fta 75%, ftm 75%, games 80%, mpg 81%, pts 78%, reb 84%, stl 81%, tov 83%
