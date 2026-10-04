---
id: INFRA-007
title: "Fetch / cloud job split with a staleness note"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-006]
areas: [apps/pipeline/**, docs/**]
standards: [devops, security]
assignee:
created: 2026-10-02
completed: 2026-10-02
---
# INFRA-007 — Fetch / cloud job split with a staleness note

## Objective
D-63: `fantasy run fetch` runs only the NBA fetch jobs (cdn-day with catch-up, game-logs) on the owner's PC; `fantasy run cloud`
runs the rest (injury report, week projection, brief, send, publish) without them, so it works from Cloud Run on whatever raw data
exists; the brief and the API say when the newest game data is older than yesterday.

## Context to read (only these)
- D-63 in docs/project/architecture-decisions.md; docs/project/tasks/INFRA-006-pipeline-jobs-on-cloud-run.md

## Acceptance criteria
- [x] AC1: `run fetch` runs exactly the fetch jobs (with catch-up); `run cloud` runs the rest and never the fetch jobs
      Verify: apps/pipeline/tests/test_jobs_nba.py, test_cli.py
- [x] AC2: When scheduled games before today are missing from the stats, the brief's first line says so (DEC-009)
      and the snapshot carries `stale_since`
      Verify: apps/pipeline/tests/test_daily_brief.py
- [x] AC3: `daily-run` (the local all-in-one) still works unchanged
      Verify: test_cli.py

## Test requirements
TDD.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | test_jobs_nba.py::test_the_cloud_registry_leaves_out_the_nba_fetch; test_cli.py::test_run_fetch_runs_only_the_nba_fetch, test_run_cloud_runs_the_rest_without_the_fetch | passed |
| AC2 | test | test_week_projection.py (newest_game, stale_since); test_daily_brief.py::test_a_stale_week_table_is_flagged_first_in_the_brief_and_the_snapshot | passed |
| AC3 | test | test_cli.py::test_daily_run_uses_the_runner_logs_results_and_releases_the_lock | passed; `uv run pytest -q apps packages` 356 passed |

## Implementation history
- 2026-10-02: jobs_nba FETCH_TARGETS / CLOUD_TARGETS and `registry(include_fetch=)`; CLI `run fetch` (catch-up) and `run cloud`; week_projection `newest_game` + `stale_since` (the first scheduled game after the newest logged one and before today; pre-season none) into the week table; the brief's first line warns (explain template) and the snapshot carries `stale_since`; the failure alert names both log locations.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- Show `stale_since` on the website (API Freshness + the SPA's Freshness line).
