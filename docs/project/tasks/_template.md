---
id: PREFIX-NNN
title: "Verb-first outcome, ≤ 70 chars"
epic: EP-xx Name
phase: 0
component: ingest
status: todo
ready: false
size: S
autonomy: auto
gate: none
depends_on: []
areas: [path/glob/**]
standards: [testing]
assignee:
created: YYYY-MM-DD
completed:
---
# PREFIX-NNN — Title

## Objective
One or two sentences: the outcome and why it matters (link the requirement, decision or ADR).

## Context to read (only these)
- `path/to/doc.md` §x

## User stories and edge cases
<!-- Required for user-facing tasks (component web or api; IMP-006). One row per persona/situation: who, what they
     want in their words, and what can go wrong (empty, error, slow, stale, invalid input, permissions, phone width,
     keyboard/screen reader). Every edge case maps to an AC or is explicitly out of scope. -->
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| | | |

## Acceptance criteria
<!-- T1: each AC is an observable, measurable outcome + a Verify line naming the exact proof. -->
- [ ] AC1: <observable outcome, with numbers/thresholds where relevant>
      Verify: <test id (file::test) | exact command + expected output | report path>
- [ ] AC2: …
      Verify: …

## Test requirements
Test layers needed (unit/property/contract/integration/leakage/golden/e2e), the fixtures used, and TDD notes.

## Evaluation requirements
n/a — or: metrics, baseline, gate, report path, `[R-xx]` grounding.

## Evidence
<!-- T2: filled at completion; one row per AC. `tasks.py done` refuses without it. -->
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | tests/…::test_… (CI run #n) | pass |

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
