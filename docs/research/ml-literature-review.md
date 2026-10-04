# ML & Decision Methods — Literature Grounding

Version 0.1 · 2026-09-24. **Rule (ML standard §1):** every modelling or decision method used in this project
cites at least one entry here, and every ML approval gate lists the relevant `[R-xx]` IDs with a one-line
justification. Entries marked were identified from memory or search but have not yet been read in full.
Task RSCH-001 verifies each one: bibliographic details, a summary, and applicability. Until then, an entry
cannot be the *sole* justification for a gated decision.

## Verification status (RSCH-001, 2026-09-25)

Every entry was checked against a primary source (DOI / arXiv / publisher / proceedings page) by two research passes.
Full details, URLs, key results and support ratings: [`lit-verification-part-a.md`](lit-verification-part-a.md) (R-01…R-31), [`lit-verification-part-b.md`](lit-verification-part-b.md) (R-40…R-66).

**Result: 40/40 found. 36 Verified, 4 Corrected (minor), 0 Not found. No entry contradicts the claim we use it for; 1 is only a partial fit (R-16).**

**Access rule:** an entry verified at *Abstract* or *Book description* level only may support a design choice, but it cannot be the **sole** basis for a gated (G-19) decision until its full text has been read. Full-text follow-ups are listed in the RSCH-004 plan.

| ID | Status | Access level | Note |
|---|---|---|---|
| R-01 | Corrected (title) | Full text | title updated to 'Static quantification of player value for fantasy basketball' (arXiv v5) |
| R-02 | Verified | Full text |  |
| R-03 | Verified | Full text |  |
| R-04 | Verified (minor note) | Full text | worked example is NHL; the NBA position constraints must be built by us |
| R-10 | Verified | Full text |  |
| R-11 | Verified | Abstract |  |
| R-12 | Verified | Full text |  |
| R-13 | Verified (practitioner, not peer-reviewed) | Full text |  |
| R-14 | Verified | Abstract |  |
| R-15 | Verified (conference paper, not peer-reviewed) | Abstract | a proxy for teammate context (RAPM), **not** a pairwise 'chemistry' model; conference paper |
| R-16 | Verified | Full text | **partially supports**: a football (soccer) cohort; NBA magnitude must be validated on our data (RSCH-002) |
| R-20 | Verified | Abstract |  |
| R-21 | Verified | Abstract |  |
| R-22 | Verified | Abstract |  |
| R-23 | Verified | Abstract |  |
| R-24 | Verified | Abstract |  |
| R-30 | Verified | Book description |  |
| R-31 | Verified | Book description |  |
| R-40 | Verified | Abstract |  |
| R-41 | Verified | Abstract |  |
| R-42 | Verified | Abstract |  |
| R-43 | Corrected | Abstract | pages corrected to 278–290 |
| R-44 | Verified | Abstract |  |
| R-45 | Verified | Book description |  |
| R-46 | Verified | Abstract |  |
| R-47 | Verified | Abstract |  |
| R-48 | Verified | Full text |  |
| R-50 | Verified | Abstract |  |
| R-51 | Verified | Abstract |  |
| R-52 | Verified | Full text |  |
| R-53 | Verified | Abstract |  |
| R-54 | Verified | Book description |  |
| R-55 | Verified | Abstract |  |
| R-60 | Verified | Abstract |  |
| R-61 | Verified | Book description | **chapter number unverified** (Ch. 4 variance reduction): cite the book, not the chapter |
| R-62 | Verified | Full text |  |
| R-63 | Verified | Abstract |  |
| R-64 | Verified | Abstract |  |
| R-65 | Verified | Book description |  |
| R-66 | Verified (minor subtitle correction) | Book description | subtitle confirmed: 'The Definitive Guide to Dimensional Modeling' |

## 1. Fantasy-specific valuation (category and roto leagues)

| ID | Reference | Used for | Key idea |
|---|---|---|---|
| R-01 | Rosenof, Z. (2023). *Static quantification of player value for fantasy basketball* (v5; earlier versions titled *Improving Algorithms for Fantasy Basketball*). arXiv:2307.02188. https://arxiv.org/abs/2307.02188 | Baseline player value in category leagues | Z-score is a special case of "G-score", which accounts for week-to-week performance variance. Z-scores assume performances are known exactly. |
| R-02 | Rosenof, Z. (2024). *Dynamic quantification of player value for fantasy basketball.* arXiv:2409.09884. https://arxiv.org/abs/2409.09884 | H2H Categories / One Win decision objective; punting | "H-scoring": value depends on the rest of the team; implementation H₀ for head-to-head formats. It supports our choice of **team-context marginal value** over static rankings. |
| R-03 | Rosenof, Z. (2025). *Optimizing for Rotisserie Fantasy Basketball.* arXiv:2501.00933. https://arxiv.org/abs/2501.00933 | Rotisserie objective | Extends the dynamic framework to roto standings. |
| R-04 | Hunter, D. S., Vielma, J. P., & Zaman, T. (2016). *Picking Winners in Daily Fantasy Sports Using Integer Programming.* arXiv:1604.01455. | Lineup MILP formulation | Integer programming for fantasy lineup construction under position constraints. |


