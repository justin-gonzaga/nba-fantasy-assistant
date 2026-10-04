---
id: HARN-003
title: "Package the skills, agents and hooks as a Claude Code plugin"
epic: EP-90 Improvement
phase: 9
component: agents
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: [HARN-001]
areas: [platform-manifest.yaml, docs/standards/**, .claude/**, tools/**]
standards: [agent-skill-development, documentation]
assignee:
created: 2026-09-25
completed:
---
# HARN-003 — Package the skills, agents and hooks as a Claude Code plugin

## Objective
Bundle the manifest's `plugin` list as an installable Claude Code plugin (a marketplace in the template repo or a separate one).

## Context to read (only these)
- platform-manifest.yaml
- docs/project/architecture-decisions.md D-46

## Acceptance criteria
- [ ] AC1: The plugin installs into a fresh repo and exposes /status, /next, /work-task, /new-task, /gate, /checkpoint, /adr + the reviewer/researcher agents
      Verify: install demo
- [ ] AC2: Plugin evals pass (a scenario per skill)
      Verify: `claude plugin eval` report

## Test requirements
A fresh project generated from the template passes `just check`.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
Scheduled after the draft (M0.5).

## Follow-ups
_None._
