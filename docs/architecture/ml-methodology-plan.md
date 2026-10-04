# ML Methodology Plan

Version 0.1 · 2026-09-25 · **Part 1: the draft slice** (RSCH-005 → gate **G-21**). Part 2 (the in-season models) follows in RSCH-004.
Status: **APPROVED 2026-09-25 (G-21, D-49)**: all four recommendations selected (§6). Model code for the draft slice may now be written.

**Citation rule.** Every `[R-xx]` below is Verified in [`docs/research/ml-literature-review.md`](../research/ml-literature-review.md) (including §9, draft-slice refs). The status tags mean:
- **(practitioner)**: not peer-reviewed.
- **(preprint)**: not peer-reviewed.
- **(cross-sport)**: evidence from another sport.

None of these tagged sources is the sole basis for a gated choice. Choices with no peer-reviewed support are listed in §5, each with the empirical test that must justify it.

League context (docs/research/yahoo-api.md):
- H2H 9-cat: FG%, FT%, 3PTM, PTS, REB, AST, ST, BLK, TO.
- 16 teams, a $200 auction.
- 14 drafted slots per team (G×3, F×3, C, Util×3, BN×4; IL slots are not drafted), so **224 players are drafted**.

---

## 1. Component card: preseason projection (DRAFT-002)

| Field | Plan |
|---|---|
| **Problem** | For every player in `mart_draft_pool`, predict the 2026-27 regular season: games played, minutes per game, and per-minute rates for the counting stats (3PM, PTS, REB, AST, STL, BLK, TOV), plus **makes and attempts separately** for FG and FT (percentages are derived, never averaged). |
| **Target** | Season per-game values and totals, each with a mean and a standard deviation. |
| **Method: baseline (B1)** | **Marcel** [R-13] (practitioner): a weighted mean of the last 3 seasons (weights 5/4/3 on minutes-weighted rates), regressed toward the league mean by a fixed amount of playing time, plus a simple age adjustment. This is the minimum bar and the fallback. |
| **Method: candidate (C1)** | **Empirical-Bayes shrinkage of per-minute rates** [R-11, R-12]. Each player's rate is shrunk toward a position/role prior, with a per-stat shrinkage weight that depends on sample size (minutes/attempts): noisy stats (e.g. 3P%, FT% on low volume, STL, BLK) shrink more, stable ones (PTS/min, REB/min) less. [R-75] provides the framework (stability/discrimination meta-metrics) for measuring which stats are reliable at which sample size. The **weights are estimated from our data** (split-half reliability), not copied from blog tables (R-77 is practitioner precedent only). |
| **Aging** | An age adjustment on the rates and minutes, estimated from our own game logs. Population shape from [R-70]: a rise to ~28–29, then a power-law decline that flattens with age. We avoid the naive delta method because of survivor bias [R-71] (cross-sport, NHL). Instead we use regression with imputation / partial pooling for players who drop out. Player-specific curves [R-70] and trajectory clusters [R-72] (preprint) are out of scope for the draft; noted for Part 2. |
| **Games played** | Marcel-style weighted GP history, regressed to the population mean, with an age term. Then the **availability-overrides file** (D-47 Q2) caps known long absences, e.g. "out until January" → the expected games are the remaining schedule. Sequence models of injury [R-74] and workload spikes [R-73] are in-season (Part 2) features. The preseason uses history only. |
| **Minutes** | A weighted recent minutes-per-game, adjusted for a **team change** (the flag from `int_player_profile`) by blending toward the new team's positional minutes available. This blend is our heuristic (§5, U3). |
| **Rookies / no NBA history** | A draft-position prior: the expected rates and minutes of past draftees at similar picks, with a **wide, right-skewed distribution** [R-78]. College production as an extra prior feature [R-79] is deferred (no college data source is confirmed; §5, U4). Rookies are flagged "low confidence" on the cheat sheet. |
| **Features** | Per-season totals and per-36 rates (2023-24…2025-26), minutes, games, age at the season midpoint, experience, position, team-change flag, draft pick, and overrides. |
| **Uncertainty** | Per-stat sd from **backtest residuals** by minutes band (empirical calibration), widened for rookies. Percentages get sd from binomial variance on the projected attempts. |
| **Leakage** | as_of = draft start (2026-10-18T06:00Z). Backtest as_of = the 2025-26 preseason, with only seasons ≤ 2024-25 visible. A build-failing test is required (data-pipeline-design §5). |
| **Explainability** | Per player: the 3-season history vs the projection, the shrinkage applied per stat, the age adjustment, and the overrides applied. |
| **Not used (and why)** | LightGBM [R-20, R-21]. With 3 seasons (~1,500 player-seasons), a tree model is unlikely to beat shrinkage on season-level targets, and it can't be validated properly in 3 weeks. It is a Part 2 candidate with game-level data. |

