---
id: DATA-027
title: "Data design, draft slice (NBA history → player pool → projection inputs)"
epic: EP-21 Warehouse
phase: 0
component: docs
status: done
ready: true
size: M
autonomy: gated
gate: none
depends_on: []
areas: [docs/architecture/**, docs/research/**]
standards: [ml, data-engineering, documentation]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DATA-027 — Data design, draft slice (NBA history → player pool → projection inputs)

## Objective
Part 1 of DATA-000: the sources (stats.nba.com history, CDN schedule, the imported Yahoo settings), the raw → staging → pool tables, lineage, keys, as-of columns and DQ checks for everything the draft helper consumes.

## Context to read (only these)
- docs/research/yahoo-api.md (league settings)
- docs/research/nba-data.md
- docs/research/ml-literature-review.md (verified entries)

## Acceptance criteria
- [x] AC1: Source inventory for the draft slice (confirmed sources only)
      Verify: docs/architecture/data-pipeline-design.md §Part 1
- [x] AC2: Table catalogue for the draft slice (grain, keys, as-of, DQ tests), plus the lineage diagram to the projection inputs
      Verify: same
- [x] AC3: The owner approves via panels (G-22)
      Verify: gates file

## Test requirements
Doc only; citation lint (every [R-xx] is Verified).

## Evaluation requirements
Evaluation designs follow docs/standards/evaluation.md.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | doc | docs/architecture/data-pipeline-design.md §1 (S1–S8, all confirmed) | ✅ |
| AC2 | doc | same, §2 table catalogue + §3 lineage | ✅ |
| AC3 | gate | human-approval-gates.md G-22 APPROVED 2026-09-25; D-47 | ✅ |

## Implementation history
- 2026-09-25: Draft-slice data design written (docs/architecture/data-pipeline-design.md Part 1); walked through with the owner; G-22 approved via panels (Q1 both, Q2 overrides file, Q3 apply after plan review; D-47). Q4 backfill 2015-16+ added under D-49.

## Decisions
_None yet._

## Known issues
Deadline: the owner approves by ~27 Sep, so the draft build fits before 15 Oct.

## Follow-ups
_None._
