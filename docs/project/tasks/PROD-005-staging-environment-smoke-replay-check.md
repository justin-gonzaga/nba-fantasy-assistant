---
id: PROD-005
title: "Staging environment + smoke + replay check"
epic: EP-80 Production
phase: 8
component: infra
status: cancelled
ready: false
size: M
autonomy: review
gate: none
depends_on: [PROD-004]
areas: [infra/**, .github/**]
standards: [devops, security]
assignee:
created: 2026-09-24
completed:
---
# PROD-005 — Staging environment + smoke + replay check

## Objective
Staging environment + smoke + replay check.

## Acceptance criteria
_To be refined (ready: false). Run `/new-task refine PROD-005` when its dependencies are nearly done, so the spec reflects the code that actually exists._

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
Cancelled 2026-09-24: I2 A selected two environments (dev, prod); the dev project serves as staging (auto-deploy on merge + smoke test).

## Follow-ups
_None._
