# ADR-0006: dbt-core with medallion layers (dbt-native names); no MetricFlow

- **Status**: Accepted · **Date**: 2026-09-24 · **Standards**: S-09, S-10, S-11
- **Related**: `technology-evaluation.md` §4, `system-architecture.md` §4.2, `[R-66]`

## Context
- The owner asked for a medallion architecture with data-quality checks, and for a dbt/Dataform-style tool.
- We need SQL transformations with tests, lineage, SCD2 snapshots, and schema contracts, all running locally on DuckDB.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. dbt-core + dbt-duckdb** | Tests, contracts, snapshots, docs/lineage; agents know it well | Jinja; the dbt Labs/Fivetran merger adds a stewardship risk |
| B. SQLMesh | Virtual envs, column lineage | Smaller community |
| C. Dataform | Clean SQLX | BigQuery-only, which breaks local-first |
| D. Python only | One language | No framework for tests or lineage |

## Decision
- Option A, organised as **bronze** (sources over raw files) → **silver** (`stg_*`, `snp_*`) → **gold** (`dim_*`, `fct_*`, `mart_*`).
- A quality gate sits at each boundary (architecture §4.5).
- Semantic metrics are defined once, in the Python `LeagueRules` module, which generates dbt macros. MetricFlow is not adopted.

## Consequences
- Lineage comes from dbt docs.
- CI runs `dbt build` on fixture bronze data.

## Revisit triggers
The dbt-core licence changes; or incremental or snapshot pain (then evaluate SQLMesh's dbt compatibility).

## Amendment (2026-09-24, before acceptance)
Adapter: **dbt-bigquery** (ADR-0020). Layer names are dbt-native (S-10 B): `staging/` → `intermediate/` → `marts/`; the medallion concept (quality gates) is unchanged. DQ uses dbt tests (S-11 A).
