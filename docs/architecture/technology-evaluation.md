# Technology Evaluation

> **Evaluation record (v0.1).** The ★ marks below were Claude's initial recommendations. **The owner's final selections (2026-09-24) are:**
> - Python 3.13 · uv · just · Docker · gh · Ruff (broad) · mypy --strict · pytest (TDD for core)
> - **BigQuery everywhere** (not DuckDB) · raw files in **GCS** · own ingestion layer · **dbt-bigquery** with dbt-native layer names · dbt tests
> - CLI job runner + **Cloud Scheduler → Cloud Run jobs** · **Terraform** · dev/prod projects · WIF · Secret Manager
> - Polars · LightGBM · **MLflow** (laptop + GCS) · HiGHS MILP · NumPy Monte Carlo
> - FastAPI + React/TS SPA (shadcn/ui + Tailwind) · **app-level login** (Firebase Auth) · NL questions via the Claude API with tool use
> - **Telegram bot** notifications · public repo + showcase · native SwiftUI later
>
> The authoritative register is [`docs/project/architecture-decisions.md`](../project/architecture-decisions.md). Section 16 of this document is superseded where it conflicts.

Version 0.1 · 2026-09-24 · Status: **Proposed**. Evidence: `docs/research/2026-09-initial-research.md`.

**Scoring**: each alternative gets 1–5 per criterion (5 = best). The criteria are:
- **Cost**
- **Cx**: simplicity, i.e. low complexity
- **Perf**: performance
- **Scale**
- **Maint**: maintainability
- **DX**: developer experience
- **CC**: Claude Code compatibility (well known to Claude, text-configurable, CLI-driven, fast feedback)
- **Local**: local development
- **Prod**: production deployment

Scores are judgement calls for *this* project (one user, < 5 GB, a Pro budget), not general rankings.

---

## 1. Python toolchain

| Option | Cost | Cx | Perf | Maint | DX | CC | Notes |
|---|---|---|---|---|---|---|---|
| **uv (workspace)** | 5 | 5 | 5 | 5 | 5 | 5 | Single binary; lockfile; workspaces for the monorepo; manages Python versions |
| Poetry | 5 | 3 | 3 | 4 | 4 | 4 | Slower; weaker monorepo story |
| pip + venv + pip-tools | 5 | 3 | 3 | 3 | 3 | 4 | Manual; no workspace |

**Choice: uv**, with **Python 3.13** (already installed; supported by the ML stack in 2026). `requires-python = ">=3.13,<3.14"`.

Also:
- **Ruff** for formatting and linting (replaces black, isort, flake8)
- **mypy --strict** for type checking. Chosen over pyright for its CLI-first output. Re-evaluate Astral `ty` in Phase 9.
- **pytest** + hypothesis + pytest-cov
- **import-linter** for architecture contracts

## 2. Storage / analytical engine

| Option | Cost | Cx | Perf | Scale | Maint | CC | Local | Prod | Notes |
|---|---|---|---|---|---|---|---|---|---|
| **DuckDB + Parquet/JSON files** | 5 | 5 | 5 | 3 | 5 | 5 | 5 | 4 | In-process; reads raw JSON directly; first-class dbt adapter; single-writer |
| PostgreSQL | 5 | 3 | 3 | 4 | 4 | 5 | 4 | 4 | Needs a server; slower for analytics; better for concurrent OLTP (not needed) |
| MotherDuck | 4 | 4 | 5 | 5 | 4 | 4 | 5 | 5 | Hosted DuckDB; nice later if multi-device query is needed; free tier limits |
| BigQuery/Snowflake | 2 | 2 | 5 | 5 | 3 | 4 | 2 | 5 | Overkill; cost; no local parity |
| SQLite | 5 | 5 | 2 | 2 | 4 | 5 | 5 | 4 | Poor for analytical scans |

**Choice: DuckDB + files.** MotherDuck is an upgrade path that needs no code changes (a connection string).

## 3. Ingestion framework

