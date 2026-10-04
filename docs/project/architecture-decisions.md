# Architecture & Technology Decisions — pick your options

Version 0.1 · 2026-09-24 · Status: **ALL ITEMS SELECTED** (2026-09-24; gate G-17 approved). Each item records its `**Selected**` option; ARCH-001 reconciled the architecture docs and ADRs.

The architecture documents (`docs/architecture/*`) and the ADRs are currently **proposals** that assume the ★
option for each decision below. Nothing is final until you choose. Each item has:
- a **Learn** primer: what the concept is and why it matters here
- the realistic options, with pros and cons
- a justified recommendation

Coding conventions live separately in [`standards-decisions.md`](standards-decisions.md) (S-xx). Items that also
appear there are cross-referenced rather than repeated.

**How to reply**:
- `D: accept all recommended`
- `D-03 B, D-11 C, rest recommended`
- `explain D-12`: Claude expands on it, with examples
- `compare D-12 A vs C`: a side-by-side deep dive

Where an item needs your answer before 20 Oct (tip-off), it is marked ⏰.

---

## Part 0 — Foundations (tech stack round 1, decided in chat 2026-09-24)

| Item | Decision | Selected |
|---|---|---|
| F1 Main language | ★A Python (data/ML ecosystem; NBA and Yahoo client libraries) · B TypeScript throughout · C Python + R | **A** — 2026-09-24 |
| F2 Python version | ★A 3.13 · B 3.14 · C 3.12 | **A** — 2026-09-24 (= S-01 A) |
| F3 Package/env manager | ★A uv (fast, workspaces, manages Python itself) · B Poetry · C pip+venv | **A** — 2026-09-24 (= S-02 A) |
| F4 Task runner | ★A just · B make · C Python scripts · D poethepoet (tasks in pyproject, run via uv) | **A** — 2026-09-24 |
| F5 Containers | ★A Docker · B Podman · C none | **A** — 2026-09-24 (= S-23 A) |
| F6 GitHub CLI | ★A gh (automated PR/merge flow) · B web-only | **A** — 2026-09-24 |

---

## Part 1 — System shape

### D-01 Where the system runs (deployment shape) ⏰ 🔗 G-06
**Learn**:
- *Local-first* means the laptop is the primary runtime. *Cloud-first* means a server or cloud service is. *Hybrid* splits the jobs between them.
- One constraint dominates here: **stats.nba.com blocks cloud IP addresses**, so some NBA history can only be fetched from a home connection.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **Local-first now; hybrid VPS later (Phase 8)** | $0 while building; home IP works for every source; identical code runs on a VPS later | Daily jobs only run while the laptop is on (catch-up logic covers the gaps) | $0 → ~$5/mo |
| B | Cloud-first (VPS) from day one | Always on from the start | stats.nba.com backfills still need the laptop; ops work before any value | ~$5/mo |
| C | Serverless (Cloud Run + storage + scheduler) | Pay per use | Cold starts; a file-based database is awkward on serverless; stats.nba.com is blocked | ~$0–3/mo |
| D | Home server (mini-PC/Pi) | Always on *and* a home IP; no monthly fee | Hardware to buy and look after | ~$100 one-off |

**Why ★A**: it gives the fastest route to collecting data before tip-off at $0, and it keeps the move to B or D a matter of changing config.

**Provider refined 2026-09-24: GCP serverless.** Cloud Scheduler triggers Cloud Run jobs, which run the pipeline; the API/dashboard is also on Cloud Run. Consequence: there's no persistent server disk, so the production database must be network-accessible (see D-04: BigQuery or MotherDuck, not a local DuckDB file).

**Selected**: B — 2026-09-24. The owner wants production use with phone alerts, so the server runs from the start of collection rather than Phase 8. The historical stats.nba.com backfill is downloaded once at home and uploaded. The schedule follows the owner's awake window (see D-33).

### D-02 Repository structure 🔗 S-02
**Selected**: A (packages + apps + warehouse + infra; import-linter) — 2026-09-24

**Learn**: a *monorepo* holds every component in one repository. Within one, you choose how strongly the boundaries between components are enforced.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Workspace: `packages/*` libraries + `apps/*` deployables + `warehouse/` (dbt) + an enforced import-layering check** | Each part is testable alone; agents can work in one package with a small context; the architecture is enforced by CI | A bit of setup boilerplate |
| B | A single Python package with sub-modules | Simplest | Boundaries erode; everything can import everything |
| C | Polyrepo (a repo per component) | Hard isolation | You asked for a monorepo; cross-repo changes are painful |

### D-03 Service architecture
**Selected**: A (modular monolith: one image, Cloud Run entrypoints) — 2026-09-24

**Learn**:
- A *modular monolith* is one deployable app with strict internal module boundaries.
- *Microservices* split the system into separately deployed services that talk over the network.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Modular monolith: one image with two entrypoints (API and scheduler)** | Simple deploys; no network calls between components; right-sized for one user | Everything scales together (irrelevant at this size) |
| B | Microservices (ingest, model, API services) | Independent scaling and deploys | Big ops and complexity overhead for no benefit here |

---

## Part 2 — Data platform

### D-04 Analytical database ⏰
**Selected**: **BigQuery everywhere (B2)** — 2026-09-24. Dev, CI and prod all use BigQuery (separate datasets/projects per environment). This follows from the Cloud Run runtime having no persistent disk. The owner accepts managing credentials properly (see the infrastructure round). Supersedes the ★ DuckDB proposal; ARCH-001 must revise ADR-0004 and the architecture.

> **Owner interest (2026-09-24): possible eventual migration to GCP.** Design seams to keep that cheap:
> - bronze is written through a storage abstraction (fsspec), so `DATA_ROOT` can be a local path or `gs://`
> - dbt models use cross-database macros
> - Python reads go through interfaces, not raw DuckDB calls everywhere
>
> The migration target would be BigQuery (free tier: 10 GiB storage + 1 TiB queries/month) with the dbt-bigquery adapter.

**Learn**:
- An *OLAP* engine is optimised for analytical scans and aggregations, like "average rebounds over the last 14 days for every player".
- An *OLTP* engine is optimised for many small concurrent transactions.
- Our workload is almost entirely OLAP.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **DuckDB (embedded, a single file) + raw files** | Very fast analytics; nothing to run; reads JSON/Parquet directly; excellent dbt support | One writer at a time | $0 |
| B | PostgreSQL | A robust general-purpose database; concurrent writers | A server to run; slower for analytics | $0 local |
| C | MotherDuck (hosted DuckDB) | Same engine, accessible anywhere | Not needed yet; free-tier limits | $0–25/mo |
| D | BigQuery / Snowflake | Huge scale | Cost, and no real local development | $$ |

**Why ★A**: all our data (< 5 GB) fits on one machine with room to spare, and it can be upgraded to C later without rewriting code.

### D-05 How raw data is kept (history model) ⏰ 🔗 G-04
**Learn**:
- *Point-in-time correctness* means we can reconstruct exactly what was known at any past moment.
- It needs **bitemporal** data, which tracks two times: when something was true in the world, and when *we observed it* [R-65].
- Without it, backtests "cheat" by using information from the future. This is called *leakage* [R-60].

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **An immutable, append-only raw snapshot of every API response, with `observed_at`, plus state-history (SCD2) tables** | Exact replay of any past decision; leakage is testable; everything can be rebuilt from raw | More storage (only a few MB/day) |
| B | Keep only the latest state (overwrite) | Simple | Makes honest backtesting impossible; history is lost for good |
| C | Store only the diffs between snapshots (event sourcing) | Compact | Complex, and fragile to rebuild |

**Selected**: A, with the G-04 A2 privacy rule — 2026-09-24. Yahoo payloads are pseudonymised by a deterministic, versioned transform *before* the bronze write. Bronze stays immutable, but holds the pseudonymised payload rather than the exact original.

### D-06 Data layering (medallion) 🔗 S-10
**Selected**: medallion concept with dbt-native names (S-10 B) — 2026-09-24

**Learn**: the *medallion architecture* organises data into layers of increasing quality:
- **Bronze**: raw, exactly as received.
- **Silver**: cleaned, typed, deduplicated.
- **Gold**: business-ready facts, dimensions, and marts.

Quality checks guard each step up.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Bronze / silver / gold, plus a serving layer (features, predictions, recommendations), with a quality gate at every boundary** | A clear contract per layer; failures are caught early and cheaply | More models to name and maintain |
| B | Two layers (raw → marts) | Less structure | Cleaning and business logic get mixed; harder to debug |
| C | dbt's staging / intermediate / marts naming | Standard dbt vocabulary | Equivalent to A in practice; a naming choice only (S-10) |

### D-07 Ingestion approach
**Selected**: A (own thin layer) — 2026-09-24. Raw files are written to Cloud Storage via a storage abstraction; BigQuery reads them through dbt sources (external tables / load jobs). PDFs use the same mechanism.

**Learn**: *ingestion* means fetching data from the source APIs and landing it in bronze. The options range from frameworks that handle much of it for you to writing a thin layer yourself.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Our own thin framework** (HTTP client + retries + rate limits + snapshot store, ~400 lines) | Full control over the raw snapshots and `observed_at`; easy to test | We maintain it |
| B | dlt (data load tool) | Schema inference; incremental state; many connectors | It normalises data away from the raw payloads by default, which fights D-05 A; a second state system |
| C | Call the Python wrappers (yfpy, nba_api) and store their objects | Fastest start | We lose the raw payloads; tied to how the libraries parse data |

### D-08 Transformation tool 🔗 S-09
**Selected**: A (dbt) — 2026-09-24

See **S-09**: dbt (★) / SQLMesh / Dataform (BigQuery-only) / pure Python.

**Learn**: these tools turn SQL files into a tested, documented dependency graph. Dataform only runs on Google BigQuery, which conflicts with D-04 A.

### D-09 Semantic layer (the single definition of fantasy stats)
**Selected**: A (Python `LeagueRules`, generating the dbt macros) — 2026-09-24

**Learn**:
- A *semantic layer* defines each metric once, e.g. "FG% = sum(FGM) / sum(FGA), never an average of percentages".
- Every consumer (SQL, Python, the dashboard) then uses that same definition.
- For us, the definitions come from **your league's settings**.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **A Python `LeagueRules` model built from the Yahoo settings, which also generates dbt macros** | One source of truth; works for all 5 scoring formats; testable | Custom code (small) |
| B | dbt Semantic Layer / MetricFlow | Standard metric definitions | Heavy; its best features need dbt Cloud; can't express the format-specific logic |
| C | Cube.dev | A powerful metrics API | A separate service; overkill |

### D-10 Orchestration (running jobs in order, on schedule) 🔗 S-13
**Selected**: A (CLI job runner + scheduler) — 2026-09-24. The owner asked about Airflow and Vertex Pipelines. Assessment: Airflow is too heavy to self-host on a small VM, and Cloud Composer costs ~$300–400/mo. Vertex Pipelines (~$0.03/run + compute) fits heavy ML retraining, not 15-minute polling. If we move to GCP, the natural equivalent of A is Cloud Scheduler + Cloud Run jobs.

See **S-13**: a CLI + OS scheduler (★) / Dagster now / Prefect.

