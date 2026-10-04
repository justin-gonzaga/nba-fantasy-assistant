---
id: FND-011
title: "Pipeline CLI skeleton: job registry, JobResult, lock, catch-up"
epic: EP-10 Foundation
phase: 1
component: pipeline
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [FND-010]
areas: [apps/pipeline/**, packages/core/**]
standards: [software-engineering, data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# FND-011 — Pipeline CLI skeleton: job registry, JobResult, lock, catch-up

## Objective
Typer CLI to run idempotent partitioned jobs with dependency order and catch-up of missed partitions.

## Context to read (only these)
- `docs/architecture/system-architecture.md §4.4`

## Acceptance criteria
- [x] AC1: `uv run fantasy run <job> --date/--start/--end` and `fantasy run daily`
      Verify: test_cli.py::test_run_named_jobs_over_a_date_range; live `uv run fantasy run daily`
- [x] AC2: Jobs declare deps and partition type; DAG executed in order; failure stops dependents, marks degraded where configured
      Verify: packages/core/tests/test_jobs.py
- [x] AC3: JobResult persisted to `ops.job_runs` (BigQuery; an in-memory fake in unit tests) with run_id, rows, duration, status
      Verify: test_jobs.py (MemorySink, JsonlSink); the BigQuery sink is a follow-up (no `ops` dataset yet)
- [x] AC4: Single-writer lock file prevents concurrent runs
      Verify: test_jobs.py lock tests (held, released, stale takeover)
- [x] AC5: Catch-up: daily computes all missing partitions since last success
      Verify: test_jobs.py catch-up tests; test_jobs_nba.py::test_catch_up_fetches_each_missed_day
- [x] AC6: Unit + integration tests with dummy jobs
      Verify: test_jobs.py (9), test_jobs_nba.py (2), test_cli.py runner tests (3)

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + live | `fantasy` console script; `fantasy run <jobs> --start --end`; live `uv run fantasy run daily`: 6 jobs, all success, week-projection 589 rows | ✅ |
| AC2 | tests | order, skip-on-failure, optional → degraded, cycle detection | ✅ |
| AC3 | tests | JobResult (run_id, job, partition, status, rows, seconds, started_at, error) to a Sink: MemorySink (tests), JsonlSink `data/ops/job_runs.jsonl` (laptop). The BigQuery `ops.job_runs` sink waits for an `ops` dataset (INFRA follow-up) | ✅ (BigQuery sink: follow-up) |
| AC4 | tests | RunLock: a second run raises LockHeldError; released on exit; a lock older than 2 h is taken over | ✅ |
| AC5 | tests | missing_partitions: every day since the last success (cap 14), oldest first | ✅ |
| AC6 | tests | 14 tests across core, pipeline and CLI | ✅ |

## Implementation history
- 2026-09-28: `fantasy_core.jobs` (platform) + `fantasy_pipeline.jobs_nba` (the NBA graph); `daily-run` now uses the runner (the scheduled task is unchanged). FND-010 (package stubs) was already satisfied by the workspace layout.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- A BigQuery `ops.job_runs` sink once an `ops` dataset exists (Terraform, INFRA-004).
