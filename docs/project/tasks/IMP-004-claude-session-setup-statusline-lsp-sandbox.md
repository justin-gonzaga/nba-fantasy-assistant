---
id: IMP-004
title: "Claude session setup: status line, Python code intelligence, sandbox"
epic: EP-90 Improvement
phase: 1
component: agents
status: todo
ready: true
size: S
autonomy: review
gate: none
depends_on: [FND-002]
areas: [.claude/**, docs/guides/local-development.md]
standards: [agent-skill-development]
assignee:
created: 2026-09-25
completed:
---
# IMP-004 — Claude session setup: status line, Python code intelligence, sandbox

## Objective
Apply S-38: a status line (context %, branch, current task ID), the Python code-intelligence plugin, and sandboxed Bash (in addition to the allowlist already added).

## Context to read (only these)
- `docs/project/standards-decisions.md` S-36…S-39
- Claude Code docs: statusline, discover-plugins (code intelligence), permission-modes, sandboxing, routines

## Acceptance criteria
- [ ] AC1: The status line shows context usage %, the git branch, and the in-progress task ID
      Verify: screenshot in Evidence; the script lives in `.claude/statusline.py`
- [ ] AC2: The Python code-intelligence plugin is installed and reports a deliberate type error after an edit
      Verify: `/plugin` list + a demo edit → a diagnostic is shown
- [ ] AC3: Sandboxed Bash is enabled, and the project's test commands still run without prompts
      Verify: `/sandbox` status + `just check` runs with no approval prompt
- [ ] AC4: Setup steps are added to the onboarding guide
      Verify: docs/guides/local-development.md §4

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