## 2. Component card: auction $ valuation (DRAFT-003)

| Field | Plan |
|---|---|
| **Problem** | Convert the projections into a **$ value per player** for this league: overall, by position, and **punt variants** (e.g. punt FT%, punt TO). |
| **Per-category value** | The **G-score** [R-01]: the z-score's refinement that accounts for week-to-week performance variance, which matters in H2H. The percentage categories are **volume-weighted** (a player's impact = (their % − league %) × attempts), so a 90 % FT shooter on 1 attempt isn't worth the same as one on 8. TO is negated. Week-to-week variances are estimated from 2023-24…2025-26 weekly data. |
| **Total value** | The sum of G-scores over the 9 categories, with punt variants dropping (or down-weighting) the punted categories. The case for punting in H2H is from [R-02]. |
| **Replacement level** | Defined by **pool size**, not an arbitrary cut [R-83] (cross-sport, baseball): the replacement player is the best player *not* in the 224 drafted. It is computed per position under the roster slots (G×3, F×3, C, Util×3 + bench), iterated because eligibility overlaps. |
| **$ conversion** | League $ = 16 × $200 = $3,200. Subtract the $1 minimum for each of the 224 slots, leaving $2,976 to share out. Each player gets $1 + a share of that $2,976 in proportion to their **value over replacement** (VOR). **This formula is practitioner only (§5, U1)**: no peer-reviewed paper derives it. [R-81] supports the premise that marginal value under a hard budget is bounded by the remaining budget per remaining slot. |
| **Outputs** | `mart_auction_values`: player × variant → $, VOR, G-score by category, position eligibility, confidence flag. |
| **Explainability** | A per-category G-score breakdown (why this player is worth $X), plus the replacement player per position. |

## 3. Component card: live auction helper (DRAFT-005)

| Field | Plan |
|---|---|
| **Problem** | During the live draft (30 s nomination / 20 s bids), show for each nominated player: **my bid ceiling**, whether he fits my build, and who to nominate next. |
| **State** | `int_draft_state`: players taken, price, team, and each team's remaining budget and open slots. |
| **Max bid (hard rule)** | Budget left − $1 × (my open slots − 1). This is a rule of the game, not a model. |
| **Inflation** | Adjusts the remaining players' $ to the money left: inflation = (league $ left − $1 × slots left) ÷ (the sum of the remaining players' VOR$). This is a practitioner method (§5, U1). |
| **Team fit (adaptive)** | After each of my picks, re-weight the categories toward my roster's needs and punts, then re-rank. This is **inspired by H-scoring** [R-02], which covers snake drafts. **Adapting it to auctions is our own extension (§5, U2).** |
| **Bid ceiling** | min(max bid, inflation-adjusted $ × fit multiplier), shown alongside the plain $ value so I can see the adjustment. |
| **Nomination hint** | Suggests nominating players other teams value above my valuation, to drain rivals' budgets. It's motivated by [R-80] (fantasy-basketball auctions with budget constraints) and [R-81] (item order matters under budget constraints). It is shown as a hint, never automatic. |
| **Latency** | < 2 s per update on the phone (a precomputed table plus light arithmetic). |
| **Fallback** | The static cheat sheet (DRAFT-004) if the helper fails. |