## 2. Shrinkage, projections, and regression to the mean

| ID | Reference | Used for |
|---|---|---|
| R-10 | James, W., & Stein, C. (1961). Estimation with quadratic loss. *Proc. 4th Berkeley Symposium*, 1, 361–379. | Theoretical basis for shrinkage |
| R-11 | Efron, B., & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *JASA*, 70(350), 311–319. | Empirical-Bayes shrinkage of sports rates (the baseball batting-average example): the C1 baseline |
| R-12 | Brown, L. D. (2008). In-season prediction of batting averages: a field test of empirical Bayes and Bayes methodologies. *Annals of Applied Statistics*, 2(1), 113–152. | In-season EB prediction; the evaluation design for rate shrinkage |
| R-13 | Tango, T. (c. 2004). "Marcel the Monkey Forecasting System" (web). Also Tango, Lichtman & Dolphin (2007), *The Book: Playing the Percentages in Baseball.* | Weighted-recency + regression-to-mean projection as a **minimum baseline** (non-peer-reviewed; practitioner standard) |
| R-15 | Sill, J. (2010). *Improved NBA Adjusted +/- Using Regularization and Out-of-Sample Testing.* MIT Sloan Sports Analytics Conference. | Teammate/lineup interaction proxies | Ridge-regularised plus-minus separates individual impact from teammates; basis for lineup-aware features |
| R-16 | Hägglund, M., Waldén, M., & Ekstrand, J. (2006). Previous injury as a risk factor for injury in elite football. *British Journal of Sports Medicine*, 40(9), 767–772. | Injury-history features | Prior injury predicts future injury (cross-sport evidence; the NBA-specific transfer is a gap for RSCH-002) |
| R-14 | Kubatko, J., Oliver, D., Pelton, K., & Rosenbaum, D. T. (2007). A starting point for analyzing basketball statistics. *JQAS*, 3(3). | Possession/pace/per-minute conventions for basketball features |

## 3. Tree ensembles, quantiles, and explanation

| ID | Reference | Used for |
|---|---|---|
| R-20 | Friedman, J. H. (2001). Greedy function approximation: a gradient boosting machine. *Annals of Statistics*, 29(5), 1189–1232. | Gradient boosting (C2, C3) |
| R-21 | Ke, G., et al. (2017). LightGBM: a highly efficient gradient boosting decision tree. *NeurIPS 30*. | Implementation choice |
| R-22 | Koenker, R., & Bassett, G. (1978). Regression quantiles. *Econometrica*, 46(1), 33–50. | Quantile heads for the minutes distribution |
| R-23 | Lundberg, S. M., & Lee, S.-I. (2017). A unified approach to interpreting model predictions. *NeurIPS 30*. | SHAP explanations as evidence |
| R-24 | Lundberg, S. M., et al. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence*, 2, 56–67. | TreeSHAP (exact, fast) |

## 4. Count models and distributions

| ID | Reference | Used for |
|---|---|---|
| R-30 | Cameron, A. C., & Trivedi, P. K. (2013). *Regression Analysis of Count Data* (2nd ed.). Cambridge UP. | Negative binomial for over-dispersed box-score counts (C4) |
| R-31 | Hilbe, J. M. (2011). *Negative Binomial Regression* (2nd ed.). Cambridge UP. | Same, practical reference |

## 5. Probabilistic forecasting, scoring rules, and calibration

