---
id: MVP-005
title: "Morning schedule for the daily run"
epic: EP-12 In-season MVP
phase: 5
component: mvp
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [MVP-004]
areas: [tools/**, docs/runbooks/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# MVP-005 — Morning schedule for the daily run

## Objective
Run nba-daily -> week-projection -> brief -> Telegram every morning (Windows Task Scheduler on the laptop; Cloud Run later, INFRA-004).

## Context to read (only these)
- docs/project/STATUS.md (MVP plan)

## Acceptance criteria
- [x] AC1: One command runs the whole chain and exits non-zero on failure
      Verify: a test of the chain command
- [x] AC2: A scheduled task (or documented one-line setup) runs it at 07:30 Sydney
      Verify: runbook + schtasks query

## Test requirements
TDD; offline tests with fixtures.

## Evaluation requirements
Baselines only (no new ML); anything measured is reported with CIs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | test_cli.py::test_daily_run_chains_the_steps_in_order (pre-draft: data only; with a league file: all 4 steps), ::test_daily_run_alerts_and_fails_when_a_step_fails | ✅ |
| AC2 | scheduled task | `tools/schedule_daily.ps1` registered "NBA Fantasy daily brief" (daily 07:30, wake to run, start when available); `Get-ScheduledTask` state Ready (2026-09-28); runbook docs/runbooks/daily-brief.md | ✅ |

## Implementation history
- 2026-09-28: `daily-run` CLI chain with a Telegram failure alert; the Windows scheduled task registered on the owner's laptop (owner's broad approval, 2026-09-27).

## Decisions
- MVP plan (owner, 2026-09-27): a daily Telegram brief from tip-off (20 Oct), baselines only.

## Known issues
- Runs whatever branch is checked out; keep main checked out when idle.
- The laptop must be on or asleep at 07:30 (Cloud Run later, INFRA-004).

## Follow-ups
_None._
