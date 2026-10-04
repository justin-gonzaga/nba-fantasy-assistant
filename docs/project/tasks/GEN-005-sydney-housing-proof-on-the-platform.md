---
id: GEN-005
title: "Sydney housing proof on the platform"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: todo
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-004]
areas: [docs/platform/**]
standards: [software-engineering, testing]
assignee:
created: 2026-09-27
completed: null
---
# GEN-005 — Sydney housing proof on the platform

## Objective
Stamp a Sydney housing project from the template and take it to a baseline backtest, measuring how general the kernel really is.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml

## Acceptance criteria
- [ ] AC1: Pre-registered metric: ingestion -> dbt -> a baseline backtest in <= 5 sessions with zero kernel edits; every edit needed is logged and fed back as a kernel fix
      Verify: docs/platform/lessons.md rows + a proof report
- [ ] AC2: Data sources verified for terms of use (NSW Valuer General bulk sales, ABS) before any collection
      Verify: a research note with URLs and dates

## Test requirements
TDD for new platform code; existing tests and backtests must reproduce unchanged.

## Evaluation requirements
The proof metric is pre-registered in AC1.

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
