---
id: FND-013
title: "Alerting: Telegram system messages + healthchecks dead-man switch"
epic: EP-10 Foundation
phase: 1
component: pipeline
status: todo
ready: true
size: S
autonomy: auto
gate: G-08
depends_on: [FND-011]
areas: [packages/core/**, apps/pipeline/**, docs/runbooks/**]
standards: [devops]
assignee:
created: 2026-09-24
completed:
---
# FND-013 — Alerting: Telegram system messages + healthchecks dead-man switch

## Objective
Get notified on the phone when jobs fail, degrade, or stop running.

## Context to read (only these)
- `docs/standards/devops.md §7`

## Acceptance criteria
- [ ] AC1: Notifier protocol with a Telegram implementation (bot token from Secret Manager / dev .env) and a no-op for tests
- [ ] AC2: Job failure/degraded -> push; successful daily run pings healthchecks URL
- [ ] AC3: Runbook for creating the Telegram bot (BotFather) + healthchecks check (owner steps)

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
