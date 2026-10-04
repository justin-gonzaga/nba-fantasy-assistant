---
id: FND-009
title: "Claude Code hooks & permissions (guardrails)"
epic: EP-10 Foundation
phase: 1
component: agents
status: todo
ready: true
size: S
autonomy: review
gate: G-11
depends_on: [FND-003]
areas: [.claude/settings.json, .claude/hooks/**]
standards: [agent-skill-development, security]
assignee:
created: 2026-09-24
completed:
---
# FND-009 — Claude Code hooks & permissions (guardrails)

## Objective
Enforce agent guardrails deterministically.

## Context to read (only these)
- `docs/agents/agent-architecture.md §5`
- `docs/standards/agent-skill-development.md`

## Acceptance criteria
- [ ] AC1: SessionStart hook injects `just status` brief (<= 30 lines)
- [ ] AC2: PreToolUse hook blocks: push to main, --force, reset --hard, rm -rf on data/raw/repo root, reads of .env*/secrets
- [ ] AC3: PostToolUse hook runs ruff format + fix on edited .py files
- [ ] AC4: Hook scripts are cross-platform (Python) and unit-tested
- [ ] AC5: Eval scenarios in .claude/evals/guardrails.yaml demonstrate blocks
- [ ] AC6: **Stop hook (S-36)**: on a `task/*` branch with uncommitted or unpushed code changes, run `just check`, and block the turn from ending while it fails. Docs-only changes and non-task branches are skipped, and the hook's output is short.
      Verify: `.claude/evals/stop-hook.yaml` scenarios (a failing test blocks; a docs-only change passes) + a hook unit test

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
