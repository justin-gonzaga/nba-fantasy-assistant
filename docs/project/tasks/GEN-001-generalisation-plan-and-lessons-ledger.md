---
id: GEN-001
title: "Generalisation plan (D-58) and lessons ledger"
epic: EP-11 Platform generalisation
phase: 1
component: docs
status: done
ready: true
size: S
autonomy: review
gate: G-01
depends_on: []
areas: [docs/platform/**, docs/project/architecture-decisions.md]
standards: [documentation]
assignee: claude
created: 2026-09-27
completed: 2026-09-27
---
# GEN-001 — Generalisation plan (D-58) and lessons ledger

## Objective
Propose how the whole stack generalises into a Claude-operated factory for decision products, and start recording lessons with evidence.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml

## Acceptance criteria
- [x] AC1: A plan classifies the existing assets into harness / platform / domain, with phases, a second-domain proof metric and owner options
      Verify: docs/platform/generalisation-plan.md §3, §6-8
- [x] AC2: The lessons ledger exists, seeded with evidence-backed lessons from this project
      Verify: docs/platform/lessons.md (17 rows, each with an evidence reference)
- [x] AC3: The owner picks the D-58 options; follow-up tasks (G0 manifest layers, G1 kernel extraction, G3 proof) are created to match
      Verify: architecture-decisions.md D-58 status; tasks.py validate

## Test requirements
Docs only: `tasks.py validate`.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | doc | generalisation-plan.md | ✅ |
| AC2 | doc | lessons.md, 17 rows | ✅ |
| AC3 | owner + tasks | D-58 selected; GEN-002..GEN-005 created | ✅ |

## Implementation history
- 2026-09-27: Requested by the owner (generalise the stack; track what works; commercial intent).

## Decisions
- D-58: 1(a) kernel in this repo, 2(a) Sydney housing, 3(c) start now.

## Known issues
_None._

## Follow-ups
_None._
