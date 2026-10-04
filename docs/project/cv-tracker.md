# CV Tracker — resume-ready record of this project

_Last updated: 2026-09-24 · Owner: project owner · Maintained by: Claude (at milestones and on resume-worthy tasks)_

The purpose is to have concise, ATS-friendly bullets ready for a **Data Engineer**, **Data Scientist**, or **ML Engineer**
CV. The phrasing mirrors common job-posting and resume language: action verb + what was built + tools + scale + result.

## Rules (so every claim survives an interview)
1. **Only ✅ bullets go on a CV.** A bullet becomes ✅ when the work is merged, and every number in it comes from a real measurement (a linked report, CI log, or dashboard).
2. The statuses are 🟦 planned (don't use), 🟨 in progress (don't use), and ✅ done (use).
3. `{placeholders}` are filled only with measured values. Don't round up or invent metrics.
4. Each ✅ bullet links to **evidence** in the repo, which you can use for interview prep.
5. Wording uses standard posting keywords. Put the exact tool names in the Skills line so ATS filters match.

---

## 1. Project header (for the "Projects" section)

**NBA Fantasy Decision Engine** · Personal project · 2026–present
_Python · SQL · dbt · BigQuery · GCP (Cloud Run, Cloud Scheduler, Cloud Storage, Secret Manager) · Terraform · Docker · GitHub Actions · LightGBM · scikit-learn · Monte Carlo simulation · MILP optimisation_

Links (add when live): **Live demo** `<url>` · **Case study** `<url>` · **Code** `github.com/<user>/<repo>`

One-liner: _Built an end-to-end data platform and ML-driven decision engine that ingests NBA and Yahoo Fantasy data and delivers explainable, evaluated recommendations via mobile notifications._ 🟦

---

## 2. Data Engineer bullets

| Status | Bullet | Evidence |
|---|---|---|
| 🟨 | Architected a cloud-native **ELT data platform** on **GCP** using a **medallion architecture** (bronze/silver/gold), documenting {n} **Architecture Decision Records (ADRs)** covering storage, orchestration, security, and cost trade-offs | `docs/architecture/`, `docs/project/architecture-decisions.md` |
| 🟦 | Designed and built **batch data pipelines** in **Python** ingesting {n} sources (REST APIs, PDFs) into **Google Cloud Storage** and **BigQuery**, processing ~{rows}/day with **idempotent**, **incremental** loads and automated **backfills** | DATA-001…DATA-011 |
| 🟦 | Implemented **point-in-time (bitemporal) data modelling** with immutable raw snapshots and **SCD Type 2** history, enabling **leakage-free backtesting** of {n} historical decision dates | ADR-0005, DATA-014, DATA-022 |
| 🟦 | Developed {n} **dbt** models with {n} automated **data quality tests** (uniqueness, referential integrity, freshness, reconciliation), blocking bad data before it reached downstream consumers | `warehouse/`, DATA-023 |
| ✅ | Provisioned **infrastructure as code** with **Terraform** across **dev/prod** GCP projects: least-privilege **IAM** service accounts per workload, keyless **Workload Identity Federation** for CI/CD, and plan-time **policy tests** (8) that fail the build on an IAM or retention regression | INFRA-001/002, FND-017, WEB-012; `infra/terraform/modules/env/tests/env.tftest.hcl` |
| 🟦 | Orchestrated serverless workloads with **Cloud Scheduler** and **Cloud Run jobs**, achieving {x}% pipeline success rate and data freshness within {n} minutes of source updates at ~${cost}/month | INFRA-004, `gold.job_runs` |
| ✅ | Built **CI** with **GitHub Actions**: 7 required checks on every pull request (lint, strict type checks, 250+ unit tests with an 85 % coverage gate, a full **dbt build** in per-PR BigQuery datasets, secret and dependency **security scanning**, Terraform policy tests, frontend build with a bundle budget), with the slowest check under 2.5 minutes | FND-006, FND-017, WEB-001; ruleset on `main` |
| 🟦 | Established **data contracts** and schema-evolution handling with **Pydantic**, automatically quarantining malformed payloads and alerting via **Telegram** | DATA-002, FND-013 |
| 🟦 | Implemented privacy-by-design **pseudonymisation** of third-party user data at ingestion, with one-command **data deletion** for compliance | G-04 A2, DATA-004 |

## 3. Data Scientist / ML Engineer bullets