## 4. Evaluation: the backtest (the evidence for G-21)

Design per docs/standards/evaluation.md, with a rolling origin [R-50, R-51].

| Item | Plan |
|---|---|
| **Fold A** (primary) | Build 2025-26 preseason projections and $ from seasons ≤ 2024-25 only, and compare with the realised 2025-26. |
| **Fold B** (secondary) | Target 2024-25 from ≤ 2023-24. This needs a backfill of 2021-22 and 2022-23 (cheap: one `LeagueGameLog` call per season). See panel Q4. |
| **Baselines** | B0 = last season's per-game values repeated. B1 = Marcel [R-13]. [R-52] notes that naive baselines are essential. |
| **Metrics: projection** | Per stat: MAE and RMSE of per-game values for players with ≥ 20 realised games. For FG%/FT%, the error on volume-weighted impact. Games played: MAE. |
| **Metrics: valuation** (the one that matters) | The **Spearman rank correlation** between the projected total G-score and the realised G-score across the realised top-224. Also the **top-224 overlap** (how many of our 224 were really top-224). |
| **Uncertainty checks** | The coverage of 80 % intervals (target 75–85 %). |
| **Statistics** | 95 % CIs by a **paired bootstrap over players** [R-54]. The unit is a player-season, so the block bootstrap used for daily data isn't needed. |
| **Gate** | C1 is used for the draft only if it beats B1 on valuation rank correlation (the paired bootstrap CI of the difference excludes 0 in Fold A). Otherwise **B1 ships**, and that is an acceptable outcome. Either way, B0 must be beaten. |
| **Report** | `docs/evaluation/draft-backtest.md`, with MLflow runs. |

### 4a. Amendment after the backtest (G-21b / D-51, 2026-09-25)
- Shipped method: **H1** = C1 rates x last season's minutes x Marcel games (the 3-year weighted minutes were the weak component).
- Primary metric: **season-total** 9-cat value rank (per game x games).
- Rank criterion: pooled over all rolling folds (bootstrap stratified by fold). The per-stat MAE criterion stays on Fold A.
- Result: docs/evaluation/reports/DRAFT-002-backtest.md.

## 5. Unsupported or partly supported choices (each needs an empirical test)

| # | Choice | Support | Empirical test before use |
|---|---|---|---|
| U1 | The VOR → $ conversion and inflation | Practitioner only. [R-81] supports only the budget-per-slot premise. | A sanity check that the sum of $ is $3,200, all drafted players get ≥ $1, and the top-10 prices are plausible vs published 2025-26 auction values. Reviewed by the owner on the cheat sheet. |
| U2 | Adapting H-score to auctions | Our extension of [R-02] (snake drafts) | Mock drafts. The fit multiplier is capped (e.g. ±25 %) so it can't dominate. |
| U3 | Team-change minutes blend | Heuristic | Fold A: error for players who changed team, B1 vs C1. |
| U4 | Rookie prior from draft position only | [R-78] + [R-79] partly (college data deferred) | Fold A/B: rookie error vs "league-average rookie" baseline. |
| U5 | Stat-specific shrinkage weights | Theory from [R-11, R-12, R-75]; the values are ours (R-77 practitioner) | Split-half reliability on our data; reported per stat. |
| U6 | Aging from 3 seasons of data | [R-70] shape; [R-71] (cross-sport) method | If Q4 backfill is approved, estimate from 2015-16+ (more ages observed); otherwise use a fixed [R-70]-shaped prior. |

## 6. Questions for the owner (G-21 panels)
1. **Projection method**: ★ Marcel baseline + EB-shrunk candidate, backtest decides [R-13, R-11, R-12, R-75]; or Marcel only (faster, weaker); or add LightGBM now (not recommended, see §1).
2. **Valuation**: ★ G-score + pool-size replacement + VOR→$ [R-01, R-83]; or plain z-scores (simpler, ignores weekly variance).
3. **Live helper scope**: ★ max bid + inflation + H-score-inspired fit + nomination hints [R-02, R-80, R-81]; or max bid + inflation only.
4. **Backfill for the backtest/aging**: ★ pull 2015-16…2022-23 game logs too (≈ 8 calls, minutes of work); or keep 3 seasons (Fold A only, fixed aging prior).

