# Intelligence & Decision Design

> **Reconciled 2026-09-24** with the owner's selections (D-16…D-25, D-36, D-40; S-14–S-17). Tracking: **MLflow** (ADR-0021). Storage: BigQuery (ADR-0020).

Version 0.1 · 2026-09-24 · Status: **Proposed** (G-14). Companion to `system-architecture.md`.

## 1. Decomposition — and where ML is *not* used

One giant model is the wrong tool here. Most decisions are optimisation problems over uncertain player
outputs. ML is only useful where it improves the **inputs** to those optimisations, namely projections
and availability.

| # | Component | Approach | ML? | Why |
|---|---|---|---|---|
| C1 | Baseline projections | Weighted recency averages (Marcel-style) + empirical-Bayes shrinkage to prior season/position | No (statistical) | Strong, cheap baseline; the bar every model must clear. **[R-10, R-11, R-12, R-13]** |
| C2 | Minutes projection | Gradient boosting (LightGBM) on role/context features, with quantile heads | **Yes** | Minutes drive most variance; role changes (teammate injuries, rotation) are nonlinear interactions. **[R-20, R-21, R-22]** |
| C3 | Per-minute rate projection | Shrunk rates (baseline) → LightGBM residual model per stat | **Yes (conditional)** | Only kept if it beats shrunk rates; rates are fairly stable. **[R-11, R-14, R-20]** |
| C4 | Projection uncertainty | Per-stat distributions: counts ~ negative binomial fit on residuals; makes/attempts jointly | Statistical | Needed for simulation; must be calibrated: "sharpness subject to calibration". **[R-30, R-42, R-44]** |
| C5 | Availability P(plays) | Logistic regression → calibrated GBM on injury designation, report timing, B2B, history | **Yes** | Clear binary target; historical labels from 2021-22 injury reports; boosted trees need calibration. **[R-40, R-46, R-47]** |
| C6 | Schedule opportunity | Deterministic counts: games, off-nights, B2Bs, slot contention | No | Exact from schedule + roster |
| C7 | Matchup/season simulation | Monte Carlo over players × remaining games × availability; common random numbers | No (simulation) | Converts distributions into the format's objective exactly; low-variance deltas. **[R-02, R-03, R-61]** |
| C8 | Lineup optimisation | MILP (HiGHS via `highspy`) maximising Σ objective-derived weights × expected contribution, under eligibility | No (optimisation) | Exact, fast, explainable. **[R-04]** |
| C9 | Add/drop/stream valuation | Δ objective (this week) + Δ ROS objective, from C7; ranked | No | Team-context marginal value beats static rankings (Z/G-score) in H2H. **[R-01, R-02]** |
| C10 | Drop candidates | Lowest marginal value among roster, subject to rules (IL, return dates) | No | Same machinery as C9 |
| C11 | Trade evaluation | ROS + playoff-week simulation with/without trade, both teams | No | Same machinery; plus schedule of playoff weeks |
| C12 | Opponent analysis | C7 applied to opponent; contested-category detection; later: opponent behaviour model (streaming propensity from their transaction history) | Later / maybe | Low data; only if measurable value |
| C13 | Confidence | From simulation spread + model calibration error | No | Principled, no extra model |
| C14 | Explanations | Structured evidence → templates; optional LLM rephrase (G-09) | No (LLM optional) | Facts must be deterministic and verifiable |
| C16 | Cold-start priors (D-40) | League-translated pre-NBA rates + draft/age/position priors, blended by EB. **Reduced form until Phase 9:** draft/age/position priors only | Statistical | Rookies and call-ups otherwise get poor early projections. **[R-11, R-12]** + RSCH-003 |
| C17 | NL question answering (D-36) | Claude API tool use over vetted functions; numbers only from tool results | LLM (grounded) | Owner requirement; evaluated on a question set for answer accuracy and grounding |
| C15 | Recommendation ranking (learned) | Learning-to-rank on logged recs + outcomes, evaluated off-policy | **Deferred** | Needs ≥1 season of logs; revisit Phase 9. **[R-62]** |

