---
id: RSCH-007
title: "Literature: pre-season performance as a signal; news/NLP and LLM extraction for sports forecasting"
epic: EP-15 Draft assistant
phase: 1
component: research
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [RSCH-006]
areas: [docs/research/**]
standards: [ml, documentation]
assignee:
created: 2026-09-26
completed: 2026-09-26
---
# RSCH-007 — Literature: pre-season performance as a signal; news/NLP and LLM extraction for sports forecasting

## Objective
Find and verify references (D-56) for: (1) whether pre-season/exhibition performance or playing time predicts regular-season role/production (any sport, NBA first); (2) news/text/NLP signals in sports forecasting; (3) the reliability of LLM information extraction (hallucination, grounding, evaluation of extraction accuracy); (4) point-in-time use of news archives (GDELT, Wayback) in forecasting research. Output docs/research/lit-signals.md + ml-literature-review.md §11, from R-92.

## Context to read (only these)
- docs/project/architecture-decisions.md D-55, D-56
- docs/evaluation/reports/DRAFT-007-backtest.md

## Acceptance criteria
- [x] AC1: At least 6 verified references across topics 1-3, or explicitly not found
      Verify: docs/research/lit-signals.md verification table
- [x] AC2: Key result + design note per reference; gaps listed
      Verify: same file, Gaps section
- [x] AC3: Merged into ml-literature-review.md §11
      Verify: ml-literature-review.md

## Test requirements
TDD for package code; fixtures, no network in unit tests.

## Evaluation requirements
Rolling origin [R-50, R-51]; bootstrap CIs [R-54]; ship rules pre-registered before running.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | verification table | docs/research/lit-signals.md: R-92..R-98. Six are peer-reviewed and verified in Crossref by the main session; R-97 (GDELT conference paper) is marked not re-verified. Topics 1-3 covered by R-92, R-93, R-94, R-95, R-96 | ✅ |
| AC2 | gaps section | same file, Gaps 1-4 (no October-exhibition study; no news-to-NBA-role study) | ✅ |
| AC3 | merged | ml-literature-review.md §11 | ✅ |

## Implementation history
- 2026-09-26: The researcher agent found and verified the references but couldn't write files (a host hook failure). The main session rebuilt the files from its report and re-verified every DOI in Crossref.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