**Learn**: an orchestrator runs jobs in dependency order, retries them, and tracks runs. Dagster adds a lineage UI and backfill tooling, at the cost of a resident process and a larger API for agents to learn.

### D-11 Data quality tooling 🔗 S-11, S-12
**Selected**: dbt tests (S-11 A) with the two-severity policy (S-12 A) — 2026-09-24

See **S-11** (tools) and **S-12** (failure policy).

**Learn**:
- Checks cover validity, uniqueness, completeness, consistency, timeliness, and referential integrity.
- *Reconciliation* checks that two independent computations agree, e.g. our totals vs Yahoo's.

---

## Part 3 — Data sources

### D-12 NBA statistics source ⏰ 🔗 G-05
**Learn**: the NBA has no official free public API. The free options are undocumented endpoints behind NBA.com, which can change without notice. The paid APIs are documented but cost money, and some are less complete.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **Free NBA.com endpoints**: `cdn.nba.com` (schedule, box scores) + `stats.nba.com` via `nba_api` (history, home IP only) | Most complete data; free | Unofficial; can change; stats.nba.com is blocked from the cloud | $0 |
| B | BALLDONTLIE paid API | Documented, stable, includes injuries | $9.99/mo tier lacks box scores and lineups ($39.99 has them) | $10–40/mo |
| C | A with automatic failover to B | Resilient | Costs money even when unused (subscription) | $10/mo |
| D | Basketball-Reference scraping | Deep history | 20 requests/min limit, licensing problems, fragile | $0 |

**Why ★A**: it's free and complete. Monitoring catches breakages within a day, and B is pre-evaluated as the fallback.

**Selected**: A — 2026-09-24 (owner: "stay free for now"; MySportsFeeds $5 trial and BALLDONTLIE kept as fallbacks, DISC-009).

### D-13 Injury data source ⏰
**Selected**: A (own versioned parser; `nbainjuries` as the test oracle) — 2026-09-24

**Learn**:
- The NBA publishes official **injury reports** (PDFs) several times a day, with designations such as Out, Doubtful, Questionable, and Probable.
- Their *history* back to 2021-22 lets us learn how often, e.g., "Questionable" players actually play.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Fetch the official PDFs ourselves and parse them with our own versioned parser, using the `nbainjuries` package as a reference and test oracle** | Full control; no dependency risk; keeps every report version | Parser to maintain when the layout changes |
| B | Use the `nbainjuries` package directly | Fastest | Depends on one maintainer's package |
| C | A paid injury API (BALLDONTLIE $9.99) | Clean data | Cost; may not keep every intraday version |

DISC-005 tests A vs B before we commit.

### D-14 Yahoo Fantasy client ⏰ 🔗 G-03
**Selected**: A (own small client, read-only scope). This follows from D-07 A + G-03 A — 2026-09-24

**Learn**:
- Yahoo's API uses **OAuth 2.0**: you approve access once, and the app then keeps a *refresh token* to get new short-lived access tokens.
- The *scope* sets the permissions: read-only, or read and write.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Our own small client (JSON, read-only scope), with yfpy used only as a reference during discovery** | Raw payloads kept (D-05); minimal permissions | We handle token refresh (standard, small) |
| B | yfpy as the runtime client | Mature, handles auth | Returns parsed objects, which makes raw capture awkward |
| C | Read/write scope (automatic lineup moves) | Could set lineups automatically | Riskier; a separate product decision for later |

### D-15 Player ID matching (NBA ↔ Yahoo)
**Selected**: A (automatic matching + overrides + a 100 % coverage test; unmatched players are resolved via Telegram) — 2026-09-24

**Learn**: the same player has different IDs in NBA data and Yahoo data. Linking them (a *crosswalk*) must be near-perfect, or recommendations silently miss players.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Automatic matching (normalised name + team + position) + a manual overrides file + a 100 %-coverage test** | Accurate, auditable | Occasional manual overrides |
| B | Fuzzy name matching only | Zero maintenance | Silent mismatches (e.g. two players with similar names) |
| C | A third-party ID map | Less work | Another dependency; may lag new players |

---

## Part 4 — Intelligence (ML, statistics, decisions)

All options cite the literature review (`docs/research/ml-literature-review.md`).

### D-16 How player projections are built 🔗 G-14
**Selected**: A (decomposed; baselines first) — 2026-09-24

**Learn**:
- A *projection* forecasts a player's stats for a future game.
- *Decomposing* means forecasting the pieces separately and combining them: will he play, how many minutes, and what per-minute rates.
- *Empirical-Bayes shrinkage* pulls noisy small-sample rates towards sensible averages. It is a classic, proven technique [R-10–R-12].

| | Option | Pros | Cons | Grounding |
|---|---|---|---|---|
| ★A | **Decomposed: P(plays) × minutes × per-minute rates; statistical baselines first; ML replaces each piece only if it measurably wins** | Each piece is testable and explainable; value arrives early; clear failure diagnosis | More components | [R-11–R-13] baselines; [R-20–R-22] ML |
| B | One gradient-boosted model per stat, predicting totals directly | Fewer parts | Mixes up availability and role; weak uncertainty estimates | [R-20] |
| C | A full hierarchical Bayesian model (PyMC) | Principled uncertainty | Slow to fit; hard to maintain and explain | [R-11] is its practical approximation |
| D | Deep learning (sequence models) | Flexible | Needs far more data; opaque; no evidence it beats boosting on small tabular data | — |

### D-17 How uncertainty is represented
**Selected**: A (negative-binomial count distributions, makes/attempts jointly) — 2026-09-24

**Learn**:
- Decisions in category leagues depend on **variance**, not just averages. A player averaging 2 blocks with huge swings is riskier than a steady one [R-01].
- Win probabilities come from *distributions*.

| | Option | Pros | Cons | Grounding |
|---|---|---|---|---|
| ★A | **Parametric count distributions (negative binomial), with made/attempted shots modelled jointly; checked by calibration tests** | Fast to simulate; statistically standard for over-dispersed counts | Assumes a distribution shape (verified by tests) | [R-30, R-42, R-44] |
| B | Quantile regression for every stat | No shape assumption | Many models; percentages are awkward | [R-22] |
| C | Resample historical residuals (bootstrap) | Simple; uses the data's real shape | Weak for players with little history | [R-54] |

### D-18 Availability (will he play?) model 🔗 G-14
**Selected**: A (staged: table → logistic → calibrated GBM) — 2026-09-24

**Learn**:
- This is a probability forecast. What matters is *calibration*: of all players given 70 %, about 70 % should play.
- Boosted trees tend to be miscalibrated and need a correction step [R-47].

| | Option | Pros | Cons | Grounding |
|---|---|---|---|---|
| ★A | **Staged: a lookup table (designation → rate) → logistic regression → calibrated gradient boosting; each stage kept only if it beats the previous one** | Simple first; improvements are proven | Three steps to build over time | [R-40, R-46, R-47] |
| B | Lookup table only | Trivial | Ignores timing, back-to-backs, and player history |
| C | Straight to gradient boosting | Most expressive | Needs calibration anyway; harder to explain | [R-47] |

### D-19 How decisions are valued (the core of the recommendation engine) 🔗 G-14
**Selected**: A (Monte Carlo simulation + per-format objectives) — 2026-09-24

**Learn**:
- *Static rankings* (Z-scores) value players in isolation.
- Rosenof's work shows that in head-to-head leagues, value **depends on your team and your opponent**, e.g. a steals specialist matters more when steals are a close category this week [R-01, R-02, R-03].
- *Monte Carlo simulation* plays the week thousands of times to estimate win probabilities.

| | Option | Pros | Cons | Grounding |
|---|---|---|---|---|
| ★A | **Simulate the matchup or season; value each action by its change in the scoring format's objective (per-format plug-ins)** | Correct for all 5 Yahoo formats; naturally discovers punting and targeting strategies; explainable ("+0.4 expected category wins") | More compute (still seconds) | [R-02, R-03, R-61] |
| B | Static Z/G-score rankings | Simple, fast, familiar | Ignores the matchup and team context; wrong for One Win and roto dynamics | [R-01] |
| C | A learned ranking model | Could learn subtle patterns | No training labels until ~a season of logged recommendations | [R-62] |

B is kept as a baseline and an explanation aid. C is a Phase 9 experiment.

### D-20 Lineup optimiser
**Selected**: A (MILP with HiGHS) — 2026-09-24

**Learn**:
- Choosing who starts, given position slots, is a combinatorial problem.
- *Mixed-integer linear programming* (MILP) finds the provably best answer quickly at this size.

| | Option | Pros | Cons | Grounding |
|---|---|---|---|---|
| ★A | **MILP with the HiGHS solver (free, open source)** | Optimal, fast, handles eligibility exactly | Needs a formulation (small) | [R-04] |
| B | Greedy heuristic (best player per slot in order) | Trivial | Can be suboptimal with multi-position players |
| C | Constraint programming (OR-Tools CP-SAT) | Very flexible | More than we need |

### D-21 Validation & promotion of models 🔗 S-16, S-17
**Selected**: walk-forward weekly (S-17 A) + a statistical promotion gate (S-16 A) — 2026-09-24

See **S-16** (the gate: statistical CI ★ / fixed threshold / owner judgement) and **S-17** (walk-forward ★ / season splits).

**Learn**: *walk-forward* validation trains on the past and tests on the next week, repeatedly. It mirrors real use and avoids future information leaking into training [R-50, R-51].

### D-22 Explanations 🔗 G-09
**Selected**: A (templates + SHAP; numbers test) — 2026-09-24

**Learn**: an explanation should restate the evidence; it should never invent it. *SHAP values* attribute a model's prediction to its inputs [R-23, R-24].

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **Templates filled from structured evidence + SHAP drivers; a test checks every number** | Always accurate; free | Can read a bit mechanically | $0 |
| B | A + the Claude API rephrasing the text (must pass the same test) | Natural language | Separate API billing (not Claude Pro) | ~$0.10–1/mo |
| C | An LLM writes explanations freely | Most fluent | May hallucinate facts, which is unacceptable for decisions | ~$1/mo |

### D-23 Experiment tracking & model registry 🔗 S-15
**Selected**: **MLflow** (tracking + model registry; chosen partly for CV value) — 2026-09-24. Follow-up for the ops round: where the MLflow server and backend store live on GCP (e.g. Cloud Run + Cloud SQL, or a lighter file-backed setup) and what it costs. Markdown reports are still generated from MLflow runs, for phone reading. ARCH-001 must revise ADR-0014.

See **S-15**: JSON manifests + markdown reports (★) / MLflow / W&B.

### D-24 Feature store
**Selected**: A (point-in-time feature views in code) — 2026-09-24

**Learn**: a *feature store* is a system for serving ML inputs consistently for training and prediction. Large companies need them; small projects usually don't.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Point-in-time feature views in code (no separate store)** | Simple; one place to test leakage | Features are recomputed each run (seconds) |
| B | Feast | Industry-standard tooling | A heavy extra system for one user |

### D-25 Text/NLP signals (includes your `laya` question)
**Selected**: A (rules now; LLM via the D-32 spike; laya only via EXP-001) — 2026-09-24

