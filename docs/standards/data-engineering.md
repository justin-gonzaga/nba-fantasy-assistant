# Data Engineering Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

Architecture: the medallion concept with dbt-native names: **raw** (GCS, immutable) → `staging` → `intermediate` → `marts` in **BigQuery**, with quality gates at each boundary (ADR-0006, ADR-0020).
See `system-architecture.md` §4.

## 1. Raw (bronze) rules
- Raw lives in GCS (`gs://<prefix>-raw-{env}/raw/…`) and is written only through the storage abstraction. The prod bucket has versioning + a retention policy, and the ingest service account cannot delete.
- **Yahoo payloads are pseudonymised before the write** (G-04 A2) by a versioned transform.
- **Immutable, append-only.** Nothing under `raw/` is ever modified or deleted, except by the retention job approved in G-04.
- Every payload has a manifest row:
  - `payload_id` (uuid7)
  - `source`, `endpoint`, `params_json` (canonical, sorted)
  - `observed_at` (UTC; the time the response was received)
  - `http_status`
  - `content_sha256`
  - `schema_version`
  - `run_id`
  - `bytes`
- Storage is deduplicated by content hash, but a manifest row is **always** written: "we saw the same content again at time t" is itself point-in-time information.
- PDFs (injury reports) are stored as the original PDF plus the extracted JSON, with the extractor version recorded.

## 2. Data contracts
- Each source endpoint has a Pydantic contract covering **only the fields we consume**, with `extra="allow"`.
- The contract lives next to the client: `fantasy_ingest/sources/<source>/contracts.py`.
- **Contract tests** run against recorded fixtures in `packages/ingest/tests/fixtures/<source>/`. A monthly `just contracts-live` run re-validates against live responses. This is local only, because of IP restrictions.
- Staging and mart models that feed Python code declare `contract: {enforced: true}` with explicit column types.

## 3. Schema evolution
| Change | Handling |
|---|---|
| New upstream field | No action. It is kept in bronze; add it to the contract only when it is consumed |
| Removed or renamed consumed field | Contract violation → the payload is quarantined → the job fails → a task is created to add a versioned parser (`schema_version` + 1). Old payloads keep parsing with the old parser |
| Our model change (staging/intermediate/marts) | Additive by default. Breaking changes need a new model version (`fct_x_v2`) and a migration note. The entire staging/intermediate/marts stack can be rebuilt from raw (`just rebuild`) |

## 4. Idempotency, incremental loads, and backfills
- Jobs are keyed by a partition, usually the NBA game date or the Yahoo week, and are re-runnable.
- Staging models are **incremental** with `unique_key` + `observed_at` watermarks. A full refresh must give identical results (tested in CI on fixtures).
- Backfills: `just backfill <job> --start --end`. It resumes from checkpoints (`ops.job_runs`), is rate-limit aware, and is safe to interrupt.
- A "catch-up" rule: the daily job computes every missing partition since its last success, which handles the laptop being off.

## 5. Point-in-time (bitemporal) modelling
- Two notions of time, never conflated:
  - `valid_from`/`valid_to`: when a state held in the world
  - `observed_at`: when we knew it [R-65]
- Tables of time-varying facts are modelled as SCD2 from snapshots: rosters, ownership, injury designation, eligibility, league settings.
- All downstream reads for ML, decisions, and evaluation go through `AsOfReader(t)`, which filters `observed_at <= t`. Direct reads of these tables from `features/`, `models/`, `decision/`, and `evaluation/` are blocked by an import-linter/SQL-lint rule.

## 6. Data quality
- The dimensions, layers, and severities are in the architecture §4.5.
- Minimum per model: primary-key `unique` + `not_null`. Also `relationships` for every foreign key, and range tests for every numeric stat.
- Every new source gets `source freshness` thresholds.
- DQ failures block promotion to the next layer. Warnings show on the dashboard.

## 7. Naming (dbt)
- Sources (raw): `raw.<source>__<endpoint>` (external tables over GCS)
- Staging: `stg_<source>__<entity>`, snapshots `snp_<entity>`
- Intermediate: `int_<purpose>`
- Gold: `dim_<entity>`, `fct_<process>`, `mart_<decision_area>`
- Columns: `snake_case`. IDs are suffixed `_id` (`nba_player_id`, `yahoo_player_key`). Timestamps are `*_at` (UTC); dates are `*_date`.

## 8. Retry and failure recovery
- HTTP retries: exponential backoff with jitter (tenacity), capped at 5 attempts. `Retry-After` is respected.
- Per-source rate limiters:
  - stats.nba.com ≥ 0.6 s between requests
  - Yahoo: conservative, 1 req/s, adaptive on 999/429 responses
- A partial failure (one endpoint down) marks the run `degraded`, and downstream steps run on the last good data, with a staleness warning.

## 9. Lineage and metadata
- dbt docs provide the SQL lineage, and `just docs-data` builds them.
- Python feature views declare their input tables in code. A test checks that those declarations match the tables actually read.
- The manifest (`run_id`) links each derived row back to the raw payloads.
