---
id: DISC-007
title: "Research: Yahoo Fantasy API terms & data retention"
epic: EP-01 Discovery
phase: 0
component: docs
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [docs/research/**, docs/project/human-approval-gates.md (G-04 context only)]
standards: [security]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DISC-007 — Research: Yahoo Fantasy API terms & data retention

## Objective
Find the current Yahoo Fantasy-specific terms and clarify whether league data is 'storable'.

## Context to read (only these)
- `docs/research/2026-09-initial-research.md §1`

## Acceptance criteria
- [x] AC1: Current fantasy-specific ToU located (or documented as unavailable) with URL + access date
      Verify: yahoo-api.md §DISC-007 sources table (fantasy API terms: 404 on 2026-09-27)
- [x] AC2: Relevant clauses quoted with interpretation and uncertainty stated
      Verify: yahoo-api.md §DISC-007 clauses 1-9 and the per-mode interpretation
- [x] AC3: G-04 context section updated; no decision made on the owner's behalf
      Verify: human-approval-gates.md G-04, the DISC-007 update line (status unchanged: APPROVED A2)

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | report | 5 pages checked on 2026-09-27; the fantasy-specific API terms are still 404 (documented; Wayback check left to the owner, since the host is blocked here) | ✅ |
| AC2 | report | 9 clauses quoted verbatim from the live pages; one search-summary claim excluded as UNVERIFIED; interpretation per mode with uncertainty | ✅ |
| AC3 | doc | G-04 context line added; status unchanged (APPROVED A2); no decision made | ✅ |

## Implementation history
- 2026-09-27: researcher subagent fetched the pages; the report was persisted by the main session (the subagent could not write files).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