| Option | Cost | Cx | Maint | CC | Notes |
|---|---|---|---|---|---|
| **Thin custom (httpx + tenacity + Pydantic + snapshot store)** | 5 | 4 | 4 | 5 | Full control of immutable raw snapshots and `observed_at`; about 400 LOC framework |
| dlt | 5 | 3 | 4 | 4 | Good schema inference/incremental; but normalises away raw payloads by default and adds its own state model; weaker fit for bitemporal replay |
| Airbyte / Meltano | 4 | 1 | 3 | 2 | Heavy; no Yahoo connector worth using |
| yfpy (Yahoo only) | 5 | 4 | 3 | 4 | Useful reference for OAuth + endpoints; returns parsed objects rather than raw |

**Choice: thin custom framework.** `yfpy` and `nba_api` are used in **spikes** to discover endpoints. `nba_api`
is kept as a dependency for stats.nba.com header/endpoint handling. Raw JSON is written by our own layer.

## 4. Transformation

| Option | Cost | Cx | Maint | CC | Notes |
|---|---|---|---|---|---|
| **dbt-core + dbt-duckdb** | 5 | 4 | 5 | 5 | Tests, docs, lineage graph, snapshots (SCD2), contracts; huge training corpus → Claude writes it well |
| SQLMesh | 5 | 3 | 4 | 3 | Better virtual environments and column lineage; smaller community; less agent familiarity |
| Dataform (Google Cloud) | 4 | 4 | 4 | 3 | SQLX + assertions + dependency graph, similar in spirit to dbt. But it is **BigQuery-only** (managed in GCP; the open-source CLI also targets BigQuery). No DuckDB/local engine, so it would force a BigQuery warehouse and break local-first parity and the $0 target. Reconsider only if we ever move to BigQuery. |
| Pure Python (Polars) | 5 | 4 | 3 | 5 | No lineage or tests framework; logic scattered |

**Choice: dbt-core** (Apache-2.0) + dbt-duckdb. dbt supplies what the medallion design needs:
- layered models (bronze sources → silver `stg_` → gold `dim_`/`fct_`/`mart_`)
- **snapshots** (SCD2) for silver state history
- **model contracts** for schema enforcement
- tests: built-in, plus `dbt_utils` and `dbt_expectations`
- `source freshness`
- the docs site with a lineage graph

Note: dbt Labs and Fivetran announced a merger in Oct 2025. dbt-core remains Apache-2.0. **Risk**: licence or stewardship changes. **Mitigation**: SQLMesh can run many dbt projects, which gives an exit path. Python (Polars) is used for features and models, where SQL is awkward.
Semantic layer: **no MetricFlow**. Category semantics live in one Python module that also generates dbt macros.

## 5. Orchestration

| Option | Cost | Cx | Maint | CC | Local | Notes |
|---|---|---|---|---|---|---|
| **Typer CLI + job DAG + cron/supercronic** | 5 | 5 | 4 | 5 | 5 | Minimal; backfills via `--start/--end`; no UI |
| Dagster | 5 | 2 | 4 | 3 | 4 | Asset lineage, partitions, backfill UI; ~0.5–1 GB RAM daemon; large API surface → more agent context |
| Prefect | 4 | 3 | 3 | 3 | 4 | Good DX; cloud-leaning; less asset-oriented |
| GitHub Actions cron | 5 | 4 | 3 | 4 | 1 | Datacenter IP → stats.nba.com blocked; no persistent disk |
| Airflow | 5 | 1 | 2 | 3 | 2 | Overkill |

**Choice: CLI + cron now.** Adopt Dagster when either trigger in ADR-0008 fires: more than 15 jobs, or backfill pain.

## 6. Data quality

**Choice: dbt tests + Pydantic ingest contracts + custom SQL checks.**

Rejected:
- Great Expectations: too heavy.
- Soda: extra tool.
- Pandera: added only if feature frames need schema checks. Likely yes, it is cheap.

## 7. ML stack

