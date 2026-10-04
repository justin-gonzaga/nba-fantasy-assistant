---
id: DATA-035
title: "The daily job publishes draft values, player history and breakout chances (no manual uploads)"
epic: EP-20 Ingestion
phase: 6
component: pipeline
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-019]
areas: [apps/pipeline/**, docs/runbooks/daily-brief.md, infra/terraform/modules/env/daily.tf, .github/workflows/ci.yml]
standards: [data-engineering, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-02
---
# DATA-035 — Pipeline-published draft values

## Objective
The owner chose option C (2026-10-03): a one-off upload of the values file now (done), and a pipeline step so that
data the website reads is never uploaded by hand again. Production data changes then happen only through the deployed
job (code reviewed and deployed by CI), like the rest of the platform. The step also publishes the inputs WEB-018's
badges need.

## Context to read (only these)
- `apps/pipeline/src/fantasy_pipeline/jobs_nba.py` (registry, Context), `draft_values.py`, `workspace.py`
- WEB-018's file contract (task file) and `apps/api/src/fantasy_api/players.py` (what the API reads)

## Files published (serve root, relative paths; the API reads them)
| File | Columns | Source |
|---|---|---|
| `predictions/auction_values.parquet` | as today + `healthy_rank`, `healthy_dollars` | `draft_values.build_values(method=SHIPPED_METHOD)` |
| `predictions/player_history.parquet` | nba_player_id, season, games_played, season_team_games, minutes, draft_year, overall_pick | `int_player_season` (3 seasons before the target) + draft picks |
| `predictions/breakout_probability.parquet` | nba_player_id, kind, p_breakout, season | `predictions.breakout_probability` (target season) |

## User stories and edge cases
| Situation | Behaviour |
|---|---|
| Normal morning | `draft-values` runs in the cloud chain, independent of the brief (optional: a failure never blocks Telegram) |
| Rebuild looks wrong (a variant missing, ranks not 1..n, row count changes > 20 %, or fewer than 5 of the old top 10 still in the new top 10) | the live file is **not** overwritten; the job fails (optional) with the reasons in the run log, and the daily alert names it |
| First run (no previous file) | only the structural checks apply |
| Breakout table empty or absent | the breakout file is skipped (badges simply absent), not an error |
| BigQuery unavailable | the job fails; yesterday's files stay live |
| The PC chain (`run daily`) | runs it too, writing locally; `publish` copies it to the serve root |

## Acceptance criteria
- [x] AC1: `draft_publish.build` returns the three tables from a warehouse (fake in tests) with the documented columns.
      Verify: `uv run pytest -q apps/pipeline/tests/test_draft_publish.py -k build`
- [x] AC2: `draft_publish.check` returns the exact reasons for each failing guard and none for a healthy rebuild.
      Verify: `test_draft_publish.py -k check` (one case per guard + first run)
- [x] AC3: the `draft-values` job writes the files to the workspace only when the checks pass; on failure the old files
      are untouched and the job raises.
      Verify: `test_draft_publish.py -k job`
- [x] AC4: the job is in the cloud and daily chains (optional, independent of the brief), and `publish` copies the
      three files when the workspace is local.
      Verify: `apps/pipeline/tests/test_jobs_nba.py -k draft_values`; `test_publish.py`
- [x] AC5: after deploy, the scheduled cloud run writes the files (run log row `draft-values ok`).
      Verify: `gs://…-serve/ops/job_runs.jsonl` after the next 07:45 run

## Test requirements
TDD with the existing `FakeWarehouse` pattern (synthetic league); no network.

## Evaluation requirements
n/a (publishes the shipped method's outputs; the guard protects against broken rebuilds).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/pipeline/tests/test_draft_publish.py::test_build_returns_the_three_tables_with_the_contract_columns, ::test_build_skips_an_empty_breakout_table, ::test_history_carries_one_draft_only_row_per_rookie | pass |
| AC2 | test | test_draft_publish.py::test_check_passes_a_healthy_rebuild_and_a_first_run, ::test_check_names_each_failing_guard | pass |
| AC3 | test | test_draft_publish.py::test_job_writes_only_when_the_checks_pass, ::test_a_failed_write_leaves_the_live_values_untouched | pass |
| AC4 | test | apps/pipeline/tests/test_jobs_nba.py (chain order incl. draft-values; cloud registry; ::test_draft_values_runs_independently_and_a_refusal_never_blocks_the_brief); test_publish.py::test_draft_files_are_published_when_present | pass |
| AC5 | run log | `gs://nbafa-hdfo-dev-serve/ops/job_runs.jsonl`: `2026-10-02T21:46:21 draft-values success 5890` (execution `daily-sk7hx`); `auction_values`, `player_history`, `breakout_probability` written 21:46:44Z by the job | pass |

## Implementation history
- 2026-10-03 — Specified (owner option C; the one-off upload was done with approval the same day).
- 2026-10-03 — Built TDD: `draft_publish.build/check/run_job`, the optional `draft-values` job in both chains,
  publish copies the three files. The cloud job lacked GCP_PROJECT: added to Terraform's daily.tf and to CI's
  `jobs update` (same value, no drift); without it the job skips rather than guessing a project. Rookie rows match
  WEB-018's contract. `just ci-local`: 462 passed, coverage 93.45 %.

## Decisions
- Review (High): writes are ordered supporting files first, values last, so a failed write never leaves new values
  with stale history; tested. Runbook updated (no manual copies of these files).
- `SHIPPED_METHOD = "H1+aging+M1"` lives in one constant (the method on the live file); changing it is a reviewed code change.

## Known issues
- Growth-breakout probabilities aren't stored yet (only bounce-back); the growth badge stays absent until a task writes them.

## Follow-ups
_None._
