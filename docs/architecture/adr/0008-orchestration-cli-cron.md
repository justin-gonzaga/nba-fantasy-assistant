# ADR-0008: Orchestration via a CLI job runner (Cloud Scheduler in prod); Dagster deferred

- **Status**: Accepted · **Date**: 2026-09-24 · **Standards**: S-13
- **Related**: `technology-evaluation.md` §5

## Context
- There are about 10 jobs at first.
- Snapshot collection must be live before 2026-10-20.
- Agent context cost matters (Claude Pro).

## Options considered
See S-13:
- **A.** CLI + cron (★)
- **B.** Dagster now
- **C.** Prefect

## Decision
- Build a Typer CLI with a small, explicit job DAG. Jobs have the signature `run(partition, ctx) -> JobResult`, and are idempotent and catch-up aware.
- Scheduling: Windows Task Scheduler locally, supercronic in the container.
- The job signature deliberately mirrors Dagster's partitioned assets, which keeps a later migration mechanical.

## Consequences
- Fast to build.
- There is no lineage UI; dbt docs cover SQL lineage.

## Revisit triggers
More than 15 jobs, painful partition backfills, or a need for asset-level lineage across Python and SQL.

## Amendment (2026-09-24, before acceptance)
Production scheduling uses **Cloud Scheduler → Cloud Run jobs** (ADR-0019); local runs use the same CLI. Event processing is per ADR-0022.