**Learn**:
- Some useful signals are free text, like injury "reasons" ("rest", "left ankle sprain") or news.
- `laya` is a ~400M-parameter model that answers typed questions about text or JSON in one pass (technology evaluation §14).

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Keyword and rule mapping of injury-report reasons now; test a model later (EXP-001) only if the rules demonstrably fall short** | Free, transparent, probably sufficient for the structured reason field | Misses nuance in free-form news |
| B | Integrate laya now for text classification | Handles nuance | +1–2 GB of dependencies; slow on CPU; unproven benefit here |
| C | Use laya for decisions themselves | — | Not suitable: our decisions are numeric optimisation that needs calibrated probabilities and auditable evidence |

---

## Part 5 — Application & operations

### D-26 Dashboard 🔗 S-24, G-07
**Selected**: A (React + TypeScript SPA on Cloud Run, with a chat panel for D-36) — 2026-09-24

See **S-24**: React SPA (★) / Streamlit / HTMX / Evidence.

In the meantime, daily **markdown reports** give you value from Phase 3 on, readable on your phone through Claude.

### D-27 Dashboard access & security 🔗 G-16
**Selected**: **App-level login** — 2026-09-24. Proposed implementation (to confirm in ARCH-001): Google sign-in via Firebase Auth / Identity Platform, an allowlist of just the owner's email, server-side token verification on every API call, rate limiting, and a security review task. Cloud Run IAP (no extra cost, GA) remains the fallback if app login proves costly to secure.

**Learn**: *Tailscale* creates a private network between your devices. The dashboard is reachable from your phone but invisible to the internet, with no login system to build.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Tailscale-only access** | Secure by default; free; no auth code | Tailscale app needed on your phone |
| B | A public URL behind Cloudflare Access (email login) | Works from any browser | More setup; publicly addressable |
| C | Public with app-level login | Standard web approach | Auth code to build and secure |

### D-28 Scheduling mechanism 🔗 S-13
**Selected (2026-09-24)**: production uses **Cloud Scheduler + Cloud Run jobs**, honouring the awake window (NFR10). Local development uses the same job CLI, run by hand or by Task Scheduler.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Windows Task Scheduler now; cron in the container later (both generated from one `schedules.yaml`)** | Native; can wake the laptop to run | Two runners (generated from one file) |
| B | GitHub Actions scheduled workflows | No machine needed | Cloud IPs are blocked by stats.nba.com; no persistent disk |
| C | Keep a Docker container always running locally | Same as production | Docker Desktop must be running |

### D-29 Backups
**Selected**: GCP-native: prod raw bucket versioning + retention lock, weekly BigQuery export to GCS, and BigQuery 7-day time travel — 2026-09-24

**Learn**:
- *Raw* is the system of record. Everything else can be rebuilt from it.
- So backing up `raw/` (a few GB at most) is what matters.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **Cloudflare R2 object storage (nightly sync)** | Off-site; free up to 10 GB; no fees for downloading | An account to create | $0 |
| B | Sync `DATA_ROOT` into your OneDrive folder | Already installed; zero setup | Syncing a live DuckDB file can corrupt copies (export snapshots instead); your personal storage quota | $0 |
| C | Backblaze B2 | Cheap, reliable | Download fees | ~$0 |

### D-30 CI/CD platform & release model 🔗 S-18–S-22, G-01
**Selected**: covered by S-18 (trunk), S-19 (conventional commits), S-20 (tiers), S-21 (public repo), S-22 (tagged releases) — 2026-09-24

See the **S-18–S-22** items (branching, commits, merge tiers, GitHub plan, releases).

**Learn**:
- *CI* (continuous integration) runs checks on every change.
- *CD* (continuous delivery) packages and deploys tested builds.
- *Trunk-based development* keeps one main branch, with short-lived task branches.

---