| Status | Bullet | Evidence |
|---|---|---|
| 🟦 | Built probabilistic **player performance forecasting** models (**LightGBM**, **quantile regression**, **empirical Bayes**) that reduced MAE by {x}% vs a strong statistical baseline across {n} stat categories, validated with **walk-forward (time-series) cross-validation** | ML-002, EVAL-003 reports |
| ✅ | Built season **player projection** models (**empirical Bayes shrinkage** with an age curve, a **ridge** minutes model with a pre-season role signal) that ranked player value better than a last-season baseline in **8/8** rolling-origin seasons (+0.016 Spearman, 95 % CI 0.009–0.023) and cut minutes-per-game error by 0.40 (95 % CI 0.32–0.49) on held-out seasons | `docs/evaluation/reports/DRAFT-002-backtest.md`, `DRAFT-008-backtest.md` |
| ✅ | Measured how often players listed on the official NBA **injury report** actually play, from **327 game days** (25.8K player-rows) of parsed PDFs joined to game logs, with day-clustered **bootstrap** CIs; replaced assumed priors (e.g. Doubtful: **1.1 %** measured vs 15–25 % commonly assumed) | `docs/evaluation/reports/MVP-002-availability.md` |
| 🟦 | Developed a calibrated **classification model** for player availability (**Brier score** {x}, **ECE** {x}) using **feature engineering** on {n}K historical injury reports | ML-003 |
| 🟦 | Designed a **Monte Carlo simulation** and **mixed-integer linear programming (MILP)** optimisation engine that generates head-to-head strategy recommendations for all 5 Yahoo scoring formats | DEC-003…DEC-008 |
| 🟦 | Built a **backtesting / historical replay** framework showing recommended lineups outperformed baseline strategies on {x}% of team-days (95% **bootstrap CI** {a}–{b}) | EVAL-006, DEC-011 |
| 🟦 | Established an **ML evaluation and model promotion gate** (paired block bootstrap, **Diebold–Mariano test**, **calibration** checks) so only statistically significant improvements reach production | EVAL-008 |
| 🟦 | Implemented **model monitoring** for accuracy and **drift**, with automated **retraining** pipelines and alerts | ML-005 |
| 🟦 | Delivered **explainable AI** recommendations using **SHAP** feature attributions and evidence-grounded explanations, tracked with a **recommendation outcome** log | DEC-009, EVAL-007 |
| 🟦 | Grounded the modelling methodology in peer-reviewed literature ({n} references), translating academic methods (G-score/H-score valuation, proper scoring rules) into production code | `docs/research/ml-literature-review.md` |

## 4. Cross-cutting bullets (engineering practice and AI-assisted development)

| Status | Bullet | Evidence |
|---|---|---|
| 🟨 | Designed an **AI-assisted development** workflow (**Claude Code** agents, skills, hooks) with **test-driven development (TDD)**, automated quality gates, and markdown-based project management, delivering {n} tasks with {x}% first-pass CI success | `docs/agents/`, `just agent-metrics` |
| 🟦 | Built a mobile-first **React/TypeScript** dashboard backed by a **FastAPI** REST API for decision support | APP/WEB tasks |

---

## 5. ATS keyword bank (tick when evidenced)

**Data engineering**
- [ ] Python
- [ ] SQL
- [ ] ETL/ELT
- [ ] data pipelines
- [ ] batch processing
- [ ] dbt
- [ ] BigQuery
- [ ] data warehouse
- [ ] data lake / lakehouse
- [ ] medallion architecture
- [ ] data modelling (Kimball, star schema, SCD Type 2)
- [ ] data quality
- [ ] data contracts
- [ ] data lineage
- [ ] orchestration
- [ ] GCP
- [ ] Cloud Run
- [ ] Cloud Storage
- [ ] Terraform / infrastructure as code
- [ ] Docker
- [ ] CI/CD
- [ ] GitHub Actions
- [ ] IAM
- [ ] data governance
- [ ] DataOps

**Data science / ML**
- [ ] machine learning
- [ ] feature engineering
- [ ] gradient boosting / LightGBM
- [ ] scikit-learn
- [ ] time-series forecasting
- [ ] probabilistic forecasting
- [ ] cross-validation
- [ ] model evaluation
- [ ] calibration
- [ ] A/B-style evaluation / backtesting
- [ ] statistical inference / hypothesis testing
- [ ] Monte Carlo simulation
- [ ] optimisation (MILP)
- [ ] explainability / SHAP

**MLOps**
- [ ] model registry
- [ ] experiment tracking
- [ ] model monitoring
- [ ] drift detection
- [ ] retraining pipelines
- [ ] reproducibility

**Common in postings but not in this project** (don't claim them; learn separately if a target role needs them): Spark/PySpark, Kafka/streaming, Airflow, Snowflake, Databricks, Kubernetes, PyTorch/TensorFlow, LLM/RAG.

---

## 6. Metrics to capture as the build progresses
- Pipelines: number of sources, rows/day, success rate, freshness (minutes), cost/month, backfill volume
- Data quality: number of dbt models, number of tests, incidents caught before reaching recommendations
- CI/CD: PR pipeline duration, deploy frequency, rollback time
- ML: MAE improvement vs baseline (per stat, with CI), Brier score/ECE, interval coverage
- Decisions: replay win-rate vs baselines (with CI), recommendation hit rate by confidence band
- Delivery: tasks completed, first-pass CI rate (from `just agent-metrics`)

## 7. Interview stories (STAR-ready decision trade-offs)
Each story links to its ADR or decision record:
1. **BigQuery over DuckDB**: serverless Cloud Run has no persistent disk, so the warehouse had to be network-accessible. The trade-off was local speed versus operational fit (D-04).
2. **Point-in-time correctness**: why the system stores what it *knew when*, and how that prevents backtest leakage (ADR-0005, [R-60]).
3. **Simulation over static rankings**: matchup-aware valuation grounded in the fantasy-basketball literature (D-19, [R-02]).
4. **Cost-conscious orchestration**: Cloud Scheduler + Cloud Run for pennies, versus Cloud Composer at ~$300–400/month (D-10).
5. **Privacy by design**: pseudonymising other managers at ingestion (G-04 A2).

## 8. Change log
| Date | Change |
|---|---|
| 2026-09-24 | Tracker created. Architecture and decision records in progress (🟨). All build bullets planned (🟦). |
| 2026-09-28 | Terraform and CI bullets reworded to what is built (no Docker, no Secret Manager yet) and marked ✅ with evidence. Two new ✅ DS bullets from measured backtests (DRAFT-002/008) and the injury-report study (MVP-002). |