---

## Part 1b: minutes model and breakout probability (DRAFT-007, gate G-23; owner D-53)
Status: **APPROVED 2026-09-26 (G-23, D-54)**: see §10a for the owner's answers.
Why it's needed: H1+aging ships "how good", but its minutes are last season's, and shrinkage damps change, so it can't anticipate role changes. With the realised minutes the rates rank far better (0.94 vs 0.91, DRAFT-002 report), so **minutes are where the missing signal is**.

### 7. Component card: pre-season minutes-per-game model (M1)
| Field | Plan |
|---|---|
| **Target** | Minutes per game in season t (players with >= 20 games), predicted before the season. |
| **Features (all knowable pre-season)** | Last-season mpg; 3-season weighted mpg; last-season games share; age and years of experience [R-70]; per-minute production and usage rate (C1 EB rates, so small samples are shrunk [R-11, R-12]), since role conditions the production curve [R-84]; a team-change flag (first team in t differs from last team in t-1) [R-85]; **vacated opportunity** on the player's team: t-1 minutes and usage of teammates no longer on the team, net of the incoming players' t-1 minutes. Redistribution is expected to be uneven, favouring efficient players [R-87], so the feature interacts with the player's own per-minute value. For young players, teammate context [R-91]. |
| **Method (panel Q1)** | ★ **Ridge regression on the change in mpg** (transparent, stable with ~350 players/season; the coefficients are the explanation), or LightGBM [R-20, R-21] (interactions like young x vacated minutes, but less data-efficient), or both with the backtest picking. |
| **Leakage** | Team membership comes from the first game of season t (pre-season rosters aren't archived historically). This is a close proxy for opening-night rosters; in-season moves after game 1 are excluded. Everything else is `< target`. A `LeakageError` test covers every feature. |
| **Evaluation** | 8 rolling folds [R-50, R-51]: mpg MAE vs last-season mpg, and the season-total value rank when M1's minutes replace last-season minutes inside H1+aging. Paired bootstrap stratified by fold [R-54]. |
| **Pre-registered ship rule** | M1 replaces last-season minutes in the shipped model only if (a) its pooled mpg MAE is lower than last-season mpg (95 % CI excluding 0), **and** (b) the pooled season-total rank of H1+aging with M1 minutes beats H1+aging (95 % CI above 0). Otherwise H1+aging stays unchanged. |

### 8. Component card: breakout probability (M2)
| Field | Plan |
|---|---|
| **Label (panel Q2)** | ★ A **breakout** in season t = the player's season-total 9-cat value rank improves by >= 50 places **and** they finish inside the top 150 (fantasy-relevant). Base rate ~5 % a season (to be measured and reported). Alternatives: top-10 % value improvement; or a per-game production jump. |
| **Features** | M1's features plus trajectory (value change t-2 -> t-1), the talent-vs-opportunity gap (strong per-minute value, low minutes), draft pick for players in their first 3 seasons [R-78, R-79], and the vacated opportunity. |
| **Method (panel Q3)** | ★ **L2 logistic regression**, class-weighted for the rare positive class [R-89]: well calibrated, and the coefficients explain each flag. Or LightGBM [R-20, R-21]. |
| **Evaluation** | Rolling folds. Precision@20 and @50 vs the base rate (lift) [R-89], cumulative gain of the ranked list [R-90], and calibration: Brier score vs a base-rate forecast plus a reliability table. |
| **Owner's hindsight check** | The 2025-26 top-20 flags from a model trained on <= 2024-25 only, listed next to who actually broke out (hits and misses). |
| **Pre-registered ship rule** | The breakout probability appears on the cheat sheet only if, pooled over folds, precision@20 beats the base rate (95 % CI above 0) **and** the Brier score beats the base-rate forecast. Otherwise it isn't shown, and the report says so. |
| **Guardrail** | A "sophomore slump" or a dip after a big year is mostly regression to the mean [R-88], so M2 is always compared with the shrinkage baseline and never replaces it. |

### 9. Unsupported choices (Part 1b)
| # | Choice | Support | Empirical test |
|---|---|---|---|
| U7 | A pre-season minutes model for the NBA | No dedicated peer-reviewed model (RSCH-006 gap); R-84 conditions curves on minutes but doesn't forecast them | The M1 ship rule |
| U8 | Vacated-opportunity redistribution weights | Theory only [R-87]; no empirical measurement found | The coefficient on vacated minutes x player value must be positive and stable across folds (reported) |
| U9 | The breakout label threshold (50 places, top 150) | None (a practitioner definition) | Sensitivity: results at 30/50/80 places are reported |
| U10 | First-game roster as the pre-season roster proxy | Data availability | Report how many players changed team after game 1 (expected to be small) |

### 10. Questions for the owner (G-23 panels)
1. **Minutes method**: ★ ridge regression / LightGBM / both, with the backtest picking.
2. **Breakout definition**: ★ >= 50 places and top 150 / top-10 % value improvement / per-game production jump.
3. **Breakout model**: ★ logistic regression / LightGBM.
4. **Ship rules**: ★ as pre-registered above / always show the breakout flags (with their track record).

### 10a. Owner answers (G-23, 2026-09-26, D-54)
1. **Minutes**: build **both** ridge and LightGBM. Pre-registered selection, to avoid choosing and judging on the same seasons:
   - **Selection**: the model with the lower pooled mpg MAE on folds 2018-19…2021-22 wins.
   - **Ship test**: the M1 ship rule (§7) is then applied to the winner on folds 2022-23…2025-26 only.
2. **Breakout** = a season-total value rank jump of >= 50 places, finishing inside the top 150 (sensitivity at 30 and 80 places).
3. **Breakout model** = L2 logistic regression, class-weighted [R-89].
4. **Ship rules** as pre-registered (§7, §8): the flags appear only if proven.

---

## Part 1c: pre-season signal (DRAFT-008) and news reader spike (DISC-012), G-24 / D-57 (2026-09-26, APPROVED)
### 12. Component card: pre-season role signal
| Field | Plan |
|---|---|
| **Why** | Box-score history can't see role changes (DRAFT-007 M2b failed). Exhibition play has some predictive value for rookies [R-92], but exhibition *results* can mislead [R-93], so we measure **role**: minutes and starts. |
| **Data** | stats.nba.com pre-season player game logs (SeasonType = Pre Season) plus per-game box scores for starts, 2015-16 … 2026-27 (DATA-030). |
| **Cutoff (point in time)** | Only exhibition games up to **2 days before that season's opening night**, which is the same position as the 18 Oct draft vs the 20 Oct opener. A leakage test enforces it. |
| **Features** | Pre-season minutes per game; share of team pre-season minutes; share of games started; pre-season mpg minus last season's mpg; games played (0 = rested or injured). Added to the M1 ridge and the M2 logistic regression. |
| **Ship rules (pre-registered, same folds as D-54/D-55)** | (a) M1 with pre-season features replaces M1 only if, on holdout folds 2022-26, its mpg MAE beats current M1 (95 % CI < 0) **and** H1+aging with its minutes beats the current model on season-total rank (95 % CI > 0). (b) Growth flags appear only if M2b with pre-season features passes the D-55 rule (precision@20 minus base, 95 % CI > 0, and a Brier score better than the base rate). The 2025-26 hindsight list is reported either way. |
| **Unsupported (U11)** | No peer-reviewed study of October exhibition minutes predicting NBA role (RSCH-007 gap 1); justified only by the rules above. |

### 13. News reader spike (DISC-012)
- Grounded extraction only: every role claim carries a verbatim quote, source URL and timestamp, checked mechanically [R-95].
- Accuracy measured on >= 50 hand-labelled articles (F1) [R-96].
- Historical coverage (Wayback/GDELT) reported with its bias [R-98].
- **Claude API spend capped at US$5** for the spike; full use decided after seeing accuracy.

---

## Part 2: in-season components (RSCH-004, gate G-19) — APPROVED 2026-09-28 (D-61)

Scope: the models and decisions that run daily from tip-off (20 Oct 2026). They replace the MVP baselines
(MVP-001..005) only through the evaluation gate. Every card names the baseline that is live today.

**Common evaluation** (every card unless stated):
- **Walk-forward by game date** [R-50, R-51]: train on dates < d, test on [d, d + 7 days). Selection folds
  roll through 2023-24..2025-26 H1; the holdout is the second half of 2025-26, pre-registered and untouched
  until the ship test.
- **Paired comparison** against the live baseline: a **Diebold-Mariano test** [R-53] plus a **block
  bootstrap** over days [R-55].
- **Probabilistic outputs**: proper scoring rules (log score/CRPS, Brier) [R-40, R-41] and calibration
  checks (PIT histograms, reliability) [R-42, R-43, R-44].
- **Leakage**: every feature must be available at decision time [R-60]; the as-of harness enforces it.

### 14. Card: in-season per-game projections (ANL-005)
| Field | Plan |
|---|---|
| **Problem** | Each morning, per-game expectations of every player's counting stats and makes/attempts for the rest of the week. |
| **Live baseline** | The draft per-game projection, frozen (MVP-001). |
| **Method** | **In-season empirical-Bayes update**. The pre-season projection is the prior and the season-to-date per-minute rates are the data. Each stat's weight on the data grows with minutes played; the prior strength is estimated from past seasons by the method of moments, as in C1. Brown (2008) tested this setting in baseball, predicting second-half batting averages from first-half data, and empirical-Bayes methods beat raw averages [R-12]; the shrinkage principle comes from [R-10, R-11]. |
| **How we differ** | Baseball batting average is a single binomial rate. We have several correlated per-minute rates and makes/attempts pairs, and our prior is a projection, not a population mean. |
| **Features** | Pre-season projection (rates, mpg), season-to-date minutes and counting totals, games played. |
| **Metrics** | Per-category MAE and mean log score of the per-game prediction; weekly totals. |
| **Ship rule (pre-registered)** | Replaces the baseline if the pooled MAE improves on >= 6 of 9 categories (DM test p < 0.05 on the holdout) and no category worsens by more than 2 %. |
| **Explainability** | Per stat: "season so far vs projection, weight on this season = x %". |

### 15. Card: minutes in season (C2)
| Field | Plan |
|---|---|
| **Live baseline** | The M1-pre minutes projection from the draft, frozen. |
| **Candidate 1** | An exponentially weighted average of recent minutes, blended with the baseline by games played (the §14 logic applied to minutes). |
| **Candidate 2** | **Teammate-absence redistribution**: minutes vacated by teammates listed Out or Doubtful on today's report, shared within the position group in proportion to each player's historical share of that role. No published coefficient exists: RSCH-002's sources (R-99..R-105) cover availability, not redistribution. This is purely empirical (**U12**). |
| **Metrics** | Minutes MAE per game, given the player plays; calibration of minutes quantiles if quantile heads are added [R-22]. |
| **Ship rule** | Each candidate ships only if it beats the previous one on holdout MAE (95 % CI < 0), as in D-54. |
| **Not now** | LightGBM [R-20, R-21]: reconsidered after 4+ weeks of in-season data. D-54 found ridge at least as good as trees at this data size. |

### 16. Card: availability P(plays) (C5)
| Field | Plan |
|---|---|
| **Live baseline** | Measured play rates by injury status (MVP-002: Questionable 48.9 %, Doubtful 1.1 %, …), otherwise season games / 82. |
| **Candidate** | Logistic regression on status, time from report to tip-off, days since the last game, back-to-back, and games since returning. Minutes and usage predict longer absences [R-100]; rest is not protective [R-101]; selection bias from conditioning on "played" is guarded against [R-102, R-103]. Calibrated if needed [R-45, R-46, R-47]. |
| **Metrics** | Brier and log loss vs the status table [R-40, R-41]; reliability diagram [R-42]. |
| **Ship rule** | Brier better than the status table, with the bootstrap CI of the difference below 0 on the holdout. |

### 17. Card: distributions of weekly totals (DEC-002)
| Field | Plan |
|---|---|
| **Live baseline** | Poisson variance for counts, binomial for percentages (MVP-003). |
| **Method** | **Negative binomial** per-game counts, with over-dispersion estimated per stat from game logs [R-30, R-31]. Makes and attempts are simulated jointly, so FG% and FT% keep their dependence. |
| **Metrics** | PIT uniformity and CRPS of weekly category totals [R-41, R-43, R-44]. |
| **Ship rule** | CRPS better on >= 6 of 9 categories (block-bootstrap CI), with calibration no worse. |

### 18. Card: matchup simulation and the H2H objective (DEC-003/004)
| Field | Plan |
|---|---|
| **Live baseline** | An independent normal approximation per category (MVP-003). |
| **Method** | A Monte Carlo simulation of the week (10k draws) using §17's distributions, both rosters, the remaining schedule and P(plays). The objective is expected categories won, plus P(winning the week). Marginal decisions (add/drop, lineup) use **common random numbers**, so small differences aren't lost in simulation noise [R-61]. The H2H category objective follows Rosenof's dynamic valuation framing, where value depends on the current matchup state [R-02]. |
| **Metrics** | Calibration of predicted category-win probabilities against actual weekly results (Brier, reliability) [R-40, R-42]. |
| **Ship rule** | Brier better than the normal approximation on the holdout weeks. |

### 19. Card: lineup optimisation (DEC-007)
| Field | Plan |
|---|---|
| **Live baseline** | Greedy by player value, benching players with no game or ruled Out (MVP-003). |
| **Method** | An integer program over eligible slots (G/F/C/Util) that maximises today's expected category contribution, solved with HiGHS. Hunter, Vielma & Zaman used integer programming to pick daily fantasy lineups [R-04]. |
| **Metrics** | A replay of 2025-26 days: the expected category wins of the chosen lineup vs greedy. Legality property tests: never an ineligible slot, never more players than slots. |
| **Ship rule** | Never worse than greedy on any replayed day (it optimises the same objective exactly), and all property tests pass. |

### 20. Card: add/drop and streaming valuation (DEC-008)
| Field | Plan |
|---|---|
| **Live baseline** | One add vs dropping the lowest-value player, scored by the normal approximation (MVP-003). |
| **Method** | Candidate pairs (the top N free agents × droppable players) scored by the §18 simulation with common random numbers [R-61]. The horizon is the rest of this week plus a discounted next week; the discount is **U13**. |
| **Metrics** | Replay: category wins with the recommended moves vs no move (a counterfactual through the simulator), then outcome scoring in EVAL-007. |

### 21. Card: explanations and answers (DEC-009, APP-004)
| Field | Plan |
|---|---|
| **Method** | Template explanations filled only from structured evidence (the numbers the decision used). A round-trip test checks every number in the text against its source. SHAP values [R-23, R-24] only if a tree model ships. Natural-language answers use Claude tool calls over vetted functions (D-36), with every number traced to a tool result; hallucination controls follow [R-95]. |
| **Metrics** | The round-trip test must pass 100 %. For NL answers, a graded question set with tool-grounding checks. |

### 22. Not covered here (own plans later)
Trade analysis (WEB-006), cold start for rookies with no NBA minutes (D-40; the draft prior is used meanwhile), and the learned ranker (C15, R-62).

### 23. Unsupported or partly supported choices (each with its test)
| ID | Choice | Test that justifies or rejects it |
|---|---|---|
| U12 | Teammate-absence minutes redistribution by position group | The §15 candidate 2 ship rule on the holdout |
| U13 | The next-week discount in add/drop value | Sensitivity: recommendations stable across 0.3-0.7; report both |
| U14 | 10k simulation draws | Monte Carlo standard error of expected category wins < 0.02 at 10k (measured) |
| U15 | Decision time: Sydney morning ≈ 4:30 PM ET | Replay 2025-26 days and compare recommendations made at 4:30 PM with those from the 5:30 PM report; report how often they change |

### 24. Questions for the owner (G-19 panels)
1. **Order of work after the MVP**: ★ distributions + simulation first (they improve every decision) / the lineup optimiser first / the in-season projection update first.
2. **Holdout**: ★ the second half of 2025-26 (pre-registered, untouched until the ship test) / the whole of 2025-26.
3. **Add/drop horizon**: ★ this week + a discounted next week / this week only.
4. **Model complexity ceiling this season**: ★ statistical models only (EB, logistic, NegBin, MILP) / allow gradient boosting once 4+ weeks of data exist.

---

## Part 1d: games for players returning after a lost season (DRAFT-022, gate G-32, APPROVED 2026-10-04)
### 25. Component card: returners' games fraction (variant R)
| Field | Plan |
|---|---|
| **Why** | The games forecast weights last season 0.5 (`expected_games`), so a player who missed essentially all of last season (Lillard: 0 games) is projected for about a third of a season. DRAFT-011/012 showed that changing games inputs for *every* short-season player loses the draft replay; this rule touches only the "lost season" cohort. |
| **Cohort (frozen, not tuned)** | For target season s: last season `games ÷ team games < 0.25` (a player with no row counts as 0), the season before `≥ 0.6` and `mpg ≥ 22`. Two consecutive lost seasons, rookies and one-season players are excluded. |
| **Variant R (the only one)** | `games fraction = max(current, r̄_s)`, `r̄_s` = mean realised games fraction of cohort players, in the seasons before s, **who played at least one game in that season** (expanding window; needs at least 30 such rows, else R does nothing). Raise-only. Minutes and per-minute rates are unchanged. Overrides (DATA-031, DATA-036) apply after R and win. |
| **Grounding** | A population base rate for sparse individual evidence, as Marcel-style projection does [R-13] (a practitioner source; it supports the idea, not this exact rule, so the rule is tested); paired bootstrap [R-54]. |
| **Ship rule (all three)** | (1) **Accuracy**: expanding folds from the first season with 30 earlier cohort rows (expected 2021-22) to 2025-26; cohort players who played that season; mean absolute error of the games fraction, R vs current; the paired-bootstrap 95 % CI of (current − R) is entirely above 0. (2) **Calibration**: over those folds, \|mean predicted − mean realised\| games fraction for cohort players under R is ≤ 0.08. (3) **Non-inferiority**: DRAFT-011 replay with IL replacements (2025-26, 40 drafts, seed 0, 3 IL slots): R − current all-play share, 95 % CI lower bound > −0.005. |
| **Clarifications fixed before any run** | (a) The estimand is "games fraction **given the player plays that season**". Cohort players with no row in s (retired, out again) are not in checks 1 and 2, because the history has no zero-game rows. (b) A player with no row last season is not in the replay pool in DRAFT-009/011/012, which would make check 3 a no-op for R. For check 3 only, the pool of **both** strategies adds every cohort player of the target (including any who never returned, who then score zero in the replay): this tests the whole decision honestly and is biased against R, not for it. (c) The base rate counts only seasons before s (leakage test). |
| **Reported, not deciding** | Lillard's rank and $ before/after; top movers; the age ≥ 33 subgroup (realised vs predicted); the replay without IL replacements; cohort size per fold. |
| **Unsupported (U16)** | That a cohort base rate generalises to a 36-year-old coming off an Achilles injury. Tested only by the rule above; the age subgroup is reported. If R does not ship, the owner uses cited override rows. |