**Grounding rule**: `[R-xx]` refers to `docs/research/ml-literature-review.md`. Any ML approval gate must restate the cited
references and explain in one line why each applies (see `docs/project/human-approval-gates.md`, G-14).

## 2a. Feature catalogue (proposed 2026-09-25, in response to the owner's question on teammates, opposition and injury history)

Every feature must be **point-in-time** (built from data observed at or before `as_of`; leakage-tested) and must **earn its place**: it is kept only if an ablation under the promotion gate (§4) shows a measurable improvement. "Plausible" is not enough.

| Family | Examples | Feeds | Source (as-of) | Phase | Grounding |
|---|---|---|---|---|---|
| **Recent form & role** | minutes last 1/3/5/10 games, EWMA; start rate; usage share; per-36 rates | C1–C3 | box scores / game logs | 3 (baseline) | [R-11, R-13, R-14] |
| **Opposition** | opponent pace; opponent category-allowed rates (e.g. rebounds conceded per 100 possessions, by position); opponent defensive rating; back-to-back status of the opponent | C3 rates, C7 | team game logs / box scores | 6 | [R-14] |
| **Teammate availability (vacated minutes/usage)** | minutes and usage of teammates who are Out/Doubtful at `as_of`; the player's historical share of that vacated role | C2 minutes (largest expected effect) | injury reports + game logs | 6 | practitioner "usage redistribution"; to be tested |
| **Teammate interaction ("chemistry" proxies)** | with-or-without-you (WOWY) splits (the player's rates when teammate X plays vs sits); lineup continuity (share of minutes with the usual starters); new-teammate/trade flag | C2, C3 | game logs (WOWY); stats.nba.com lineups endpoint (home IP) | 6–9 | regularised plus-minus / lineup literature [R-15]; true "chemistry" isn't directly observable, so these are measurable proxies |
| **Injury history** | days since return; games since return (ramp-up); count and length of absences over the last 1–3 seasons; recurrence of the same body part; minutes-restriction signal (news, D-32) | C5 availability, C2 minutes | injury-report history (2021-22+), game logs | 6 | prior injury as a risk factor [R-16]; the NBA-specific literature is a gap (RSCH-002) |
| **Schedule & fatigue** | rest days; back-to-back (2nd leg); games in the last 7 days; travel/time-zone changes | C2, C5 | schedule | 3–6 | practitioner; to be tested |
| **Game context** | home/away; betting spread (blowout risk → starters' minutes); game total (pace) | C2, C3 | cdn odds (today only; no free history) | 9 (needs an odds history) | — |
| **Cold start** | draft slot, age, position priors; translated pre-NBA stats | C16 | draft data; pre-NBA leagues (low priority) | 1 / 9 | [R-11, R-12] + RSCH-003 |

**Explainability**: each prediction's top SHAP drivers [R-23, R-24] are stored as evidence, so a recommendation can say, for example, "+5.8 min: two starters out", "opponent allows the 3rd-most rebounds", or "3rd game back from a knee injury; minutes still ramping".

## 2. ML component cards

Each card answers the 15 required questions. Metrics are computed **per category**, out-of-sample,
using walk-forward folds (by game date). Each fold trains on dates < *d* and tests on [*d*, *d* + 7 days).

### C2 — Minutes model
1. **Why ML**: minutes depend on interacting factors: teammate absences, blowout risk, rest, and role trend. Averages miss abrupt role changes.
2. **Problem**: predict the minutes distribution for player *p* in game *g*, as of *t* (before tip-off).
3. **Features**:
   - recent minutes (last 1/3/5/10 games, EWMA)
   - season average
   - starts share
   - teammates' availability as of *t* (the minutes vacated by Out/Doubtful teammates)
   - rest days, B2B, home/away
   - projected spread (only if obtainable as of *t*; otherwise omitted)
   - games since return from injury
   - position depth
4. **Target**: actual minutes, conditional on playing (P(plays) is modelled separately in C5).
5. **Training data**: player-games 2021-22 onward, from stats.nba.com logs + injury-report snapshots as of the pre-game report time.
6. **Method**: LightGBM with L2 objective + quantile heads (p10/p50/p90). Hyperparameters are tuned on inner walk-forward folds only.
7. **Validation**: walk-forward by week across ≥ 2 seasons. The final season is held out, touched once per model release.
8. **Metrics**: MAE and RMSE in minutes; quantile coverage (p10–p90 covers ~80 %); MAE sliced by role-change events.
9. **Baselines**: B-min-1 = last-10 average; B-min-2 = EWMA + shrinkage.
10. **Leakage risks**:
    - using box-score `starter` flags for the game being predicted
    - final injury status instead of the as-of report
    - season averages that include future games
    - features computed from rows with `observed_at > t`
11. **Retraining**: weekly during the season (cheap: < 2 min CPU). The model is promoted only through the evaluation gate (§4).
12. **Monitoring**: rolling 14-day MAE vs baseline in the dashboard; an alert if the model is worse than the baseline for 7 consecutive days.
13. **Explainability**: SHAP top contributors per prediction, stored as evidence (e.g. "+6.2 min: teammate X out").
14. **Compute**: laptop CPU; training < 2 min; inference ms.
15. **Expected value**: highest of all ML components. Minutes errors dominate projection error, especially after injuries or trades.
16. **Grounding**:
    - gradient boosting [R-20, R-21]
    - pinball-loss quantile regression [R-22]
    - rolling-origin evaluation [R-50, R-51]
    - leakage-by-legitimacy principle [R-60]
    - Gap: no peer-reviewed NBA minutes model has been identified yet (RSCH-002).

### C3 — Per-minute rate residual model
1. **Why ML**: modest. Matchup (opponent pace and defense) and usage shifts may add signal beyond shrunk rates.
2. **Problem**: per-36 rate for each category (PTS, REB, AST, STL, BLK, 3PM, TOV, FGA, FGM, FTA, FTM).
3. **Features**: shrunk rates, opponent category-allowed rates (as-of), pace (as-of), usage share (as-of), teammate availability.
4. **Target**: realised per-minute rate (weighted by minutes).
5. **Training data**: as for C2.
6. **Method**: LightGBM on the residual from the shrunk rate, one model per category, or multi-output if it helps.
7. **Validation**: as for C2.
8. **Metrics**: category MAE, both per-game and aggregated per week.
9. **Baselines**: shrunk rate (C1).
10. **Leakage risks**: opponent stats including the target game; end-of-season pace.
11. **Retraining**: weekly.
12. **Monitoring**: per-category skill score vs C1.
13. **Explainability**: SHAP.
14. **Compute**: trivial.
15. **Expected value**: **uncertain**. It is dropped if the gate fails for a category, and that category falls back to C1.
16. **Grounding**:
    - The baseline is Efron–Morris / Brown in-season empirical-Bayes shrinkage [R-11, R-12]. Brown (2008) is also a template for testing whether more complex methods beat EB in-season.
    - Basketball per-possession and per-minute conventions [R-14].

### C5 — Availability model
1. **Why ML**: the mapping from designation to P(plays) varies by designation × timing × team × player history, and needs calibration.
2. **Problem**: P(player appears in game *g*), as of *t*.
3. **Features**:
   - latest designation as of *t*
   - hours between the report and tip-off
   - reason category (rest, injury type)
   - B2B second leg
   - days out so far
   - player's historical "Questionable → played" rate (shrunk)
   - team's tendencies
4. **Target**: played (MIN > 0).
5. **Training data**: official injury reports since 2021-22 (every report version), joined to box scores.
6. **Method**: logistic regression first; GBM + isotonic calibration if it beats the logistic model.
7. **Validation**: walk-forward by week. Separate evaluation at different lead times (T-24h, T-6h, T-1h).
8. **Metrics**: Brier score, log loss, ECE, reliability diagram, AUC (secondary).
9. **Baselines**: the static designation → rate table (e.g. Questionable ≈ 0.6), estimated on training data.
10. **Leakage risks**:
    - using the *final* report when predicting at an earlier lead time
    - using the inactive list (published about 30 min before tip) at longer lead times
    - "not on report" being treated differently in history than live
11. **Retraining**: monthly, plus at the season start.
12. **Monitoring**: rolling Brier vs baseline; calibration drift.
13. **Explainability**: coefficients / SHAP; the evidence shows "Questionable, report 3 h pre-tip, player history 71 % plays".
14. **Compute**: trivial.
15. **Expected value**: high for daily lineups and streaming during injury-heavy stretches.
16. **Grounding**:
    - proper scoring rules [R-40, R-41]
    - calibration of boosted trees [R-46, R-47]
    - ECE [R-48]
    - Gap: designation → outcome base rates have no peer-reviewed source yet (RSCH-002); we estimate them empirically, with CIs.

### C4 — Distributions (statistical, not ML)
- Fit per-category residual dispersion by minutes bucket. Simulate counting stats from NegBin(mean = minutes × rate), and makes/attempts jointly (attempts ~ NegBin; makes ~ Binomial(attempts, p shrunk)).
- Validate with PIT histograms and interval coverage.
- The gate is calibrated coverage (80 % intervals cover 75–85 %).
- **Grounding**:
  - over-dispersed count models [R-30, R-31]
  - PIT / density-forecast evaluation [R-43, R-44]
  - the sharpness-subject-to-calibration objective [R-42]

### C2 / C5 research update (PROPOSAL, RSCH-002, 2026-09-27; owner review, Tier B)

`docs/research/lit-minutes-injury.md` found no peer-reviewed minutes-projection model and no measured designation play rates. Proposed changes to C2 and C5:
- C2 stays a project-specific empirical model; state that no peer-reviewed baseline exists. Add age and workload trend; guard against selection bias from conditioning on "played" [R-102, R-103].
- C5: P(plays | designation) is estimated from our own injury-report history with CIs, never hard-coded. Duration priors by injury type come from [R-99, R-100, R-105], recalibrated on our data. Rest is not treated as protective [R-101].
- Teammate-out minutes redistribution and blowout effects are hypotheses to test on our own data.

## 3. Decision engine

### 3.1 Inputs (the `DecisionContext`, built as-of *t*)
- league settings: categories, roster slots, lineup lock rules, acquisition limits, playoff weeks
- my roster and the opponent's roster, with eligibility and status (IL/IL+)
- the free-agent pool
- schedule
- projections + availability
- current matchup totals (week-to-date)
- the remaining-acquisitions budget

### 3.2 Core machinery
1. **Simulator (C7)**:
   - N draws (default 2 000; reproducible via seed).
   - For each remaining game of each rostered player: plays ~ Bernoulli(P), then a stat line drawn from C4.
   - The lineup policy decides which players count on each day (C8 is applied per day inside the sim, or a greedy approximation for speed).
   - Category totals are added to week-to-date actuals.
   - Outputs: P(win) per category, and E[category wins].
2. **Objective (per scoring format)**: `ScoringObjective` is selected by `LeagueRules.format` (architecture §4.3).
   - H2H Categories: E[category wins − losses]
   - H2H One Win: P(win matchup)
   - H2H Points: P(points > opponent)
   - Rotisserie: E[standings points] [R-03]
   - Points: E[season points] under games caps

   The team-context formulation follows the H-scoring framework [R-02]. Static Z/G-scores [R-01] are kept as **baselines and explainability aids**, not as the decision objective.
3. **Marginal value**: for an action *a* (add X / drop Y / swap), ΔV(a) = E[objective | a] − E[objective | status quo], computed with **common random numbers** [R-61] so the variance of Δ is low.
4. **Optimiser (C8)**:
   - A daily MILP [R-04] assigns players to slots and maximises Σ_players Σ_stats w_s · E[contribution_s].
   - The weights w_s = ∂objective/∂contribution_s come from the simulation (`ScoringObjective.marginal_weights`).
   - In category formats this concentrates effort on contested categories. This is how the engine "recommends strategy against the opponent" (e.g. it stops chasing locked or lost categories, and in One Win it may punt).
   - In points formats, the weights reduce to the league's stat modifiers.
5. **Rules**:
   - hard constraints: roster legality, acquisition limits, IL eligibility, games-played caps
   - soft vetoes, which must be explained: e.g. don't drop top-50 ROS players for one-week streams
   - Rules are versioned code with unit tests.
6. **Horizon blending**: score = λ · ΔV_week + (1 − λ) · ΔV_ROS, where λ is configurable and depends on the action type (streaming λ≈1, core pickups λ≈0.3).

### 3.3 Recommendation schema (core fields)
`rec_id, created_at, as_of, kind (lineup|add|drop|stream|trade|strategy), action, alternatives[], expected_delta, delta_ci, confidence (low|med|high), evidence[] (fact/metric/prediction refs with values), rules_applied[], explanation_template_id, explanation_text, model_versions{}, snapshot_ids[], git_sha, seed`

### 3.4 Explanation rules
- Explanations are rendered from **evidence only**. The template tests assert that every number in the text appears in the evidence.
- An optional LLM rephrase (G-09) receives only the evidence JSON and must round-trip the numbers. This is verified by the same test.

## 4. Model promotion gate (enforced by `just eval-gate`)

A candidate replaces the incumbent only if **all** of the following hold:
1. The software, data-contract and leakage tests pass.
2. Walk-forward [R-50] on ≥ 2 seasons: the paired block-bootstrap [R-54, R-55] 95 % CI of (incumbent_error − candidate_error) is > 0 on the primary metric, for the targeted stats. A Diebold–Mariano test [R-53] is reported alongside.
3. There is no regression beyond tolerance (e.g. +2 % MAE) on any other category.
4. Calibration is within bounds (ECE / interval coverage).
5. The backtest report is committed under `docs/evaluation/reports/`, and the **MLflow run** records the data snapshot hash, feature list, params, seed, and git SHA. On PASS, the model is **promoted automatically** (owner decision 2026-09-24): the MLflow alias `champion` moves, the model is exported to the versioned GCS path that prod reads, a promotion record goes to `predictions.model_promotions`, and a Telegram note links the report. Rolling back means moving the alias back (one command).
6. The model card cites its methodological grounding (`[R-xx]`) and states any deviation from the cited method.

## 5. Evaluation framework (summary; standard in `docs/standards/evaluation.md`)

| Level | Question | Method | Metric |
|---|---|---|---|
| Model | Are projections accurate? | walk-forward | MAE/RMSE per category, skill vs baseline, coverage |
| Probability | Are probabilities honest? | walk-forward | Brier, log loss, ECE, reliability |
| Decision (offline) | Are lineups/streams better than baselines? | **historical replay**: run the engine at past *t* using only data observed ≤ *t*, then score with realised stats | Δ realised category value vs B1/B2; % days better; bootstrap CI |
| Decision (online) | Were logged recommendations useful? | outcome scoring of the rec log vs what the owner did and vs baselines | followed-rate, realised Δ, hit rate by confidence bucket |
| Matchup | Are category-win and matchup-win probabilities calibrated? | all league matchups × categories × weeks (roto: end-of-season standings) | Brier / reliability [R-40, R-48] |
| Format coverage | Does each scoring format's objective behave correctly? | golden-fixture tests per format + replay on synthetic leagues | exact expected outputs; property tests (e.g. adding a strictly dominant player never lowers the objective) |

**Why clean counterfactuals are possible here**: the owner's lineup and waiver choices do not change NBA
players' stats, so "what if I had started Y" can be scored exactly from realised box scores. The exceptions
are opponent reactions and waiver competition, which are documented as limitations.

**Leakage and bias controls**:
- all reads go through `AsOfReader(t)`, which filters `observed_at <= t`
- a replay harness forbids direct table access
- Yahoo ownership and FA pools come from snapshots only, so backtests before snapshot collection are limited to lineup and projection evaluation
- survivorship: the player universe as of *t* includes later-waived or retired players
- selection bias: the owner's followed and not-followed recommendations are analysed separately
