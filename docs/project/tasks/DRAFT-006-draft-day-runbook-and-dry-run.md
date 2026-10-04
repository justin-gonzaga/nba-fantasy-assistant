---
id: DRAFT-006
title: "Draft-day runbook + dry run with the owner"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: in_progress
ready: true
size: S
autonomy: review
gate: none
depends_on: [DRAFT-004, DRAFT-005]
areas: [docs/runbooks/**]
standards: [documentation]
assignee: claude
created: 2026-09-25
completed:
---
# DRAFT-006 — Draft-day runbook + dry run with the owner

## Objective
**Deadline: the dry run is done by Thu 15 Oct 2026** (draft Sun 18 Oct 17:00 AEDT).

A one-page runbook (what to open, how to use the helper, fallbacks), plus a rehearsal with the owner 1-3 days before the draft.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-42 (draft assistant)
- `docs/research/ml-literature-review.md` R-01, R-02, R-11, R-13

## Acceptance criteria
- [x] AC1: Runbook exists and is phone-readable
      Verify: docs/runbooks/draft-day.md
- [ ] AC2: Dry run completed with the owner; issues fixed or listed
      Verify: Implementation-history entry + follow-up tasks

## Test requirements
Unit tests with fixtures (no network). Property tests where noted. TDD for the package code.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | doc | docs/runbooks/draft-day.md (one page: dry run, final data commands, draft night, fallbacks) | ✅ |
| AC2 | dry run | Thu 15 Oct with the owner (also verifies DRAFT-005 AC3) | ⏳ |

## Implementation history
- 2026-09-26: Runbook written. Added `draft-pool --refresh commonteamroster` so draft-week rosters are fetched again as new snapshots (the resume logic otherwise skips them). Started manually: the CLI claim waits on DRAFT-005 (review), whose last AC is verified by this dry run.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
