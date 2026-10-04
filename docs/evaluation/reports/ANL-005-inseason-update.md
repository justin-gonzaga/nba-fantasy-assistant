# ANL-005: updating pre-season projections with the season so far

Generated 2026-09-28 00:31 UTC by
`python -m fantasy_pipeline inseason-backtest`.
Pre-registered in the task file (commit f6e1775) before any result.

**Setup**: leak-free pre-season priors (H1+aging+M1pre) for 2023-24, 2024-25 and 2025-26;
player-weeks with a prior and >= 1 earlier game: 22,101 selection weeks pick
k per stat; 4,540 holdout player-weeks (from 19 Jan 2026) score. Weekly MAE
given the games played; week-block bootstrap CIs [R-55]; ✅ = CI below 0.

## Verdict

**SHIPS**: the week projection blends the prior with the season so far. The blend beats the frozen prior on **9 of 9** categories (rule: >= 6, with no
category more than 2 % worse).

## Holdout MAE (lower is better)

| category | k (games of prior) | MAE frozen prior | MAE season-to-date | MAE blend | blend - prior (95 % CI) |
|---|---|---|---|---|---|
| pts | 3.0 | 10.6796 | 8.9805 | 8.9503 | -1.7293 (-1.9944 to -1.4445) ✅ |
| reb | 5.0 | 3.9862 | 3.4996 | 3.4761 | -0.5101 (-0.6084 to -0.4015) ✅ |
| ast | 3.0 | 3.0215 | 2.5102 | 2.5026 | -0.5189 (-0.6168 to -0.4173) ✅ |
| stl | 20.0 | 1.2983 | 1.2568 | 1.2435 | -0.0548 (-0.0663 to -0.0418) ✅ |
| blk | 8.0 | 0.9335 | 0.8762 | 0.8794 | -0.0541 (-0.0618 to -0.0463) ✅ |
| fg3m | 5.0 | 1.8225 | 1.6155 | 1.6118 | -0.2107 (-0.2580 to -0.1678) ✅ |
| tov | 8.0 | 1.7440 | 1.5781 | 1.5694 | -0.1746 (-0.2002 to -0.1427) ✅ |
| fg_pct | (3.0, 2.0) | 0.1213 | 0.1212 | 0.1187 | -0.0026 (-0.0044 to -0.0010) ✅ |
| ft_pct | (8.0, 5.0) | 0.1753 | 0.1784 | 0.1726 | -0.0027 (-0.0048 to -0.0006) ✅ |

## What it means

- The prior is worth only a few games (k = 3 to 8 for most stats, 20 for steals): the season's own
  numbers take over quickly, especially for points, rebounds and assists. Steals are noisy
  per game, so the prior keeps more weight.
- On the holdout (second half), season-to-date alone is almost as good as the blend, because most
  of the season has been played by then. The blend matters most early in the season, which the
  selection weeks cover but the holdout doesn't: a caveat on how early-season gains are measured.
- Shipped: `fantasy_models.inseason.K_SHIPPED`; `week-projection` blends the draft projection with
  each player's stored season-to-date totals (nothing changes until games are played).
