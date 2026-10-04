---
id: DATA-000
title: "Data pipeline design: sources to layers to features to models (for owner approval, G-20)"
epic: EP-21 Warehouse
phase: 0
component: docs
status: todo
ready: true
size: M
autonomy: gated
gate: none
depends_on: [DISC-011, DISC-006]
areas: [docs/architecture/data-pipeline-design.md]
standards: [data-engineering, documentation]
assignee:
created: 2026-09-25
completed:
---
# DATA-000 — Data pipeline design (owner approval required)

## Objective
Once every raw source is confirmed, write and present the complete data pipeline design: how each source lands in raw, is shaped through staging → intermediate → marts, becomes point-in-time features, and feeds each model and decision component. The owner approves it via panels (G-20) before any warehouse or feature code.

## Context to read (only these)
- `docs/research/nba-data.md`, `docs/research/yahoo-api.md` (DISC-002)
- `docs/architecture/system-architecture.md` §4
- `docs/architecture/ml-and-decision-design.md` §2a (feature catalogue)
- `docs/standards/data-engineering.md`

## Acceptance criteria
- [ ] AC1: A source inventory of each confirmed source: endpoints, cadence, auth, limits, known quirks, and fixture references.
      Verify: data-pipeline-design.md §1
- [ ] AC2: A layer-by-layer table catalogue (raw, staging, intermediate, marts, features, predictions, recs). Each table has: grain, keys, bitemporal columns (valid/observed), sources, freshness SLA, DQ tests, and the pseudonymisation point.
      Verify: data-pipeline-design.md §2 tables
- [ ] AC3: Lineage diagrams (Mermaid): source → raw → staging → intermediate → marts → features → models/decisions, plus a model-input matrix (which feature views each model and decision component consumes).
      Verify: data-pipeline-design.md §3–4
- [ ] AC4: Point-in-time and leakage controls are shown for every path into a model (the AsOfReader boundaries).
      Verify: data-pipeline-design.md §5
- [ ] AC5: The owner approves via panels (G-20 APPROVED).
      Verify: human-approval-gates.md G-20

## Test requirements
Doc only. Lint that every table named in the diagrams appears in the catalogue.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
- Needs the Yahoo spikes (DISC-001/002), which need the owner's one-time consent click.

## Follow-ups
_None._