| Need | Choice | Alternatives considered | Reason |
|---|---|---|---|
| Dataframes | **Polars** (+ DuckDB SQL) | pandas | Faster, stricter types; pandas only at library boundaries |
| Tabular models | **LightGBM** | XGBoost, CatBoost | Fast on CPU, quantile objective, mature SHAP support |
| Statistical | **statsmodels, scipy** | PyMC | Bayesian hierarchical models are deferred unless shrinkage baselines prove insufficient |
| Calibration/metrics | **scikit-learn** | — | Standard |
| Explainability | **shap** (TreeExplainer) | — | Standard |
| Optimisation | **HiGHS via `highspy`** (or PuLP→HiGHS) | OR-Tools CP-SAT | Lineup MILP is tiny; HiGHS is MIT and pip-installable |
| Simulation | **NumPy** vectorised | Numba | Fast enough at N=2 000 |
| Experiment tracking | **Run manifests (JSON) + `ml_runs` DuckDB table** | MLflow, W&B | No server, git-friendly, cheap for agents to read; MLflow when >1 active line of experiments needs UI comparison |
| Model registry | **File-based `models/{name}/{version}/manifest.json` + `current` pointer** | MLflow registry | Personal scale |
| Dataset versioning | **Content hash of the raw manifest slice + dbt git SHA** | DVC, lakeFS | raw/ is immutable → (manifest hash, code SHA) fully identifies a dataset |

## 8. Backend

| Option | Cx | Perf | Maint | CC | Notes |
|---|---|---|---|---|---|
| **FastAPI + Pydantic v2** | 5 | 4 | 5 | 5 | Shares Pydantic models with the domain; OpenAPI → TS client generation |
| Litestar | 4 | 5 | 4 | 3 | Fine, less common |
| Django | 2 | 3 | 4 | 5 | ORM/admin unused |

**Choice: FastAPI**, read-mostly. DuckDB is opened read-only per request, with a small cache.

## 9. Frontend

| Option | Cost | Cx | Maint | DX | CC | Mobile UX | Testability | Notes |
|---|---|---|---|---|---|---|---|---|
| **React + Vite + TS + TanStack Query + Tailwind + Recharts** | 5 | 3 | 4 | 4 | 5 | 5 | 5 | Static build served by FastAPI; typed API client; Vitest + Testing Library + Playwright |
| Streamlit | 5 | 5 | 3 | 5 | 5 | 2 | 2 | Fastest prototype; weak mobile layout, reruns whole script; hard to test |
| Next.js | 4 | 2 | 3 | 4 | 5 | 5 | 5 | SSR/server features not needed; adds a Node server |
| Evidence.dev | 5 | 4 | 3 | 4 | 3 | 3 | 2 | Great for SQL reports, weak for interactive tools (trade analyser) |
| HTMX + Jinja | 5 | 4 | 3 | 3 | 4 | 4 | 3 | Viable; less rich charting |

**Choice: React SPA** (gated, G-07). Before the dashboard exists (Phases 3–6), decisions are delivered as
**markdown reports**, which are readable on the phone via Claude Code. That delivers value early without a throwaway UI.
Package manager: **pnpm**.

## 10. Hosting / deployment (G-06)

| Option | $/mo | Cx | stats.nba.com | Always-on | Local parity | Notes |
|---|---|---|---|---|---|---|
| A. Local only + Tailscale | 0 | 5 | ✅ | ❌ | 5 | Start here |
| **B. Hetzner-class VPS + docker compose** | ~5 | 4 | ❌ (backfill local) | ✅ | 5 | Recommended for Phase 8 |
| C. Cloud Run + GCS + Scheduler | 0–3 | 2 | ❌ | ✅ | 3 | DuckDB-on-GCS sync is awkward |
| D. Fly.io | 3–10 | 3 | ❌ | ✅ | 4 | No free tier; volumes OK |
| E. Home mini-PC / Raspberry Pi 5 | one-off ~$100 | 3 | ✅ | ✅ | 5 | Nice alternative to B if you own hardware |

## 11. CI/CD and supply chain