### D-31 Commercial optionality
**Selected (owner's words, 2026-09-24)**: "flexible enough that someone else can use it, but not designed for a massive user base". Interpreted as **small multi-user ready**:
- data is keyed by league and user (no single-owner assumptions)
- each user connects their own Yahoo account (per-user OAuth tokens in Secret Manager)
- the app login uses an allowlist of several emails
- per-user notification settings (Telegram chat ID, awake window, time zone)
- a per-user cap on LLM questions
- **Not** included: scaling infrastructure, billing/subscriptions, sharding

Commercial use would still need Yahoo's permission and licensed data (see `commercial-view.md`).

**Confirmed by the owner** — 2026-09-24.

**Learn**:
- The project is personal, but some design choices make a future product easier or harder.
- *Seams* are clean boundaries (e.g. "the data source is swappable") that cost little now and save a rewrite later.
- See [`commercial-view.md`](commercial-view.md).

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Personal-first, with cheap seams**: swappable data sources, league rules read from config, no hard-coded league or user, a commercial-view doc kept current | Nearly free (mostly already in the design); keeps the door open | Going multi-user would still need real work |
| B | Design multi-user from day one (accounts, per-user data separation) | A faster path to a product | Slower now; Yahoo's terms forbid monetisation anyway |
| C | Purely personal; ignore commercial concerns | Simplest | Harder to pivot later |

### D-32 Pre-game news (minutes limits, rest, late scratches) — owner-proposed
**Selected**: spike first (DISC-008), then choose — 2026-09-24

**Learn**:
- The official injury report (every 15 min) misses nuance like "minutes restriction", "will play but come off the bench", or rest decisions that reporters post first.
- An LLM can read short news items and **extract structured facts**: player, status, minutes cap, source, time.
- Two rules apply:
  - Only use sources whose terms allow automated access. Many sites and X/Twitter forbid scraping, and the X API is paid.
  - Treat LLM output as a cited signal, never as unverified fact.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **Scheduled extraction: a script fetches permitted sources (official team/NBA injury updates, RSS feeds whose terms allow it) about 90 and 45 min before the first relevant tip-off, for relevant players only (your roster, your opponent's, stream targets). The Claude API (Haiku) extracts cited, structured facts into bronze with `observed_at`** | Cheap, targeted, point-in-time-correct, testable; you can see every source | Free sources lag X/Twitter by minutes to an hour; separate API billing | Expected small (measured in DISC-008) |
| B | The same, but run by a scheduled Claude Code routine | No separate API bill | Uses your Claude Pro allowance; less deterministic; harder to test | Pro usage |
| C | A paid feed with lineups/news (BALLDONTLIE $39.99, MySportsFeeds add-ons, SportsDataIO) | Structured, no LLM | Cost; timeliness unverified for the cheaper feeds | $5–40+/mo |
| D | Skip news; rely on the 15-min official injury reports | Simplest, $0 | Misses minutes limits and late nuance | $0 |

A and C must prove their value like any model: extraction accuracy on a labelled sample, and a measurable improvement in the availability and minutes forecasts [R-40, R-41]. The laya model (D-25) could stand in for Haiku inside option A if it proves cheaper and equally accurate.

---

## Part 6 — Production operating model (owner question, 2026-09-24)

### D-33 How the pipeline reacts to new information
**Learn**:
- *Event-driven* means work starts when something changes, rather than on a fixed clock.
- Neither Yahoo nor the NBA sends us events (no webhooks), so a truly push-based design isn't available.
- The practical pattern is **"poll on a schedule, process on change"**: cheap pollers fetch often, and the content hash we already store detects real changes. Only a change triggers the heavier recompute and a possible notification.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Scheduled polling + change detection → an in-process event queue → targeted recompute → notify only if a recommendation materially changes** | Reacts within one polling interval; most runs cost nothing; no extra infrastructure | The scheduler must be always-on to react in time |
| B | Fixed batch runs only (e.g. overnight + morning) | Simplest | Misses late injury news; alerts arrive after lineups lock |
| C | A message broker (Redis/Kafka/cloud pub-sub) | "Real" event infrastructure | Overkill for one user and a handful of sources |

**Selected**: A — 2026-09-24. **Owner rule: awake-window scheduling.** Decisions are only made while the owner is awake, so nothing user-facing runs or notifies during sleep hours. Overnight changes are consolidated into one morning catch-up. Data that can't be recovered later is still captured, minimally (details in the spec, NFR10).

### D-34 Phone notification channel
**Learn**: push services deliver alerts to your phone. They differ in cost, interactivity, and whether you can reply.

| | Option | Pros | Cons | Cost |
|---|---|---|---|---|
| ★A | **ntfy** (open-source push app) | Free; priorities, quiet hours, action buttons (open the dashboard or Yahoo); trivial to send | One-way (buttons open links; no conversation) | $0 |
| B | Telegram bot | Free; **two-way** (you could reply "why?" or "show alternatives"); rich formatting | A bot to build; Telegram account | $0 |
| C | Pushover | Very reliable; polished | Paid app | ~$5 one-off |
| D | Email digest only | Nothing to install | Easy to miss; not urgent-capable | $0 |

**Selected**: B (Telegram bot, two-way) — 2026-09-24.

### D-35 Acting on a recommendation
**Learn**:
- With the **read-only** Yahoo scope (G-03 A), the system can only *advise*. You make the move in the Yahoo app, and a notification button can deep-link there.
- *Read/write* scope would allow **one-tap approve**, where the system makes the move after you confirm. Full autopilot makes moves without asking.

| | Option | Pros | Cons |
|---|---|---|---|
| ★A | **Advise only; you tap through to Yahoo to act (v1)** | Zero risk of unwanted moves; simplest | A few taps per move |
| B | One-tap approve (needs Yahoo write scope + an approval step) | Fast; you stay in control | Write-scope risk; more to build and test; revisit after M3 |
| C | Autopilot for low-risk actions (e.g. daily lineup only) | Hands-off | Mistakes cost matchups; only worth considering after a season of proven accuracy |

**Selected**: A (advise only in v1) — 2026-09-24.

---

## Part 7 — Infrastructure & access (decided in chat 2026-09-24)

| Item | Options | Selected |
|---|---|---|
| I1 Infrastructure as code | ★A Terraform · B OpenTofu · C Pulumi · D gcloud scripts | **A Terraform**; state in a locked GCS bucket |
| I2 Environments | ★A two GCP projects: dev, prod (CI uses ephemeral per-PR datasets in dev) · B dev/staging/prod · C one project | **A** |
| I3 Dev data | ★A dev reads the prod raw bucket read-only · B nightly copy · C dev collects its own | **A**. Prod raw bucket: retention lock + versioning. Dev buckets expire after 30 days |
| I4 CI → GCP auth | ★A Workload Identity Federation (keyless; prod deploys only from `main`) · B SA key secret | **A** |
| I5 Access model | ★A per-workload service accounts, least privilege; owner = break-glass; **Claude: dev only; prod changes only via CI** · B Claude may run prod commands with approval · C one broad identity | **A** + amendment (G-00 review, 2026-09-24): Claude also gets read-only prod logging/monitoring viewer roles |
| I6 Secrets | ★A Secret Manager per env; the Yahoo token manager writes new versions; local `.env` holds dev values only · B env vars / .env | **A** |

Always included: a billing budget alert at the G-08 ceiling, sent to Telegram.

### D-36 Natural-language questions in the dashboard (owner requirement, 2026-09-24)
**Learn**: an LLM can answer questions like "who should I stream for blocks?". The difference between the options is where the facts come from.

| | Option | Notes |
|---|---|---|
| ★A | **LLM + vetted tools** | The Claude API picks from our functions (projections, matchup state, what-if, compare) and answers with cited numbers only. Accurate; ~cents per question (separate API billing); strong CV value (LLM agents / tool use) |
| B | Text-to-SQL over the BigQuery marts | Flexible; risk of plausible-but-wrong SQL |
| C | GCP-managed conversational analytics agent | GCP-native; less control; availability and pricing to verify |
| D | Not in the dashboard (Claude Code / Telegram only) | No build |

**Selected**: A — 2026-09-24. The same agent backs the two-way Telegram bot (D-34). Grounding rule as D-22: every number in an answer must come from a tool result (tested). Requires an Anthropic API account and key (owner action) and counts toward the G-08 cost ceiling.

### D-37 MLflow hosting (2026-09-24)
| | Option | Notes |
|---|---|---|
| ★A | **Laptop MLflow + GCS artifacts; promoted models exported to GCS for Cloud Run** | $0; retraining runs when the laptop is on |
| B | Cloud Run + Cloud SQL Postgres | ~$8–10/mo; always reachable |
| C | Cloud Run + SQLite on a GCS mount | Near $0; fragile |

**Selected**: A — 2026-09-24.

### D-38 Public showcase for CV visitors (owner requirement, 2026-09-24)
**Selected**:
- **A public demo + case study**:
  - A public site containing a case-study page (architecture, evaluation results with CIs, decision log) and the dashboard in **read-only demo mode**, running on anonymised or replayed data.
  - The owner's real app stays behind login (D-27). Live Yahoo league data is never displayed publicly.
- **Demo chat**: live on demo data, strictly capped (a global daily question cap + per-visitor rate limits), within the G-08 budget.
- **Timing**: launches **with the dashboard (Phase 7)**.
- **Repo**: **public** (G-01 revised). This needs a pre-publication audit (SEC-001). It also makes GitHub branch protection/rulesets available for free, so S-21 moves to server-side protection.

---

## Part 8 — UI/UX (owner requirement: UI/UX options need approval; 2026-09-24)

| Item | Options | Selected |
|---|---|---|
| U1 Primary surface | ★Telegram-first · dashboard-first · equal | **Telegram-first, with a dedicated iOS app later** (owner). Implications: the backend stays API-first (REST + OpenAPI, S-26) so an iOS client can reuse it; app-level login must support mobile (Firebase Auth does); push later via APNs/FCM. The iOS approach is D-39 |
| U2 Dashboard home | ★Today: actions first · matchup scoreboard · analytics hub | **Today: actions first** |
| U3 Recommendation presentation | ★Action card + expandable why · ranked table · narrative | **Action card + why** |
| U4 Look & feel | ★shadcn/ui + Tailwind · Material UI · custom sports look | **shadcn/ui + Tailwind** |
| U5 Detail level | ★simple + drill-down · full detail · minimal | **Simple + drill-down** |
| U6 Telegram style | ★compact + buttons · detailed · digest only | **Compact + buttons** (e.g. [Open Yahoo] [Why?] [Alternatives]) |
| U7 Theme | ★follow phone · dark · light | **Follow phone setting** |
| U8 Design approval | ★clickable prototype · static mockups · trust standards | **Clickable prototype** (key screens with 2–3 variants, shareable page) before any real frontend work: task WEB-000 |

### D-39 iOS app approach (future; decided 2026-09-24)
**Selected**: **Native SwiftUI** (the owner's choice over the ★ React Native/Expo recommendation).

Implications:
1. The API contract (OpenAPI) must stay clean and versioned, so a Swift client can be generated (e.g. swift-openapi-generator).
2. **iOS builds need macOS + Xcode.** The owner's dev machine is Windows, so the options are cloud macOS builds (GitHub Actions macOS runners, Xcode Cloud) or a Mac.
3. The Apple Developer Program costs US$99/yr, which needs budget approval (G-08) when publishing.
4. Firebase Auth supports iOS sign-in, and push notifications come via APNs.
5. The web dashboard is not shared code with iOS; only the API and design language are shared.

A future gate is added.

### D-40 Cold-start projections for players with little NBA history (2026-09-24)
**Learn**: rookies, G League call-ups and international signings have little NBA data. Their stats from other leagues are informative but *inflated or deflated* by league strength. *Translation factors* convert them into NBA-equivalent rates. They are estimated from players who played in both leagues, which is also known as the "common-player" method.

**Selected**: **Translated priors + empirical Bayes.** Pre-NBA rates are translated to NBA-equivalent rates and combined with draft slot, age and position into an informative prior. Empirical-Bayes shrinkage [R-11, R-12] then moves weight to NBA data as minutes accrue. The literature for translation and rookie projection is reviewed in RSCH-003 before building.

### D-41 Pre-NBA leagues to collect (2026-09-24)
> **Priority (owner, 2026-09-24): low.** Moved to Phase 9. Until then, D-40 runs in a reduced form: draft slot/age/position priors + EB blending, without pre-NBA stats.

**Selected**: **G League** (nba_api), **NCAA college** (a permitted source to be chosen in DISC-010), and **EuroLeague / EuroCup** (public stats API). Other international leagues are deferred.

---

## Part 9 — Research paper (owner requirement, 2026-09-24)

| Item | Options | Selected |
|---|---|---|
| PAPER-1 Style | ★IEEE two-column · ACM sigconf · Sloan-style · Springer LNCS | **IEEE two-column, 6–7 pages** |
| PAPER-2 Authoring | ★LaTeX in repo + CI-built PDF · Markdown→PDF · Overleaf | **LaTeX in `paper/`, BibTeX from the literature review, PDF built by GitHub Actions** |
| PAPER-3 Contribution | ★system + evaluation · modelling study · agent-built-system case study | **System + evaluation** (point-in-time, format-aware decision support; leakage-free replay evaluation) |
| PAPER-4 Goal | ★arXiv preprint + portfolio · venue submission · portfolio only | **arXiv preprint + portfolio** (first-time arXiv submitters may need an endorsement; posting is an owner action) |

### D-42 Draft assistant (owner requirement, 2026-09-25)
**Selected**: **cheat sheet + live helper** (DRAFT-001…006).
- Draft in 2+ weeks (~9–19 Oct). The format (snake/auction/autodraft) is read from Yahoo settings (DISC-002).
- It runs **in parallel** with the M1 collection work, using git worktrees (owner accepted the higher Claude usage).
- Methods:
  - Marcel-weighted, EB-shrunk season projections [R-11–R-13]
  - G-score valuation with punt variants [R-01]
  - a team-aware live recommendation in the spirit of H-scoring [R-02]
  - a backtest vs the last-season baseline
- CV/paper value: the draft is a natural evaluation case for the paper's §VII.

### D-43 Yahoo data access after the API closure (2026-09-25)
**Context**: Yahoo's self-serve Fantasy API returns 403 for all existing apps since 2026-07-22 (docs/research/yahoo-api.md).
**Selected**:
- **Apply to Yahoo's approval-based developer programme** (YAHOO-001), and in parallel
- use an **assisted-import fallback**: the owner sends screenshots/pastes via Telegram or the dashboard; extraction plus owner confirmation lands them in raw (ADR-0025)

Rejected: a browser helper script (grey ToS area), server-side scraping (ToS/account risk), and waiting only for approval.

### D-44 Draft-day input and secret rotation (2026-09-25)
**Selected**:
- live-draft picks are entered by **quick pick entry** (autocomplete, ~2 s per pick)
- the exposed client secret is rotated **when new access arrives** (otherwise the old app is deleted)

### D-45 Keeping league data current without routine screenshots (2026-09-25)
**Owner requirement**: no routine screenshots.
**Selected: both**:

**1. Low-touch mode (default)**
- Rosters are seeded once after the draft (from the entered picks, or one paste).
- The owner's roster is synced by tapping [Done]/[Skipped] on Telegram suggestions, plus plain-English move messages ("added X, dropped Y").
- Opponent rosters are known from the draft and may drift. The bot asks an optional "has Team N made moves?" when a matchup is close.
- Free-agent suggestions say "if available" and come with ranked backups.
- Live matchup scores are computed from box scores.

**2. One-click laptop bookmarklet (optional extra)**
- It reads the Yahoo page the owner is viewing (Rosters/Transactions) and sends it to the system. If Yahoo's page security blocks a direct send, the fallback is copy → one paste.
- It only runs on the owner's tap, and only reads the visible page. Low ToS risk (equivalent to copy-paste).

**Rejected**: an automated logged-in browser. It's automated access against Yahoo's terms and risks the owner's account; Claude won't build detection evasion.
**If the API is approved**: switch to fully automatic behind the same Source interface.

### D-46 Reusable harness for other projects (2026-09-25)
**Owner requirement**: the standards, best practices and boilerplate must be reusable for other ML and personal projects.

**Selected**: a **Copier project template + a Claude Code plugin**.
- **Now**: keep generic assets separate from NBA-specific ones, listed in `harness-manifest.yaml`. Generic docs contain no project specifics.
- **After the draft**: extract them into
  1. a Copier template (new repos can pull template updates)
  2. a Claude Code plugin (skills, agents, hooks) installable into any repo

### D-47 Draft-slice data design answers (G-22 Q1–Q3, 2026-09-25)
- **Q1 positions**: both. Derive G/F/C from NBA positions automatically, and correct with a one-time Yahoo list paste if the owner provides one.
- **Q2 injuries**: a curated availability-overrides file (public source + date per entry), reviewed by the owner before the draft.
- **Q3 cloud**: Claude writes the Terraform and runs `plan` (a preview; nothing created), gives the owner a plain-English summary, and applies only after approval. Target: this week.

### D-48 Player profiles and narratives (2026-09-25)
**Owner requirement**: player profile pages like Yahoo's, with summaries, forecasts and analysis.

**Selected**: summaries are written by an **LLM grounded on our data**: Claude API tool use over vetted functions. Every number must come from a tool result (the same test as D-36). They're generated once daily per relevant player and cached.

**Profile sections (all four)**:
1. form + game log (rolling averages, trend, category strengths)
2. forecast (next game, week and rest of season, with ranges and expected games)
3. context and risks (schedule/B2B, injury history/status, role and minutes trend, teammates out)
4. fantasy verdict (value in the owner's league, team fit, buy/hold/drop)

### D-49 ML plan, draft slice (G-21, 2026-09-25)
Plan: docs/architecture/ml-methodology-plan.md Part 1. All recommendations selected:
- **Q1 projection**: Marcel baseline [R-13] + EB-shrunk candidate [R-11, R-12, R-75] with aging [R-70, R-71]; the backtest gate decides which ships.
- **Q2 valuation**: G-score [R-01], pool-size replacement [R-83], VOR→$ (practitioner, U1), punt variants [R-02].
- **Q3 live helper**: max bid + inflation + H-score-inspired fit (capped ±25 %, U2) + nomination hints [R-80, R-81].
- **Q4 backfill**: pull 2015-16…2022-23 game logs for Fold B and aging.

### D-50 Draft-slice season table: dbt first (2026-09-25)
**Question**: DRAFT-002 needs a player × season table. The design (G-22) puts it in dbt on BigQuery, but the dbt project didn't exist yet.
**Options**: (A) Polars loader now, port to dbt after the draft (fastest) · (B) build the dbt skeleton + staging/intermediate models first (matches the design; ~2–3 days).
**Selected (owner panel)**: **B, dbt first.** DATA-012 → DATA-013 (draft-slice subset) → `int_player_season` → DRAFT-002. DATA-012's dependencies on DATA-000/DATA-001 are dropped for this: the skeleton reads the DRAFT-001 raw snapshots directly.

### D-51 Draft projection method after the backtest (G-21b, 2026-09-25)
- **Finding**: the 3-year weighted minutes per game were the weak component. With the realised minutes, the EB rates rank far better than last season's (0.94 vs 0.91).
- **Selected (owner panels)**:
  1. Ship **H1** = C1 per-minute rates [R-11, R-12] x last season's minutes per game x Marcel games [R-13].
  2. The gate ranks on **season-total** 9-cat value (per game x games), not per game.
  3. The rank criterion is judged **pooled over all 8 rolling folds** (paired bootstrap stratified by fold [R-54]; rolling origin [R-50, R-51]) instead of the latest fold alone; the per-stat MAE criterion (>= 2/3 of stats) stays on the latest fold.
- **Why**: H1 beats B0 in 8/8 folds (pooled +0.013, 95 % CI +0.006 to +0.020) and on MAE for 11/11 stats in 2025-26. The latest fold alone had CI -0.004 to +0.032.
- **Follow-up**: a real minutes model (RSCH-002 literature gap) for Part 2.

### D-52 Test an age adjustment on top of H1 (owner, 2026-09-25)
**Owner request**: "we should test against age as well". The insights showed H1 doesn't discount old stars or credit young improvers.
**Candidate**: **H1+aging** = H1 with the per-stat age curve estimated from our data (delta method with harmonic-mean minute weights; aging shape [R-70], survivor-bias caveat [R-71]; U6).
**Rule, pre-registered before running**: H1+aging replaces H1 only if
1. its season-total value rank beats H1, pooled over all rolling folds, with the 95 % CI above 0, and
2. it is at least as accurate as H1 (MAE) on >= half of the 11 gate stats in the latest fold.

Otherwise H1 stays. Both results go in the backtest report whatever the outcome.
**Outcome (same day)**: H1+aging vs H1 pooled +0.002 (95 % CI +0.001 to +0.003), 8/8 folds; MAE as good or better on 10/11 → **H1+aging ships** (docs/evaluation/reports/DRAFT-002-backtest.md).

### D-53 Predict breakouts and hidden gems (owner, 2026-09-25)
**Owner requirement**: "the model should be able to predict breakouts as well or hidden gems". H1+aging answers "how good", not "who jumps": its minutes are last season's and shrinkage damps change.
**Selected (owner panels)**:
1. A **minutes-per-game model** from pre-season-knowable features: per-minute talent (EB rates), last and weighted minutes, age/experience, team change, and minutes vacated at the player's position. It replaces "last season's minutes" inside H1 only if it wins the rolling backtest.
2. A **breakout probability** per player (the chance their season value rank jumps sharply), shown on the cheat sheet, and scored on held-out seasons (e.g. precision of the top-k flags, calibration).
3. **Research first** (RSCH-006): verified literature on playing-time/role prediction and player improvement before the plan amendment (G-23) and any code.

### D-54 Minutes model + breakout probability design (G-23, 2026-09-26)
Plan: docs/architecture/ml-methodology-plan.md Part 1b (§7–§10a). Owner panels:
- **Minutes**: ridge and LightGBM both built. Selection on folds 2018-19…2021-22; the ship rule on 2022-23…2025-26.
- **Breakout** = +50 value ranks into the top 150.
- **Model**: logistic regression.
- **Flags**: shown only if pre-registered precision@20 and Brier criteria pass.

Refs: R-11, R-12, R-20, R-21, R-50, R-51, R-54, R-70, R-78, R-79, R-84, R-85, R-87, R-88, R-89, R-90, R-91.

### D-55 After the DRAFT-007 backtest: ship M1; M2 is "bounce-back"; pre-registered growth test (owner, 2026-09-26)
- **Finding**: M1 (ridge minutes) passed its rule. M2 passed too, but 22 of its 28 top-20 hits (holdout folds) were players returning from injury-shortened seasons (< 60 % of games), and it missed most genuine role breakouts.
- **Selected (owner panel)**:
  1. Ship **M1**, so the draft projections use M1 minutes.
  2. Show M2 only as **"bounce-back chance"**.
  3. Run a **second, pre-registered test** before any growth flags are shown:
     - **Population** (train and test): players who played >= 60 % of their team's games last season.
     - **Label**: the same breakout definition (>= 50 value ranks, finishing in the top 150).
     - **Model**: the same logistic regression, features, folds and bootstrap.
     - **Ship rule**: identical to §8 (pooled precision@20 minus the base rate, 95 % CI above 0, **and** a Brier score better than the base-rate forecast).
     - **Outcome**: if it passes, "growth breakout chance" flags appear on the cheat sheet; if not, they don't. Both results stay in the report either way.
- This rule was committed before the growth test was run.

### D-56 Breakout signals beyond box scores (owner, 2026-09-26)
**Why**: DRAFT-007 showed genuine role/skill breakouts aren't predictable from box-score history alone (M2b failed its pre-registered test).
**Selected (owner panels)**:
1. **Pre-season games first**: minutes and starts in October exhibition games (stats.nba.com, archived back to 2015, and complete before the 18 Oct draft). Fully backtestable, using the equivalent pre-draft games of past years.
2. **An LLM news/depth-chart reader next**: Claude extracts role statements from public news and depth charts. It's tested on the historical sample we can get (GDELT, Wayback Machine), then tracked live.
3. **Research first**: verified literature before any ingestion or model code (RSCH-007), then a plan amendment (gate G-24).
- Every new signal must pass the same pre-registered growth-breakout test (D-55 population and label) before any flag shows.

### D-57 Pre-season signal and news spike design (G-24, 2026-09-26)
Plan Part 1c (§12–§13). Owner panels:
- **Signals**: pre-season minutes + starts (role, not results [R-92, R-93]).
- **Cutoff**: games up to 2 days before each opening night.
- **Ship rules**: the same pre-registered rules as D-54/D-55 on the same holdout folds.
- **News**: a spike first, Claude API capped at US$5 [R-95, R-96, R-98].

## Summary of recommendations
D-01 A · D-02 A · D-03 A · D-04 A · D-05 A · D-06 A · D-07 A · D-09 A · D-12 A · D-13 A · D-14 A · D-15 A ·
D-16 A · D-17 A · D-18 A · D-19 A · D-20 A · D-22 A · D-24 A · D-25 A · D-27 A · D-28 A · D-29 A

D-08, D-10, D-11, D-21, D-23, D-26 and D-30 are answered through their S-xx items.

**⏰ The minimum set to answer this week** (to hit data collection by tip-off):
D-01, D-04, D-05, D-07, D-12, D-13, D-14 (+ G-01, G-03, G-12, G-15).

### D-58 Generalise the stack into a Claude-operated decision-intelligence factory (owner, 2026-09-27)
**Owner requirement**: make the pipeline → model → decision → frontend workflow reusable across domains (e.g. Sydney housing, banking/retail), built by Claude, with a continuous record of what works, as the basis for something commercially viable. Run it in parallel with the NBA work.
**Plan**: `docs/platform/generalisation-plan.md`. Three layers (harness / platform kernel / domain pack), a lessons ledger (`docs/platform/lessons.md`) plus a playbook, and a second-domain proof.

**Learn**: a *kernel* is the code every product needs regardless of subject (history-keeping ingestion, point-in-time reads, backtests with pre-registered gates, decision/explanation contracts, infra). A *domain pack* is what changes per subject (sources, targets, objective, screens). Keeping them apart, and enforcing it with import rules, is what makes the second product cheap.

**Options** (★ = recommended):
1. **Where the kernel lives**
   - ★ (a) Packages in this repo first; extract to a template + plugin after the proof. Pros: no churn during the season; one CI. Cons: the repo mixes concerns for a while.
   - (b) A separate platform repo now. Pros: a clean boundary. Cons: two repos to keep in sync, before we know what's truly generic.
   - (c) A template only, no shared code. Pros: simplest. Cons: fixes don't flow between products.
2. **Proof domain**
   - ★ (a) Sydney housing: public NSW Valuer General sales, clear decisions, local market.
   - (b) Banking/retail: realistic data is private (synthetic only).
   - (c) Another sports league: easy, but proves little.
3. **Timing**
   - ★ (a) G0 now (ledger, manifest layers), G1 extraction after the draft.
   - (b) Everything after the season.
   - (c) Start the extraction now (risks the draft).

**CV value**: "Designed a reusable ML decision platform (medallion ingestion, point-in-time backtesting, pre-registered model gates) and proved it on a second domain" is a strong DE/DS/ML-platform line. (a)/(a)/(a) produce that evidence soonest without risking the draft.
**Selected (owner, 2026-09-27)**: 1(a) kernel packages in this repo first; 2(a) Sydney housing as the proof domain; 3(c) **start the extraction now**, not after the draft. The frontend (WEB-001+) continues alongside it, and draft-week tasks (16-18 Oct) take priority if they clash.

### D-59 Website hosting and audience (owner, 2026-09-27)
**Question**: how the website is served so people can use it (the SPA from WEB-001).
**Learn**: the SPA builds to static files (~0.5 MB). Hosting = those files on a CDN, plus routing `/api` to the Cloud Run API. Typical choices: Vercel/Netlify/Cloudflare Pages (startups), Firebase Hosting (GCP web apps), bucket + load balancer + CDN (enterprise), containers only for server-side rendering.
**Options**: Firebase Hosting · Cloud Run container · Cloud Storage + Cloud CDN (~US$18/mo LB) · Cloudflare Pages/Vercel (second provider).
**Selected**:
1. **Firebase Hosting** in each GCP env project (dev, prod): free tier, global CDN, same project as the Firebase sign-in (D-27), a preview channel per PR, `/api/**` rewritten to the Cloud Run API. Managed by Terraform; deployed by CI through WIF (merge → dev; CalVer tag → prod).
2. **Audience**: the public demo on sample/anonymised data for anyone, plus the real app for the owner and invited users behind Google sign-in and an allowlist (D-38/D-27 unchanged). Open sign-ups for other people's leagues are out of scope; if wanted later, a separate epic (it needs Yahoo API access or other platforms, accounts and privacy terms).
3. **Domain**: none; use the free `<project>.web.app` address.
This supersedes technology-evaluation.md §10 for the website.

### D-60 Kernel package structure and name (decided 2026-09-28; the owner delegated the choice to Claude)
**Question**: how the platform kernel (the 109 platform files + the platform halves of the 13 mixed files in
`platform-manifest.yaml`) is packaged when it is extracted, and what it is called.

**Learn**: a package is the unit other projects install. One package is easiest to reuse and version; several
packages let a project take only what it needs, at the cost of more packaging and version juggling. Inside
one package, import-linter can still enforce the layers (store → time → eval/methods → decide).

**Options** (★ = recommended):
1. **Structure**
   - ★ (a) **One platform package** with subpackages: `store` (snapshots, paced client), `time` (clock, as-of),
     `evaluate` (rolling origin, paired/clustered bootstrap, gates, calibration), `methods` (EB shrinkage,
     aging, ridge, logistic), `decide` (win probabilities, evidence rendering), plus the web UI kit in
     `apps/web/src/components/ui`. Pros: one dependency for the template (GEN-004); simplest. Cons: a project
     takes all of it.
   - (b) **Several packages** (`<name>-store`, `<name>-evaluate`, …). Pros: pick-and-choose. Cons: more
     pyproject files, versions and CI for a one-person, one-Claude setup.
   - (c) **Leave the code in the fantasy packages**, marked generic. Pros: no moves. Cons: every new domain
     imports `fantasy_*` names; the proof (GEN-005) can't claim a clean kernel.
2. **Name** (the import name; the repo stays as is): ★ `dikit` ("decision-intelligence kit") /
   `evidencekit` / your own.

**CV value**: (a) gives a clean "built a reusable decision-intelligence kit, reused for a second domain" story.
**Selected** (Claude, on the owner's delegation, 2026-09-28): 1(a) **one platform package**, 2 name **`dikit`**, at `packages/dikit` with subpackages store, time, evaluate, methods, decide. GEN-003 can start.

### D-61 In-season methodology approved (G-19, owner, 2026-09-28)
The owner approved Part 2 of `ml-methodology-plan.md` with every recommended answer (§24):
1. **Order**: distributions (DEC-002) + matchup simulation (DEC-003/004) first, then the lineup optimiser and the in-season projection update.
2. **Holdout**: the second half of 2025-26, pre-registered and untouched until each ship test.
3. **Add/drop horizon**: this week + a discounted next week (the discount is U13, tested for sensitivity).
4. **Model ceiling this season**: statistical models only (EB, logistic, negative binomial, MILP); no gradient boosting.

### D-62 What the API reads until the warehouse serves recommendations (decided 2026-09-28; the owner delegated "do what you think is best")
**Question**: the backend standard says the API reads BigQuery, but the daily chain writes its outputs (week
projection, brief) as files under the data root, and no recommendation reaches BigQuery yet. What does the first
API read?

**Learn**: a "serving layer" is whatever the web API reads. It can be warehouse tables (flexible queries, needs the
pipeline to load them) or files the pipeline publishes (simple, one read per request, no query cost).

**Options**: (a) ★ the pipeline publishes a structured JSON per day next to the markdown brief; the API reads the
latest one read-only from the data root (local path now, `gs://` on Cloud Run via the same fsspec store);
(b) load the brief outputs into BigQuery first (a new mart + load job), then build the API on it; (c) the API
recomputes the brief on request from the parquet files.
**Pros/cons**: (a) is fastest and keeps "all writes in pipeline jobs"; it serves only what the brief computed.
(b) matches the standard but adds a load job and dbt model before any page works. (c) duplicates pipeline work
in the request path and needs the inputs on the API host.
**Cost**: (a) none; (b) BigQuery storage/queries within the free tier; (c) none, but slower responses.
**CV value**: (b) is the more "data platform" story; (a) is a standard publish-then-serve pattern. (a) now does
not block (b) later: the JSON contract is the API's schema either way.
**Selected** (Claude, on the owner's delegation): **(a)**. APP-001 no longer depends on DATA-023 (the DQ
framework, behind gate G-20): freshness comes from the pipeline run log and each published file's `as_of` until
DQ results exist. The standard's BigQuery read path returns when recommendations are logged there (EVAL-005).

### D-63 Where the daily chain runs, given the NBA blocks cloud IPs (decided 2026-10-02; owner delegated)
**Evidence** (INFRA-006 spike, 2026-10-02): a temporary Cloud Run job built from our image probed each source.
From both australia-southeast1 and us-central1: cdn.nba.com (schedule, box scores) **HTTP 403**; stats.nba.com
(game logs) **timed out**; the official injury-report PDFs **200**; api.telegram.org **200**. The NBA hosts block
Google Cloud's addresses, as D-28 feared. (The probe jobs were deleted.)

**Learn**: some websites refuse traffic from data-centre IP ranges to stop scraping. A home connection (a
"residential" IP) is accepted. So the step that talks to those hosts has to run from a home machine, or the data
has to come from somewhere else.

**Options**: (a) ★ **hybrid**: the owner's PC runs only the NBA fetch at 07:30 and writes the raw snapshots straight
to the GCS raw bucket; a Cloud Run job on Cloud Scheduler runs everything else (injury report, projections, brief,
publish, Telegram) from GCS. If the PC is off, the cloud job still sends the brief on the last data, marked stale.
(b) all on the PC (today): the PC must be on for anything to happen. (c) all in the cloud through a residential
proxy service: paid, and against the spirit of the hosts' blocking. (d) another data source (e.g. a paid stats API):
cost and new parsers.
**Pros/cons**: (a) keeps every parser, makes the brief resilient to a sleeping PC, and moves secrets and schedules
to the cloud; the PC still matters for fresh stats. (b) no work, no resilience. (c) costs money and is a ToS grey
area. (d) cost and weeks of work.
**Cost**: (a) within the free tiers (one daily job, a scheduler trigger); (c) and (d) monthly fees.
**CV value**: (a) is a realistic edge + cloud ingestion pattern with graceful degradation.
**Selected** (Claude, on the owner's delegation "you don't need my approval"): **(a)**. Slices: INFRA-006 (1) a
workspace root for every pipeline file (local or gs://), (2) the fetch / cloud job split with a staleness note,
(3) Terraform: the Cloud Run job, Cloud Scheduler, secrets as env, and the owner's switch of DATA_ROOT/WORK_ROOT.

### D-64 Users, profiles and settings: store, roles, first slice (decided 2026-10-02 by the owner; gate G-25)
**Context**: the owner asked for "capability for different users, managing profile, settings etc." D-31 already set
the direction (small multi-user ready: data keyed by league and user, per-user Yahoo OAuth, several allowlisted
emails, per-user notification settings, an LLM cap). Today the app has one hard-coded identity: an
`ALLOWED_EMAILS` env var on Cloud Run, settings in `.env`, and a read-only API (D-62). Three choices remain.

**Learn**: *authentication* proves who you are (Google sign-in, done in WEB-013/APP-005); *authorization* decides
what you may do (roles). A *profile/settings store* is a small transactional database (OLTP): many tiny reads and
writes by key. That differs from the warehouse (BigQuery, OLAP: big scans, cheap storage, slow small writes) and
from the published files the API reads today. Keying users by the sign-in provider's stable **uid**, not their email,
survives an email change. *Optimistic concurrency* (an `updatedAt`/ETag the client sends back) stops two tabs
silently overwriting each other.

**Q1 Where users, invites and settings live**
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ (a) Firestore (Native mode), written only by the API (Admin SDK; client rules deny all) | Serverless, already in this Firebase project, per-document transactions, queries for invites, emulator for tests | A new datastore to learn and back up; vendor-specific API | Free tier (50k reads / 20k writes a day); ~US$0 at our size |
| (b) JSON documents in the serve bucket with generation-match writes | No new service; matches D-62's file pattern; conditional writes give concurrency safety | Hand-rolled indexing (invites by email), no transactions across documents | ~US$0 |
| (c) Cloud SQL Postgres (smallest) | Relational, SQL, migrations; strongest CV keyword | ~US$9–10/month at minimum (at the G-08 ceiling), always-on instance to patch | ~US$10/mo |
| (d) BigQuery tables | Already used | Wrong tool: slow, quota-limited small writes; no transactions | ~US$0 |

**Q2 How people get access**
| Option | Pros | Cons |
|---|---|---|
| ★ (a) Invites + roles in the store: the owner invites an email from the app; roles `owner` / `member`; the env allowlist only bootstraps the first owner | No redeploy to add someone; removal takes effect on the next request; auditable | Needs an owner admin screen (WEB-015) |
| (b) Keep the env allowlist; settings per email | Smallest change | Every new user is a Terraform change + deploy; no roles |
| (c) Open sign-up | Zero friction | Against D-31 (small, invited) and privacy (live league data) |

**Q3 First slice**
| Option | Pros | Cons |
|---|---|---|
| ★ (a) Identity + profile + settings now (built user-keyed); a second user's own league later, behind Yahoo's per-user OAuth and a league-keyed pipeline (DATA-032) | Delivers the profile/settings UX before the draft; no throwaway work; the pipeline split is its own decision | A member sees only demo data until DATA-032 |
| (b) Everything at once (users + per-user Yahoo + per-league pipelines) | Full multi-user in one go | Weeks of work across the pipeline right before the draft; high risk |
| (c) Settings for the owner only, no user model | Fastest | Rework when the second user arrives; contradicts D-31 |

**Settings in scope** (APP-009/WEB-014): display name (from Google, editable), time zone (IANA, default
Australia/Sydney), daily brief on/off and its awake window, Telegram linking (a one-time code sent to the bot, never
typing a chat ID), alert types (brief, injury, waiver), default draft strategy (all / a punt), theme
(system/light/dark), and account actions: export my data, delete my account (removes the profile, settings and
invites they made; the owner account can't delete itself while it's the last owner).

**API change**: the API gains its first writes (`PATCH /me/settings`, `POST /invites`, `DELETE /members/{uid}`).
D-62 ("all writes in pipeline jobs") stays true for *data products*; user state is a separate artefact type.
Bearer tokens in a header (no cookies) keep CSRF out of scope; CORS adds PATCH/POST/DELETE for the site's origins.

**CV value**: (Q1a) Firestore + (Q2a) RBAC with invites is a recognisable "multi-user SaaS foundation" story;
(Q1c) Postgres reads stronger on DE CVs but costs money now and can follow if the product grows.
**Recommendation**: ★ Q1(a), Q2(a), Q3(a). Tasks: APP-008, APP-009, WEB-014, WEB-015 (gated G-25), DATA-032 (placeholder).

**Selected by the owner (2026-10-02)**: **Q1 (a) Firestore + a BigQuery copy**, Q2 (a) invites + owner/member roles,
Q3 (a) identity + profile + settings first. The owner first chose BigQuery, then picked Firestore for latency
(~5–30 ms reads vs ~0.5–2 s) once the trade-off was laid out. The "Stream Firestore to BigQuery" Firebase extension
(free, Google-maintained) mirrors the users/invites/settings collections into an `app_raw` dataset as change logs,
so user data can be analysed in SQL next to everything else (e.g. EVAL usage joins) without the app paying
BigQuery latency. The copy is read-only analytics: the API never reads it.
### D-65 Missed games are worth replacement level, not zero (G-26, owner, 2026-10-02)
**Trigger**: the owner saw Giannis Antetokounmpo at #118 ($10). The season-total value (D-51) multiplies per-game
value by expected games and scores missed games as zero; his forecast (45 games, 27.8 min) leans on one injury year
(36 games in 2025-26 against 63–73 before), so one injury season wipes out his value.
**Options**: (A ★) fill missed games with a replacement-level line [R-83], judged on a draft replay that also lets
teams replace injured players · (B) smooth games and minutes over three seasons · (C) both · (D) keep, adjust by hand.
**Selected (owner)**: **A**. Pre-registered in DRAFT-011 (replacement line, fill rate 1.0, IL replay, ship rule).

### D-66 How monitoring alerts reach the owner (decided 2026-10-03 by the owner: A; gate G-27)
**Context**: the cloud job alerts on in-run step failures, but not on a run that never starts, stale NBA data from the
PC, site/API downtime, or spend. INFRA-005 holds the user stories.
**Learn**: *monitoring* watches signals (did the job run, is the site up); *alerting* decides who hears and when.
Alerting on "something didn't happen" (absence) is the hard part: something must be running to notice.
**Options**: (A ★) a small watchdog job on its own schedule, reusing the bot secret and tested Python · (B) Cloud
Monitoring policies + uptime checks with a Telegram webhook channel · (C) A for job/data checks + Cloud Monitoring
uptime checks to email.
**Pros/cons**: A: one tested code path, free, but blind to a Cloud Scheduler outage. B: Google-native and sees
platform failures, but puts the bot token in channel config/state and the logic in MQL. C: covers both blind spots
at the cost of two mechanisms.
**Cost**: all ~US$0 at this size; the budget alert itself is free (needs the billing account).
**CV value**: B/C show Cloud Monitoring/SRE practice; A shows pragmatic observability in code.
**Recommendation**: ★ A now (fast, testable, no secret sprawl), adding B's uptime checks later if A's blind spot matters.

### D-67 Draft simulator: where it lives, how opponents bid, pace (decided 2026-10-03 by the owner: A, A, A; gate G-28)
**Context**: the owner wants to practise the 18 Oct auction (DRAFT-013/014/015). The engine exists (`draft_live` advice,
`draft_mock` random room); the open choices are the surface, the opponent model and the pace.
**Learn**: an auction simulator is only useful if the simulated room prices players like a real room. Too cheap and
you learn to wait for bargains that never come; too dear and you learn to panic. So the opponent model is
*calibrated*: its average prices are checked against a reference (our published $, or Yahoo's market prices).
**Q1 Surface**: (A ★) a "Draft practice" page in the web app (Courtside design, phone + desktop, uses the board's
advice engine) · (B) a practice mode inside the HTML auction board used on draft night.
A: polished, reuses the React table/panel work, testable with personas; the practice UI differs from the board you
use on the night unless the board moves into the app later. B: practise on exactly the draft-night tool; plain
HTML/JS, harder to test and to make look modern. **CV value**: A (product/front-end); B (none extra).
**Q2 Opponents**: (A ★) rule-based "styles" (balanced, stars-and-scrubs, punter, value hunter) bidding up to
published $ × inflation × need × noise, calibrated so top-50 prices land within ±15 % of the $ values ·
(B) the same, calibrated to Yahoo market prices (needs DATA-034's Yahoo login) · (C) agent-based with learned
tendencies (needs a history of this league's auction bids, which we don't have).
A: works today, honest about its assumptions. B: closer to how this room actually prices, blocked on a login. C:
most realistic, not possible before the draft. **CV value**: C > B > A (simulation/agent modelling).
**Q3 Pace**: (A ★) real timers (30 s nominate / 20 s bid, reset on each bid) plus "sim to my next nomination" and
"sim the rest" · (B) untimed, turn by turn. A rehearses the time pressure of the night; B is easier to think in.
**Cost**: US$0 (client-side; the report reuses the existing weekly simulation).
**Recommendation**: ★ Q1 A, Q2 A (switch the base to B when a Yahoo login lands), Q3 A. Time: about 3–4 days of
work; a first playable version (room + bidding, no report) in ~2 days so practice starts by ~Thu 8 Oct.

### D-68 Telegram linking and how the daily job reads user settings (decided 2026-10-03 by the owner: A, A; gate G-30)
**Context**: APP-009 lets each user link Telegram with a one-time code and set their alert preferences. Two pieces
aren't decided: how the bot's `/start <code>` message reaches the API, and how the daily job (a pipeline app)
reads each user's settings, which live in the API's users store (Firestore).
**Learn**: Telegram bots receive messages either by **webhook** (Telegram POSTs each update to a public URL you
register, signed with a secret header) or by **polling** (`getUpdates`; a bot can't do both at once). Separately,
**layering**: apps may import packages but not each other, so the pipeline can't import the API's users code.
**Q1 How `/start <code>` reaches the API**
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ (a) Webhook: `POST /telegram/webhook` on the API, verified by Telegram's secret-token header; `setWebhook` once | Instant linking; the standard production pattern; no polling | A new public endpoint (secret header + rate limit); the daily job's `getUpdates` setup step stops working once the webhook is set (the chat id is already stored) | US$0 |
| (b) On demand: after showing the code, the page's "I've sent it" button makes the API call `getUpdates` and look for the code | No public endpoint | The user must press a button; polling and a future webhook can't coexist | US$0 |
**Q2 How the daily job reads settings**
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ (a) Move the users store port + Firestore adapter into a package (`packages/core` or a new `packages/users`); API and pipeline both use it | One implementation, typed, tested once; follows the layering rule | A refactor of APP-008's code (moves, no behaviour change) | US$0 |
| (b) The pipeline calls an internal API route with a service token | No code moves | A second auth path to secure; the job depends on the API being up | US$0 |
| (c) Read the BigQuery mirror (Firestore → BigQuery extension) | Fits the warehouse pattern | Needs the extension installed (your step); minutes of lag | ~US$0 |
**CV value**: Q1(a) shows a production webhook with signature verification; Q2(a) shows clean hexagonal layering.
**Recommendation**: ★ Q1 (a) and Q2 (a). Q2(c) stays useful for analytics, not for sending alerts.
### D-69 Season replay: data delivery, lineups, rivals, waivers, seasons (decided 2026-10-04 by the owner: all A; gate G-31)
**Context**: the owner wants to draft on a past season, then play that season's weekly H2H matchups against the
drafted rivals, with daily lineups and up to 4 pickups a week (the league's limit), scored on real box scores
(SIM-001…004). The game logs with dates already exist (2015-16 → 2025-26).
**Learn**: a *replay* uses the real outcomes, so it tests decisions (lineups, pickups) rather than predictions. It
must hide the future: the draft uses values as they were before that season; within a week, advice may only use
games already played.
**Q1 Data delivery**: (A ★) the pipeline publishes compact per-season files (values, daily lines, weeks); the API
serves them; the browser simulates (instant, works offline once loaded) · (B) the API simulates each week on request
(less data in the browser, but every move waits on the server).
**Q2 Lineups**: (A ★) daily, like the league ("Weekly Deadline: Daily"), with auto-start as the default and manual
changes · (B) one lineup for the whole week (simpler, less like the real game).
**Q3 Rivals**: (A ★) rivals auto-start their best players each day and make no pickups (simple, stated on screen)
· (B) rivals also stream up to 4 a week by a greedy rule (harder weeks, more to tune).
**Q4 Waivers**: (A ★) a pickup plays from the next day (free agents; the league's 2-day waiver period is skipped
in practice) · (B) model the 2-day waiver period.
**Q5 Seasons**: (A ★) the last three (2023-24, 2024-25, 2025-26) · (B) all since 2016-17.
**Cost**: US$0 (static files, ~1 MB per season compressed).
**CV value**: a replay simulator over real event data (Q1 A) is a strong product + data story.
**Recommendation**: ★ A for all five; Q3 B and Q4 B can follow if practice feels too easy.

### D-70 Where league-specific values are computed (decided 2026-10-04 by the owner: B; gate G-33)
**Context**: the board's dollar values and z-scores are computed for one league (9-cat, 16 teams, $200, 14 spots) and
published as a file. Draft settings (DRAFT-017) let the owner change team count, budget, roster size, categories and
scoring format (points, roto, categories), which changes every value. Python already has the tested computation
(`value_all` with `LeagueRules`, five formats, ADR-0018).
**Learn**: auction value = the player's z-score impact above a replacement level, scaled so the values of the drafted pool
add up to the money in the league. Change the league and the replacement level, the scale and possibly the stats all change.
**Q1 Location**: (A) port the valuation to TypeScript and compute in the browser (instant, offline, but a second
implementation that can drift, and extra tests) · (B ★) the API computes on demand from published projection
distributions, with an in-process and shared cache and single-flight (one implementation, ~100s of ms on a cache miss,
cost near zero) · (C) the pipeline precomputes a fixed set of presets daily (cheapest and fastest, but only those shapes).
**Cost**: A none · B none to a few cents (CPU on Cloud Run) · C none (storage).
**CV value**: B shows a clean service boundary with caching and concurrency control; A shows more front-end depth but duplicates logic.
**Recommendation**: ★ B; keep the published default board as the fallback and the source for the default league.

### D-71 Scale targets and spend (decided 2026-10-04 by the owner: all A; gate G-33)
**Context**: the owner wants many users to use the site at once eventually. Nothing is measured yet (PERF-001).
**Q1 Cold starts**: (A ★) scale to zero for now (cold start of a few seconds on the first request after idle; no cost) ·
(B) one minimum instance on the API (about US$5-15 per month depending on CPU allocation; removes the cold start; above the G-08 ceiling together
with other costs, so it needs your explicit yes).
**Q2 Load-test and web-perf tooling** (including a non-blocking CI job for each; CI changes are Tier B): (A ★) a small asyncio + httpx
script in `tools/` for the API plus Lighthouse CI for the web (free; Lighthouse is the one new dev tool) ·
(B) k6 (industry standard, a new tool to install and learn; good CV value) · (C) Locust (Python, a web UI, extra dependency).
**Q3 Targets** (to be replaced by measured baseline plus margin): (A ★) 25 concurrent users, p95 ≤ 300 ms on published reads
and ≤ 500 ms on `/me/*`, error rate < 0.5 %, web LCP ≤ 2.5 s on a throttled phone · (B) 100 concurrent users (probably needs
min instances and costs more) · (C) only measure and report, no target.
**Learn**: p95 = the latency 95 % of requests beat. A load test ramps virtual users and records p50/p95/p99 and errors;
"scalable" is a claim about those numbers at a stated concurrency.
**Cost**: A/A/A is US$0.
**Recommendation**: ★ A, A, A now; revisit B/Q1 when the first friends join.

### D-72 Accounts and leagues: who may register, sign-in methods, pictures, scope, phone navigation (APPROVED by the owner 2026-10-04, all recommendations; gate G-34)
**Context**: the owner asked (2026-10-04) for user-created leagues with invite URLs, commissioners and co-commissioners,
private and public leagues with a discovery panel, league and team names, usernames and pictures, and a proper sign-up.
D-64 chose an invite-only model (Q2 (c) "open sign-up" was rejected for privacy and scale) and APP-005/APP-008 return
`403 not-invited` to any account that is not on the list. A public leagues panel needs strangers to be able to register,
so this reverses that part of D-64 and needs your explicit decision. The full design is
`docs/specification/leagues-and-accounts.md`.

**Learn**: *Two levels of roles* (RBAC): a platform role says what you can do across the product (`owner`, `member`);
a resource-scoped role says what you can do inside one league (`commissioner`, `co_commissioner`, `manager`). They are
kept apart so becoming a commissioner never widens access to anything else. A *capability URL* is a link whose
unguessable token is the permission (here: 128 random bits, stored only as a hash, expiring, revocable); anyone holding
it can use it, so it is treated like a password. *Defence in depth for open sign-up*: the privacy of the live Yahoo
data does not depend on who may register, because new accounts get the `member` role, which never reads it.

**Q1 Who may register**
| Option | Pros | Cons |
|---|---|---|
| ★ (a) Open registration behind an `OPEN_SIGNUP` flag (default off), email verified, new accounts are `member` (demo data and leagues only); the flag is turned on only after the SEC-002 review | Needed for a public panel; private data unaffected; reversible by the flag | Abuse and spam become possible: needs the caps, reports and the review; more support surface |
| (b) Link-only registration: an account can be created only from a valid owner invite or league invite link | Nobody unknown can join; very low abuse | A stranger cannot find a public league without a link, which defeats the public panel |
| (c) Keep invite-only for now; build leagues for invited users only | No new risk | The public panel has nobody to see; the owner's request is only half met |

**Q2 Sign-in methods**
| Option | Pros | Cons |
|---|---|---|
| ★ (a) Google plus email and password (verified email required, Firebase password reset) | Anyone can join, the usual "proper sign-up" | Password reset and verification screens, weak-password and credential-stuffing risk (Firebase throttles) |
| (b) Google only | Smallest surface; every account is already verified | People without a Google account cannot join |

**Q3 Pictures**
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ (a) Uploads: the API decodes, crops, re-encodes to a 256 px WebP and strips metadata; stored in one public-read bucket of server-produced files under random ids and served from `storage.googleapis.com` (a separate origin, no load balancer, so no fixed cost); reports hide a picture; initials and 12 preset icons as the default | What was asked for; the re-encode removes most upload attacks | Moderation exists (report, hide, the owner removes); a Pillow dependency | Cents per month |
| (b) Presets and initials only | No upload risk, no moderation | Not what "profile pictures" means | none |
| (c) Show the Google photo only | No storage | No team pictures; email/password users have none; leaks the Google photo | none |

**Q4 What a league does in this slice**
| Option | Pros | Cons |
|---|---|---|
| ★ (a) Shell: membership, roles, invites, discovery, settings that drive the league's practice drafts and valuations (D-70). Live drafts and in-app seasons come later | Delivers everything in the request without the weeks a live draft room and a scoring engine need; nothing built twice | A league is a group with rules, not yet a season you play |
| (b) (a) plus a live multi-user auction draft room now | A visible product moment | Websockets or polling, a state machine for bids, timers and reconnection: its own spec and review; competes with the 18 Oct draft |
| (c) League as a wrapper around a Yahoo league only (DATA-032) | Reuses real data | Needs each member's Yahoo OAuth; gated; nothing native |

**Q5 Phone navigation** (the tab bar already holds six tabs, and WEB-029's e2e proves they fit at 320 px)
| Option | Pros | Cons |
|---|---|---|
| ★ (a) No seventh tab: Leagues is reached from the avatar menu and a Leagues card on the Practice hub (desktop sidebar gets a full item) | Keeps the proven layout; two taps | Less prominent on phone |
| (b) Seven tabs | One tap | Fails the 320 px fit test; tiny targets |
| (c) Rename the Practice tab "Play" and put Practice and Leagues under it | One tap, room to grow | Renames a tab that just shipped |

**Defaults taken in the spec that you can overturn at G-34**: co-commissioners can change settings but not appoint, transfer
or delete; the default team name is `<username> <Keyword>`; league names are unique only among public leagues; a user
may create 5 leagues; signed-out visitors can open only an invite preview.

**CV value**: two-level RBAC, capability URLs, an image-processing pipeline and abuse controls make a credible
"multi-tenant SaaS foundation" story; (Q4b) a real-time draft room would add websockets/concurrency depth but later.
**Cost**: ★ choices add about US$0 a month (Firestore and Auth free tiers; storage cents). Terraform changes (buckets,
IAM, TTL, indexes: INFRA-010) are Tier B.
**Recommendation**: ★ Q1(a), Q2(a), Q3(a), Q4(a), Q5(a). Tasks: APP-012..017, WEB-030..035, SEC-002.

### D-73 Product name: Courtside, and what the rename does not touch (name APPROVED by the owner, 2026-10-04; only the repository rename BRAND-002 waits on G-35)
**Context**: the owner pivoted the product from a personal "NBA Fantasy Assistant" to an actual fantasy app and simulator
for many users, and named it **Courtside** (2026-10-04). Old name references describe the old concept and must go.

**Decision**: the user-facing name, documentation and public wording change to Courtside (BRAND-001). **Identifiers do not
change**: the Python packages (`fantasy_*`), GCP project ids and resource names (`nbafa-*`), Terraform state and bucket
names, BigQuery datasets and the workload-identity trust. Renaming those would destroy and recreate infrastructure for no
user benefit. The docs, harness and app renames (BRAND-001, BRAND-003) are not gated. The GitHub repository rename is a separate owner action (BRAND-002, gate G-35); CI trusts the repository id,
so it survives the rename. A test (`tools/tests/test_brand.py`) fails if the old name appears outside an explicit allow-list
of historical references (ADR history, git-tracked evidence), so the rename cannot silently regress.

**Risk to know (owner decision needed before launch, not before building)**: the Yahoo developer application states
"personal, non-commercial" use. A public product must keep live Yahoo data owner-only (already true: new accounts are
`member`, D-72/D-64) and must not redistribute Yahoo or NBA data in ways their terms forbid. DISC-007 recorded the Yahoo
terms; a public launch needs that re-read for the new purpose and the NBA data licensing reviewed. Recorded as an open item
in G-35, not decided here.

**CV value**: a clear product story ("a multi-user fantasy platform with a simulator") reads better than "a personal tool".
**Cost**: none.

### D-74 Sign-in methods and the user-data and authentication ruleset (APPROVED by the owner 2026-10-04 with Q5 = 16+; gate G-35; supersedes D-72 Q2)
**Context**: the owner asked (2026-10-04) for best-practice privacy and a ruleset for authentication and data handling,
with sign-up by Google, email, phone and others, with verification codes where they apply. The research is
`docs/research/user-data-privacy-and-auth.md` (47 verified sources, 40 candidate rules, four unverified facts that the
RSCH-010 spike settles). The ruleset is the standard `docs/standards/user-data-and-auth.md` (rule ids UDR-xx).
Approving this decision approves the standard.

**Learn**: *Authentication* proves who you are (Firebase Auth does it); *authorisation* decides what you may do (the API
does, with `can()`). A *verified* identity means the provider confirmed the email or phone. *SMS codes* are the weakest
second factor (SIM swapping) and cost money per message, and attackers abuse them (SMS pumping) so they need a country
allow-list and caps. *Data minimisation*: collect only what a feature needs and delete it on a schedule. *Account linking*
joins several sign-in methods to one account, which is a takeover risk if an unverified email is trusted.

**Q1 Methods at launch**
| Option | Pros | Cons | Cost |
|---|---|---|---|
| ★ (a) Google + email/password (15+ characters, verified email) | Covers most people; verification mail is within the free quota; no SMS risk | Password breach screening cannot be enforced by the server with Firebase, so it is advisory on the client; passwords add reset and support work | US$0 |
| (b) (a) + passwordless email link | No password to leak | Email-link volume above 5 a day needs a billing account | billing account (needed before 25 Dec anyway) |
| (c) (b) + phone SMS code | What the owner asked for; easy for phone users | Per-SMS cost, SMS-pumping fraud, SIM swap, phone numbers are personal data, needs Identity Platform and a billing account | about US$0.01 per US SMS; bounded by the region allow-list, provider throttles, a budget alert and the `AUTH_METHODS` switch (the API itself cannot cap SMS: the client SDK sends them) |
| (d) + Sign in with Apple | Needed if an iOS app offers Google sign-in | Paid Apple developer account | Apple fee |

**Q2 Phone numbers**: ★ (a) off at launch, built and tested behind `AUTH_METHODS` so enabling is configuration, US + AU
region allow-list, provider throttles, a usage alert on a daily budget, reCAPTCHA defence in audit then enforce first; (b) on at launch; (c) never.
**Q3 Identity Platform upgrade**: ★ (a) upgrade in dev only when INFRA-009 starts (needed for blocking functions, MFA
and password policy; free for the first 50,000 monthly users, but it needs a billing account); (b) stay on plain Firebase Auth.
**Q4 Where tokens live in the browser**: ★ (a) Firebase SDK default persistence with a strict CSP and an ADR (UDR-12);
(b) server session cookie (`__session`), stronger against XSS theft, needs CSRF work. Revisit after RSCH-010 SPK-3.
**Q5 Minimum age**: (a) 13+ globally, confirmed by a checkbox, no birthdate stored; ★ (b) 16+ in all launch markets (US and
Australia), confirmed by a checkbox (owner direction 2026-10-04, D-75); (c) block the EU at launch. This is a legal
question (SEC-003 records the owner's choice).

**CV value**: documented threat model, standards-mapped rules (NIST 800-63B, OWASP ASVS 5.0) and a compliance matrix are
strong security-engineering evidence.
**Cost**: ★ choices US$0 now; (c) and Q3 need a billing account and per-SMS spend, which are the owner's to approve.
**Recommendation**: ★ Q1(a), Q2(a), Q3(a), Q4(a), Q5(b). The ruleset itself is the new standard
`docs/standards/user-data-and-auth.md`, approved through S-40. Tasks: RSCH-010, INFRA-009, INFRA-010, APP-018, APP-019,
APP-020, APP-024, APP-025, APP-026, APP-027, WEB-030, WEB-036, WEB-037, SEC-002, SEC-003.

### D-75 Standalone product: no Yahoo, free to play, no paid licences yet, US and Australia, 16+ (owner direction 2026-10-04; confirm in G-35)
**Context**: the owner said Courtside is its own fantasy app and simulator, so Yahoo is no longer a dependency; it will be
free to play with ads possible later; the owner does not want to pay for data or image licences yet; launch markets are
the US and Australia; minimum age 16. Research: `docs/research/player-images-and-data-licensing.md`. Not legal advice.

**Decisions (owner direction, recorded here for the G-35 confirmation)**
1. **Yahoo**: dropped entirely. Nothing is removed before the 18 Oct draft; afterwards YAHOO-002 retires the login, import
   and Yahoo-derived values. G-04 becomes moot.
2. **Data**: build and use personally on the free NBA sources now; a `DataProvider` interface and a `DATA_LICENSE`
   setting (DATA-039) let a licensed provider be swapped in later. While the licence is `personal`, sign-up stays closed to
   strangers and nothing public is shown.
3. **Images**: no team logos ever without a licence. Player photos only while `DATA_LICENSE=personal` and only for the
   owner (WEB-039); otherwise initials on a team-colour chip. Wikimedia Commons photos (about 45 % coverage, CC BY / BY-SA
   attribution) are an optional later task.
4. **Ads**: nothing legal stops free-to-play with ads, but ads are commercial use: they need a commercial data licence,
   consent for tracking, an updated privacy policy, no betting ads, and a lawyer's look at player names beside ads. Launch
   without ads first.
5. **Markets and age**: US and Australia, 16+ (replaces D-74 Q5 option (a) 13+). Australia adds the Privacy Act, Australian
   Consumer Law on the terms, and a check against the under-16 social media minimum age rules (chat features).
6. **Lawyer**: one review before sign-up opens to strangers or before ads: US, Australia, ads, player names, age.

**Cost**: US$0 now. Commercial data and image licences are reported at about US$500 to 1,000+ a month (UNVERIFIED, needs
quotes); the owner declines that spend until the app has users.
**Tasks**: DATA-039, WEB-039, YAHOO-002; D-74 Q5 and the terms and privacy pages (WEB-037) use 16+ and add Australia.
