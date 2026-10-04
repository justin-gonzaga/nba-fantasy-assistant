---
id: DEC-009
title: "Evidence + explanation templates (number round-trip test)"
epic: EP-50 Decision engine
phase: 5
component: decision
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DEC-008]
areas: [packages/decision/**, apps/api/src/fantasy_api/views.py, apps/api/tests/**]
standards: [ml, evaluation, testing]
assignee:
created: 2026-09-24
completed: 2026-09-28
---
# DEC-009 — Evidence + explanation templates (number round-trip test)

## Objective
Deterministic explanations per ADR-0016: templates filled only from named evidence, and a number round-trip test
over every user-facing text the engine produces today (the Telegram brief and the API's actions).

## Context to read (only these)
- docs/architecture/adr/0016-deterministic-explanations.md

## Acceptance criteria
- [x] AC1: `fantasy_decision.explain.render` fills a template only from named evidence; missing evidence and numbers
      written into the template itself are errors
      Verify: packages/decision/tests/test_explain.py
- [x] AC2: `ungrounded` finds any number in a text that isn't in its evidence
      Verify: test_explain.py::test_round_trip_catches_a_number_that_is_not_in_the_evidence
- [x] AC3: The brief (unchanged text) and the API's action texts are rendered from templates, and every number in
      them round-trips to the evidence
      Verify: test_brief.py::test_every_number_in_the_brief_comes_from_evidence; apps/api/tests/test_views.py::test_every_number_in_the_actions_comes_from_the_snapshot

## Test requirements
TDD; the existing brief and daily-brief tests must pass unchanged (the text is identical).

## Evaluation requirements
The round-trip tests are the evaluation (ADR-0016).

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest -q packages/decision/tests/test_explain.py` | 5 passed |
| AC2 | test | test_round_trip_catches_a_number_that_is_not_in_the_evidence | passed (a forged +0.50 is caught) |
| AC3 | test | test_brief.py (round trip + unchanged render), test_daily_brief.py, test_views.py round trip | passed; `just ci-local` 409 passed, coverage 93.55 % |

## Implementation history
- 2026-09-28: explain.py (render, numbers, ungrounded, MissingEvidenceError, LiteralNumberError); brief.explained
  (render = its lines joined; output identical); views.explained_actions. A template like "of 9 categories" is
  rejected: the count comes from evidence (`len(outlook)`).

## Decisions
_None yet._

## Known issues
- The round trip compares number tokens as text: a value rendered with a different precision than its evidence
  would be flagged (by design: format the evidence where it is used).

## Follow-ups
- DEC-010: the brief's pickups via DEC-008's `best_moves`, with explanations through these templates.
