---
id: INFRA-006
title: "Pipeline workspace root (local or gs://) for the daily chain"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [INFRA-004]
areas: [apps/pipeline/**, packages/dikit/src/dikit/jobs.py, packages/core/src/fantasy_core/settings.py, docs/**]
standards: [devops, testing]
assignee:
created: 2026-09-28
completed: 2026-10-02
---
# INFRA-006 — Pipeline workspace root (local or gs://) for the daily chain

## Objective
First of three tasks for D-63 (hybrid: the owner's PC fetches NBA data, a Cloud Run job runs the rest): every file
the daily chain reads or writes outside raw (projections, values, league file, league settings, briefs, run log)
goes through a configurable workspace root, `WORK_ROOT` (local "data" by default, or gs://). No behaviour change
locally. Follow-ups: INFRA-007 (fetch / cloud job split + staleness note), INFRA-008 (Terraform + switch-over).

## Context to read (only these)
- D-63, D-62, D-28 in docs/project/architecture-decisions.md

## Acceptance criteria
- [x] AC1: `fantasy_pipeline.workspace` reads and writes text and parquet under a local or fsspec (gs://-like) root
      Verify: apps/pipeline/tests/test_workspace.py (local and memory:// roots)
- [x] AC2: The kernel's run log (`dikit.jobs.JsonlSink`) works on any fsspec URL (object stores can't append:
      it rewrites)
      Verify: test_workspace.py::test_the_run_log_sink_appends_and_reads_back (both roots); packages/dikit tests
- [x] AC3: The daily chain and its manual commands use the workspace; the default keeps today's layout; tests never
      touch the real data/ folder
      Verify: `uv run pytest -q apps packages`; `uv run fantasy week-projection` writes data/predictions/week_projection.parquet

## Test requirements
TDD; fsspec memory:// for gs-like roots.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest -q apps/pipeline/tests/test_workspace.py` | passed (local + memory roots) |
| AC2 | test | test_the_run_log_sink_appends_and_reads_back; `uv run pytest -q packages/dikit` | passed |
| AC3 | test + smoke | `uv run pytest -q apps packages` -> 350 passed; `uv run fantasy week-projection` -> 589 players, file written via the workspace; no file under data/ newer than the change after the tests | passed |

## Implementation history
- 2026-10-02: spike: a temporary Cloud Run job probed each source from australia-southeast1 and us-central1:
  cdn.nba.com 403, stats.nba.com timeout, injury PDFs 200, Telegram 200 (D-63). Probe jobs deleted.
- 2026-10-02: workspace.py (Workspace, RunLogSink, use/get), settings `work_root` and `telegram_chat_id`,
  dikit JsonlSink on fsspec URLs, daily_brief/week_projection/jobs_nba/publish/cli on the workspace; the telegram
  chat id may come from settings (the cloud has no chat file); alerts reuse the brief's sender. The task was split
  (one task = one PR): INFRA-007 and INFRA-008.

## Decisions
- D-63 (delegated): hybrid PC fetch + cloud chain.
- `telegram.py` (platform) stays path-based; the cloud gets TELEGRAM_CHAT_ID instead of a chat file.
- The run lock stays machine-local (data/ops/run.lock): a Cloud Run job runs one task at a time.

## Known issues
- Draft-time and report outputs (draft board, evaluation reports, availability rates) stay local by design.

## Follow-ups
- INFRA-007, INFRA-008.
