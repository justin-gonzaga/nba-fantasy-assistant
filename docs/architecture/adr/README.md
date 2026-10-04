# Architecture Decision Records

## Process
1. **When**: any decision that is hard to reverse, costs money, changes a component boundary or data contract, or picks a method for ML or decisions.
2. **Who**: Claude (or the owner) drafts from `0000-template.md` via `/adr <title>`. The status starts as **Proposed**.
3. **Approval**:
   - Only the owner moves an ADR to **Accepted**, either directly or by approving its linked gate in `docs/project/human-approval-gates.md`.
   - ML and decision ADRs must cite `[R-xx]` references (ML standard §1).
4. **Immutability**:
   - Once Accepted, the content is frozen. To change a decision, write a new ADR and set the old one to "Superseded by ADR-XXXX".
   - Typo fixes are allowed.
5. **Index**: keep the table below in sync. CI checks it.

## Index
| ADR | Title | Status |
|---|---|---|
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-monorepo-uv-workspace.md) | Monorepo with a uv workspace | Accepted |
| [0003](0003-local-first-hybrid-deployment.md) | Local-first single node; hybrid production path | Superseded by ADR-0019 |
| [0004](0004-duckdb-file-storage.md) | DuckDB + file-based bronze storage | Superseded by ADR-0020 |
| [0005](0005-immutable-snapshots-bitemporal.md) | Immutable raw snapshots and a bitemporal point-in-time model | Accepted |
| [0006](0006-dbt-medallion-transformations.md) | dbt-core with medallion layers (dbt-native names); no MetricFlow | Accepted |
| [0007](0007-thin-custom-ingestion.md) | Thin custom ingestion framework | Accepted |
| [0008](0008-orchestration-cli-cron.md) | Orchestration via a CLI job runner (Cloud Scheduler in prod); Dagster deferred | Accepted |
| [0009](0009-nba-data-sources.md) | NBA data sources | Accepted |
| [0010](0010-yahoo-oauth-readonly-client.md) | Yahoo integration — OAuth2, read-only scope, own client | Accepted |
| [0011](0011-decision-engine-separation.md) | Decision engine separated from models; typed artefact classes | Accepted |
| [0012](0012-probabilistic-decomposed-projections.md) | Decomposed probabilistic projections, baselines first, statistical promotion gate | Accepted |
| [0013](0013-fastapi-react-spa.md) | FastAPI + React SPA; markdown reports first | Accepted |
| [0014](0014-lightweight-experiment-tracking.md) | Lightweight experiment tracking; file-based registry; no feature store | Superseded by ADR-0021 |
| [0015](0015-markdown-task-system-agent-model.md) | In-repo markdown task system and agent operating model | Accepted |
| [0016](0016-deterministic-explanations.md) | Deterministic, evidence-based explanations; LLM optional | Accepted |
| [0017](0017-ci-cd-trunk-based.md) | GitHub Actions CI/CD, trunk-based branching, CalVer releases | Accepted |
| [0018](0018-scoring-format-objectives.md) | Yahoo scoring formats as pluggable objectives | Accepted |
| [0019](0019-gcp-serverless-runtime-terraform.md) | GCP serverless runtime (Cloud Run + Cloud Scheduler), Terraform, dev/prod projects | Accepted |
| [0020](0020-bigquery-warehouse-gcs-raw.md) | BigQuery warehouse in every environment; raw files in GCS | Accepted |
| [0021](0021-mlflow-tracking-registry.md) | MLflow for experiment tracking and model registry (laptop server, GCS artefacts) | Accepted |
| [0022](0022-telegram-notifications-event-processing.md) | Telegram bot as the primary interface; poll-and-react event processing; awake window | Accepted |
| [0023](0023-nl-question-agent-tool-use.md) | Natural-language questions answered by an LLM using vetted tools | Accepted |
| [0024](0024-small-multi-user-public-showcase-app-auth.md) | Small multi-user readiness, app-level login, public repo and showcase | Accepted |
| [0025](0025-yahoo-api-closed-assisted-import.md) | Yahoo Fantasy API closed: apply to the new programme + assisted-import fallback | Accepted |
