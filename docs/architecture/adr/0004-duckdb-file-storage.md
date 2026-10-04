# ADR-0004: DuckDB + file-based bronze storage

- **Status**: Superseded by ADR-0020 · **Date**: 2026-09-24 · **Gate**: G-00
- **Related**: `technology-evaluation.md` §2

## Context
The workload is analytical (scans, window functions, aggregates), with a single writer (the scheduler) and low concurrency (one dashboard user).

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. DuckDB file + raw JSON/Parquet files** | In-process, $0, fast, first-class dbt adapter, reads JSON directly | Single writer |
| B. PostgreSQL | Concurrency | Server to run; slower analytics |
| C. BigQuery/Snowflake | Scale | Cost; no local parity |
| D. MotherDuck | Hosted DuckDB | Not needed yet |

## Decision
- Option A.
- Bronze is stored as files; silver, gold and serving data live in `warehouse.duckdb`.
- The API opens the database read-only.

## Consequences
- Rebuilding from bronze is cheap.
- Backups are file copies.
- Accepted: jobs must not write concurrently. The pipeline CLI holds a lock file.

## Revisit triggers
Multi-device querying is needed (then use MotherDuck), or the data grows beyond 50 GB.
