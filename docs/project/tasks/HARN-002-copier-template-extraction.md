---
id: HARN-002
title: "Extract a Copier project template (with updates) from the harness"
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
# HARN-002 — Extract a Copier project template (with updates) from the harness

## Objective
Create a separate template repo from the manifest's `template` list, with Copier questions (project name, package prefix, cloud, etc.).

## Context to read (only these)
- platform-manifest.yaml
- docs/project/architecture-decisions.md D-46

## Acceptance criteria
- [ ] AC1: `copier copy` creates a new project that passes `just check` out of the box
      Verify: a temp dir run log
- [ ] AC2: `copier update` pulls template improvements into an existing project
      Verify: demo on a scratch project

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