| ID | Reference | Used for |
|---|---|---|
| R-40 | Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3. | Brier score (availability, category-win probabilities) |
| R-41 | Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*, 102(477), 359–378. | Choice of log loss / CRPS as proper scores |
| R-42 | Gneiting, T., Balabdaoui, F., & Raftery, A. E. (2007). Probabilistic forecasts, calibration and sharpness. *JRSS B*, 69(2), 243–268. | "Maximise sharpness subject to calibration" as the projection-distribution objective |
| R-43 | Dawid, A. P. (1984). Statistical theory: the prequential approach. *JRSS A*, 147(2), 278–290. | PIT, and prequential (walk-forward) evaluation |
| R-44 | Diebold, F. X., Gunther, T. A., & Tay, A. S. (1998). Evaluating density forecasts with applications to financial risk management. *International Economic Review*, 39(4), 863–883. | PIT histograms for C4 |
| R-45 | Platt, J. (1999). Probabilistic outputs for support vector machines… *Advances in Large Margin Classifiers*. | Sigmoid calibration |
| R-46 | Zadrozny, B., & Elkan, C. (2002). Transforming classifier scores into accurate multiclass probability estimates. *KDD '02*. | Isotonic calibration (C5) |
| R-47 | Niculescu-Mizil, A., & Caruana, R. (2005). Predicting good probabilities with supervised learning. *ICML '05*. | Boosted trees need calibration, which justifies the C5 design |
| R-48 | Guo, C., Pleiss, G., Sun, Y., & Weinberger, K. Q. (2017). On calibration of modern neural networks. *ICML '17*. | ECE metric definition |

## 6. Forecast evaluation, time-series validation, and significance

| ID | Reference | Used for |
|---|---|---|
| R-50 | Tashman, L. J. (2000). Out-of-sample tests of forecasting accuracy: an analysis and review. *International Journal of Forecasting*, 16(4), 437–450. | Rolling-origin (walk-forward) evaluation |
| R-51 | Bergmeir, C., & Benítez, J. M. (2012). On the use of cross-validation for time series predictor evaluation. *Information Sciences*, 191, 192–213. | Why not random K-fold |
| R-52 | Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts. | Baselines, time-series CV, forecast accuracy measures |
| R-53 | Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *JBES*, 13(3), 253–263. | Paired test of model vs baseline errors |
| R-54 | Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap.* Chapman & Hall. | Bootstrap CIs |
| R-55 | Künsch, H. R. (1989). The jackknife and the bootstrap for general stationary observations. *Annals of Statistics*, 17(3), 1217–1241. | Block bootstrap (serially correlated daily errors) |

## 7. Leakage, simulation, off-policy evaluation, and ML systems

| ID | Reference | Used for |
|---|---|---|
| R-60 | Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: formulation, detection, and avoidance. *ACM TKDD*, 6(4). | Leakage taxonomy; the "legitimacy as of prediction time" principle behind `AsOfReader` |
| R-61 | Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering.* Springer. (variance reduction; chapter number unverified) | Common random numbers for marginal-value Δ |
| R-62 | Dudík, M., Langford, J., & Li, L. (2011). Doubly robust policy evaluation and learning. *ICML '11*. | Future learned ranker (C15): off-policy evaluation from the rec log |
| R-63 | Sculley, D., et al. (2015). Hidden technical debt in machine learning systems. *NeurIPS 28*. | Architecture guard-rails (pipeline jungles, entanglement) |
| R-64 | Breck, E., Cai, S., Nielsen, E., Salib, M., & Sculley, D. (2017). The ML Test Score: a rubric for ML production readiness. *IEEE Big Data*. | ML testing standard checklist |
| R-65 | Snodgrass, R. T. (1999). *Developing Time-Oriented Database Applications in SQL.* Morgan Kaufmann. | Bitemporal modelling (valid time vs transaction/observed time) |
| R-66 | Kimball, R., & Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* (3rd ed.). Wiley. | Dimensional modelling, SCD2 |

## 9. Draft-slice references (R-70…R-83; verified 2026-09-25)
Full citations, URLs, key results and design notes: [`lit-draft-slice.md`](lit-draft-slice.md). The access rule in the Verification status section applies.

