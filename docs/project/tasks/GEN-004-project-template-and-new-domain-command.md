---
id: GEN-004
title: "Project template and new-domain command"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: todo
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-008]
areas: [tools/**, docs/platform/**]
standards: [software-engineering, testing]
assignee:
created: 2026-09-27
completed: null
---
# GEN-004 — Project template and new-domain command

## Objective
A Copier template (harness + platform + an empty domain pack) plus a domain.yaml spec and `just new-domain` (supersedes HARN-002/003 scope).

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml

## Acceptance criteria
- [ ] AC1: `copier copy` produces a repo that passes `just check`
      Verify: a CI job stamps a throwaway repo and runs just check
- [ ] AC2: domain.yaml schema with validation; `just new-domain` generates a domain-pack skeleton from it
      Verify: tests on an example spec

## Test requirements
TDD for new platform code; existing tests and backtests must reproduce unchanged.

## Evaluation requirements
n/a

## Evidence
_Filled at completion._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