| Need | Choice | Alternatives |
|---|---|---|
| CI | **GitHub Actions** (private repo; the free tier covers this) | GitLab CI |
| Registry | **GHCR** | Docker Hub |
| Containers | **Docker** (multi-stage, non-root, `python:3.13-slim`) + compose | Podman |
| IaC | **None until Phase 8**, then a cloud-init + compose file; Terraform (hcloud provider) only if >1 resource | Pulumi |
| Deploy | GH Actions → build image → SSH `docker compose pull && up -d` with a health-check-gated rollback to the previous tag | Watchtower |
| Security scanning | `pip-audit`, `pnpm audit`, Dependabot, Trivy (image), gitleaks (pre-commit + CI) | Snyk |
| Task runner | **just** (install via `uv tool install rust-just`) | make (not on Windows), poe |
| Pre-commit | **pre-commit** (ruff, gitleaks, EOF/whitespace, nbstripout) | lefthook |

## 12. Secrets

| Option | Choice |
|---|---|
| Local | `.env` (gitignored) loaded by pydantic-settings. The Yahoo refresh token is in `secrets/yahoo_token.json` (gitignored, owner-only permissions) |
| CI | none needed (fixtures only) |
| Prod | VPS `/etc/fantasy/.env` (0600) provisioned manually once. Optionally SOPS+age later |

## 13. LLM usage in the product

| Option | Cost | Choice |
|---|---|---|
| No LLM; templated explanations | $0 | **Default** |
| Claude API (Haiku) rephrase of the evidence JSON | ~$0.10–1/mo | Optional, G-09 (separate API billing; **not** covered by Claude Pro) |
| Ask Claude Code via Remote Control to interpret reports | Pro usage | Already available at no cost |

## 14. Evaluated at the owner's request: `laya` (github.com/NandhaKishorM/laya)

**What it is**, according to its README (reviewed 2026-09-24; claims not independently verified):
- an Apache-2.0 "non-autoregressive decision engine"
- ModernBERT/mmBERT encoder checkpoints, 322–421 M parameters
- it answers typed questions (`choice`, `score`, yes/no) about a **text or JSON state** in one forward pass
- runs on PyTorch, with an optional FastAPI, LangChain and MCP integration

| Possible use here | Assessment |
|---|---|
| Core decisions (lineup, add/drop, trade) | ❌ **Not a fit.** Our decisions are numeric optimisation over calibrated distributions under exact league rules. A general text encoder scoring a JSON state cannot beat MILP + simulation on these problems. It is not calibrated to our domain, and it can't be audited the way evidence-based rules can. It would also violate the "facts are deterministic" principle (spec §8). |
| Classifying free-text signals: injury-report *reason* text, news blurbs (e.g. "rest" vs "injury", "minutes restriction") into features | ⚠️ **Plausible niche.** A keyword or regex baseline will probably cover the structured injury-report reasons. Worth an experiment only if we add unstructured news and the baseline misclassifies materially. |
| Cost | Adds PyTorch plus a ~1–2 GB model. That means a much larger Docker image, and CPU latency far above its GPU benchmark. |

**Decision:** not in the v1 stack. We've recorded experiment **EXP-001** (Phase 9, optional): "text-signal
classifier for injury/news reasons — laya vs keyword baseline, macro-F1 on a labelled sample". It is adopted
only if it beats the baseline and the improved feature measurably helps C5 (availability) under the §4 gate.

## 15. GitHub plan constraint (affects branching strategy, G-01)

Verified on docs.github.com, 2026-09-24:
- **Private repos on GitHub Free have no branch protection, no rulesets, and no environment required-reviewers.**
- On public repos these features are free.
- GitHub Pro (~US$4/mo) enables them on private repos.

The options are in `docs/standards/git-workflow.md` §6. We recommend a private repo on Free, with protection
enforced locally and by the agent (hooks + a `just ship` script that refuses to merge unless CI is green),
and upgrading to Pro if that ever proves leaky.

## 16. Rejected outright (and why)

- Kubernetes, Spark, Kafka, and feature-store products (Feast/Tecton): scale not needed.
- Scraping Yahoo pages: the official API exists.
- Basketball-Reference as a primary source: licensing and strict rate limits.
