---
id: HARN-001
title: "Audit generic assets: remove project specifics from manifest-listed files"
epic: EP-90 Improvement
phase: 9
component: agents
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: []
areas: [platform-manifest.yaml, docs/standards/**, .claude/**, tools/**]
standards: [agent-skill-development, documentation]
assignee:
created: 2026-09-25
completed:
---
# HARN-001 — Audit generic assets: remove project specifics from manifest-listed files

## Objective
Make every file in platform-manifest.yaml project-agnostic (parameterise names/paths; move NBA specifics into project docs).

## Context to read (only these)
- platform-manifest.yaml
- docs/project/architecture-decisions.md D-46

## Acceptance criteria
- [ ] AC1: Every manifest file is free of NBA/fantasy specifics
      Verify: `just harness-lint` (a grep for a project-term list) → 0 hits
- [ ] AC2: Project-specific content moved out has links back
      Verify: diff review

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
