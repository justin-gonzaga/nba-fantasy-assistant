---
id: IMP-005
title: "Weekly Claude routine: status, dependency triage, board and agent-metrics check"
epic: EP-90 Improvement
phase: 2
component: agents
status: todo
ready: true
size: S
autonomy: review
gate: none
depends_on: [FND-006, IMP-001]
areas: [.claude/**, docs/guides/local-development.md]
standards: [agent-skill-development]
assignee:
created: 2026-09-25
completed:
---
# IMP-005 — Weekly Claude routine: status, dependency triage, board and agent-metrics check

## Objective
Apply S-39: a scheduled weekly routine that sends the owner a phone-length status report, triages Dependabot PRs (merges Tier A patch/minor on green), checks the task board and agent metrics, and flags stale docs.

## Context to read (only these)
- `docs/project/standards-decisions.md` S-36…S-39
- Claude Code docs: statusline, discover-plugins (code intelligence), permission-modes, sandboxing, routines

## Acceptance criteria
- [ ] AC1: The routine is configured and runs weekly (Sunday evening Sydney time)
      Verify: routine listing + the first run's report linked in Evidence
- [ ] AC2: Its report is at most 20 lines and ends with the decisions needed, if any
      Verify: the first report
- [ ] AC3: Usage stays small: under X% of weekly Pro usage (measured over 2 runs)
      Verify: usage figures recorded

## Test requirements
Configuration only; verification commands/screenshots.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
