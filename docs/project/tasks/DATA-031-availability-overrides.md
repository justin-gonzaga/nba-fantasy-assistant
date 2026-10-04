---
id: DATA-031
title: "Availability overrides: owner-reviewed absences cap projected games (S8)"
epic: EP-15 Draft assistant
phase: 1
component: pipeline
status: done
ready: true
size: S
autonomy: auto
gate: G-22
depends_on: [DRAFT-002]
areas: [apps/pipeline/**, warehouse/seeds/**, docs/research/**]
standards: [data-engineering, testing]
assignee: claude
created: 2026-09-26
completed: 2026-09-26
---
# DATA-031 — Availability overrides: owner-reviewed absences cap projected games (S8)

## Objective
Apply the curated availability-overrides file (D-47 Q2) to the draft projections and values: public source + date per entry, point-in-time checked, reviewed by the owner before the draft.

## Context to read (only these)
- docs/architecture/data-pipeline-design.md §1 (S8), §5

## Acceptance criteria
- [x] AC1: Overrides cap expected games from est_games_missed or expected_return; no estimate means no numeric change (tag only); sources dated after the draft and unmatched names are rejected
      Verify: `apps/pipeline/tests/test_overrides.py`
- [x] AC2: The projections and values use the overrides when the file exists
      Verify: `draft-projections` run with the reviewed file; the capped players' games in `predictions.preseason_projection`
- [x] AC3: The owner has reviewed the list before the draft
      Verify: an owner panel answer recorded here

## Test requirements
Unit tests with fixtures.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | `apps/pipeline/tests/test_overrides.py` (3): caps from the estimate or return date; tag-only when there's no estimate; rejects future-dated sources, unknown statuses and unmatched names | ✅ |
| AC2 | live run | `draft-projections` with `warehouse/seeds/availability_overrides.csv` → Veesaar games 0.0; Duren 63.3 and Ingram 60.8 unchanged (tag only); the board shows the tags (version 4) | ✅ |
| AC3 | owner review | Owner approved the 3-entry list via panel 2026-09-26; re-check after media day (docs/research/availability-overrides-2026-27.md) | ✅ |

## Implementation history
- 2026-09-26:
  - `fantasy_pipeline.overrides` wired into draft-projections, draft-values and the board tags.
  - Researcher list: 3 entries; 2 sources re-checked (HTTP 200); CBS blocked automated access. Owner approved.

## Decisions
- Name matching is accent/case/punctuation-insensitive against the 2026-27 rosters; ambiguous or missing names fail loudly.

## Known issues
_None._

## Follow-ups
_None._
