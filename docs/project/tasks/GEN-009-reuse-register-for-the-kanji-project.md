---
id: GEN-009
title: "Reuse register for the next project (Japanese kanji trainer)"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [docs/platform/**]
standards: [documentation]
assignee: claude
created: 2026-10-04
completed: 2026-10-04
---
# GEN-009 — Reuse register

## Objective
The owner (2026-10-04) plans a commercial Japanese kanji trainer for JLPT (public free datasets, multiple-choice
drills, an ML model of what the learner needs to work on, frequency-first ordering) and wants the learnings,
boilerplate and patterns from this repo tracked as we go. Add one register that maps each reusable asset to its path,
status and what changes, plus the rule that keeps it current, and add the two lessons from today.

## Context to read (only these)
- `docs/platform/lessons.md`, `docs/platform/generalisation-plan.md`, `platform-manifest.yaml`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner starting the kanji repo | "What can I copy, and what do I rewrite?" | candidate assets that still carry NBA names are marked, not claimed ready |
| Claude closing any task | "Do I record this for reuse?" | the rule is on the page; the manifest classifies new files |
| Commercial use | "Can I use these datasets?" | every licence statement is marked UNVERIFIED until researched |

## Acceptance criteria
- [x] AC1: `docs/platform/reuse-register.md` lists each reusable asset with path, status (ready, candidate, rewrite,
      not reusable) and the kanji-project use, plus the upkeep rule and early kanji notes.
      Verify: the file exists and `python tools/tasks.py validate` passes
- [x] AC2: lessons 46 (phone fit) and 47 (CI billing) are appended to the ledger.
      Verify: `grep -c "^| 4[67] " docs/platform/lessons.md` prints 2
- [x] AC3: every path named in the register's table exists in the repo (or is marked as in progress).
      Verify: a script checks each path in the table column "Where" (two are marked in progress)

## Test requirements
n/a (documentation)

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | cmd | `tasks.py validate` | pass |
| AC2 | cmd | grep count | pass |
| AC3 | cmd | path check | pass |

## Implementation history
- 2026-10-04 — Specified and written from the owner's message.

## Decisions
- One register file rather than spreading notes over the lessons ledger: the ledger is append-only history, the register is a current map.

## Known issues
_None._

## Follow-ups
- A kanji-project data-and-licence research task belongs in that repo's first backlog, not here.