| ID | Topic | Status | Access |
|---|---|---|---|
| R-70 | 1. Aging curves (NBA-specific) | Verified | Full text (PMC) |
| R-71 | 1. Aging curves — methodology (delta method, survivorship bias) | Verified (peer-reviewed, but NHL not NBA — cross-sport transfer, same caveat pattern as R-16) | Abstract (paywalled; preprint at https://arxiv.org/abs/2110.14017) |
| R-72 | 1. Aging curves — NBA-specific, method comparison (preprint only) | Verified (preprint, NOT peer-reviewed) | Full text (arXiv) |
| R-73 | 2. Games-played / availability (NBA-specific, workload→injury) | Verified | Abstract (confirmed via search-engine cached abstract/citation; direct fetch returned 403) |
| R-74 | 2. Games-played / availability (NBA-specific, forecasting model) | Verified | Abstract (confirmed via IOS Press / search snippets; full-text fetch blocked, 403) |
| R-75 | 3. Preseason projection accuracy / stabilization of NBA rate stats | Verified | Full text (arXiv preprint) |
| R-76 | 3. Preseason projection / small-sample shooting reliability (preprint only) | Verified (preprint, NOT peer-reviewed) | Full text (arXiv) |
| R-77 | 3. Practitioner-only note: "stabilization rates" | Not peer-reviewed — practitioner only | Full text (blog) |
| R-78 | 4. Rookie / draft-position priors | Verified | Abstract (confirmed via search snippets/cached abstract; direct fetch blocked) |
| R-79 | 4. Rookie / draft-position priors — career length & college production | Verified | Full text (author-hosted PDF) |
| R-80 | 5. Auction draft valuation — fantasy-basketball-specific auction theory | Verified | Abstract (confirmed via search snippets; direct fetch returned 403) |
| R-81 | 5. Auction draft valuation — general multi-object auction theory, budget constraints | Verified (general economics, not fantasy-sports-specific) | Abstract |
| R-82 | 5. Rosenof auction coverage | Checked — Not found (no auction-specific treatment) | Full text (already verified in RSCH-001) |
| R-83 | 6. Replacement level / value over replacement | Verified (peer-reviewed; baseball, cross-sport caveat) | Abstract (arXiv + RePEc) |

**Gaps (explicitly unsupported by peer-reviewed literature; must be justified empirically in RSCH-005):**
- the numeric NBA stat stabilisation points (practitioner only, R-77)
- the auction $ conversion formula (practitioner value-over-replacement budget allocation)
- the H-score-style dynamic valuation adapted to auctions (R-02 covers snake drafts; the adaptation is ours)

## 10. Breakout references (R-84…; verified 2026-09-25)
Full citations, URLs, key results and design notes: [`lit-breakouts.md`](lit-breakouts.md). The access rule in the Verification status section applies. Covers RSCH-006 (D-53): minutes/role prediction, breakout seasons, opportunity effects, and rare-event/top-k evaluation.

| ID | Topic | Status | Access |
|---|---|---|---|
| R-84 | 1&2. Minutes/usage/position-conditioned production curves (NBA-specific) | Verified | Abstract (RePEc/IDEAS; publisher page 405; self-archived PDF not machine-readable this pass) |
| R-85 | 3. Opportunity effects — trades / "comobility" (NBA-specific) | Verified (peer-reviewed, management journal) | Abstract (confirmed via search snippets; direct fetch returned 403) |
| R-86 | 3. Opportunity effects — coaching changes (NBA-specific, team-level) | Verified (peer-reviewed, sports-science journal) | Full text (RICYDE, open access) |
| R-87 | 3. Opportunity effects — theoretical basis for usage redistribution (NBA-specific) | Verified | Full text (PLOS ONE) |
| R-88 | 2. Breakout / "sophomore slump" vs. regression to the mean (soccer, cross-sport caveat) | Verified (peer-reviewed; soccer not basketball) | Abstract (confirmed via search snippets; direct fetch returned 403/404) |
| R-89 | 4. Rare-event / imbalanced classification — evaluation and methods | Verified (peer-reviewed, foundational survey) | Abstract (Google Scholar citation lookup; DOI resolves to IEEE Xplore, page itself empty/paywalled) |
| R-90 | 4. Top-k ranking evaluation — precision@k, graded relevance | Verified (peer-reviewed, foundational) | Abstract (bibliographic record confirmed via Tampere research portal; no abstract text obtained; ACM DL page returned 403) |
| R-91 | 3. Opportunity effects — teammate/team-fit context on rookie production and earnings (NBA-specific) | Verified (peer-reviewed, sports-economics journal) | Abstract (RePEc/IDEAS) |

**Gaps (explicitly unsupported by peer-reviewed literature):**
- a dedicated NBA minutes-played / discrete role-change forecasting model (topic 1)
- a dedicated NBA "breakout season" classifier/predictor, and the per-minute-efficiency-at-low-minutes latent-talent signal specifically for breakouts (topic 2)
- an individual player's minutes shift caused by a coaching change, and the empirical split of vacated usage/minutes among remaining teammates (topic 3)
- precision@k / calibration evaluation applied specifically to a sports breakout or top-k rare-talent task (topic 4)

## 11. Signal references (R-92…R-98; verified 2026-09-26)
Full citations, key results and design notes: [`lit-signals.md`](lit-signals.md).

| ID | Topic | Status | Access |
|---|---|---|---|
| R-92 | 1. Pre-season/exhibition play -> regular season (NBA Summer League, rookies) | Verified (peer-reviewed) | Abstract |
| R-93 | 1. Pre-season results -> regular season (NFL, team level; cross-sport) | Verified (peer-reviewed; cross-sport) | Abstract |
| R-94 | 2. Text mining of NBA injury data | Verified (peer-reviewed) | Full text (open access) |
| R-95 | 3. LLM hallucination: taxonomy and detection | Verified (peer-reviewed) | Abstract |
| R-96 | 3. LLM extraction accuracy vs a gold standard (clinical; cross-domain) | Verified (peer-reviewed; cross-domain) | Abstract |
| R-97 | 4. GDELT as a dated news-event archive | Not re-verified (conference paper, not peer-reviewed; not in Crossref) | Bibliographic only |
| R-98 | 4. Wayback Machine as a research data source | Verified (peer-reviewed) | Abstract |

## 8. Known gaps (research tasks)

- **NBA availability / injury-designation outcome rates**: searched in RSCH-002 (2026-09-27). **No measured source exists**; the circulating percentages are unverifiable. The empirical fallback stands (our own injury-report history, 2021-22+, with CIs). Return-to-play duration by injury type is covered: R-99, R-100, R-105. See `lit-minutes-injury.md`.
- **Minutes projection in basketball**: searched in RSCH-002. **No dedicated peer-reviewed paper**; the adjacent availability/load-management work is R-101-R-104. The in-game mechanics are practitioner only (Rotogrinders heuristics, to be tested, not adopted). See `lit-minutes-injury.md`.
- **H2H opponent behaviour modelling**: no source found; deferred (C12).

## 12. Minutes and injury references (R-99…R-105; verified 2026-09-27, RSCH-002)

Full table, search log and quality ratings: `docs/research/lit-minutes-injury.md`.

- R-99 Bullock et al. (2022), PNAS Nexus: return to performance after severe NBA injuries. Peer-reviewed.
- R-100 Tummala et al. (2023), OJSM: NBA ankle injuries; minutes and usage associated with time loss. Peer-reviewed.
- R-101 Herzog et al. (2026), Sports Medicine: rest/load management and later injury. Peer-reviewed.
- R-102 Yu & Hu (2026), arXiv:2603.26935: survivor bias in NBA workload models. Preprint.
- R-103 Nakamura-Sakai, Forastiere & Macdonald (2024), arXiv:2402.12400: age-conditioned rest effects. Preprint.
- R-104 Cohan, Schuster & Fernandez (2021), J. Sports Analytics: deep-learning NBA injury forecasting. Peer-reviewed.
- R-105 Drakos et al. (2010), Sports Health: 17-year NBA injury overview. Peer-reviewed.

## 13. In-season trends, late-season rest/tanking, trade-deadline role, playoff scheduling (R-106…R-109; verified 2026-10-03, RSCH-008)

Full tables, search log and the per-question summary for RSCH-008: `docs/research/lit-in-season-trends.md`.
All four entries are Abstract/Crossref-metadata level only (no full text read this pass).

- R-106 Schall & Smith (2000), *American Statistician*: regression to the mean in baseball splits. Peer-reviewed (cross-sport, baseball).
- R-107 Albert (1994), *JASA*: hierarchical-model test of 8 situational splits incl. first/second-half. Peer-reviewed (cross-sport, baseball).
- R-108 Gong, Watanabe, Soebbing, Brown & Nagel (2022), *Sport Management Review*: NBA tanking via resting healthy players, 2006-07…2017-18. Peer-reviewed, NBA-specific.
- R-109 Nong & Huang (2026), *Journal of Sports Economics*: NBA trade-deadline bargaining dynamics; no individual minutes/role measure (weak fit, flagged as a gap). Peer-reviewed, NBA-specific.

**Gaps (explicitly unsupported by peer-reviewed literature; see `lit-in-season-trends.md` for detail):**
- no NBA-specific first-half/second-half split-persistence study (Q1 uses cross-sport R-106/R-107 for method only)
- no individual-player (vs. team-decision) minutes/games-missed effect size by playoff team-context (Q2)
- no peer-reviewed or credible quantitative source at all for fantasy-sports playoff-schedule weighting (Q3) — practitioner-only
- no peer-reviewed source measuring an individual player's minutes change specifically at the trade deadline (R-85, already catalogued in §10, is the closest fit — a general post-trade performance shock, not a minutes measure)
