# ADR-0020: BigQuery warehouse in every environment; raw files in GCS

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: D-04 B2, D-07 A, I3 · **Supersedes**: ADR-0004
- **Related**: ADR-0005, ADR-0006, ADR-0019

## Context
Cloud Run jobs have no persistent disk, so a file-based DuckDB doesn't fit production. The owner prefers one SQL dialect everywhere.

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
- **BigQuery** is used in local dev, CI (ephemeral per-PR datasets), dev and prod. dbt uses the **dbt-bigquery** adapter.
- Raw (bronze) payloads are immutable files in GCS, written through a storage abstraction and exposed to dbt as sources/external tables.
- Dev reads the prod raw bucket read-only.

## Consequences
- One dialect.
- Tests that touch SQL need GCP credentials (unit tests remain offline).
- Cost stays within the BigQuery free tier at our volume (to be monitored).

## Revisit triggers
Costs exceed the free tier, or offline development becomes essential (then consider DuckDB for dev).
