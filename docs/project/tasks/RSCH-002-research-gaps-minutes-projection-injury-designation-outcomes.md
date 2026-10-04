---
id: RSCH-002
title: "Research gaps: minutes projection & injury-designation outcomes"
epic: EP-02 Research
phase: 0
component: docs
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [docs/research/**]
standards: [ml]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# RSCH-002 — Research gaps: minutes projection & injury-designation outcomes

## Objective
Search peer-reviewed and reputable practitioner literature for NBA minutes models and injury-designation play rates.

## Context to read (only these)
- `docs/research/ml-literature-review.md §8`

## Acceptance criteria
- [x] AC1: Search log (queries, databases) recorded
      Verify: docs/research/lit-minutes-injury.md §Search log
- [x] AC2: Findings added to literature review with quality rating (peer-reviewed / practitioner / anecdotal)
      Verify: ml-literature-review.md §8 and §12; lit-minutes-injury.md §References
- [x] AC3: Implications for C2/C5 designs noted in ml-and-decision-design.md (proposal only, via Tier B)
      Verify: ml-and-decision-design.md §C2 / C5 research update (PROPOSAL)

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | report | lit-minutes-injury.md search log: 12 queries (Google, PubMed, arXiv, publisher pages, ESPN) | ✅ |
| AC2 | report | 7 verified references R-99..R-105 with quality ratings (5 peer-reviewed, 2 preprints); 1 excluded as unverifiable; both gaps answered (designation rates: none measured; minutes: none peer-reviewed) | ✅ |
| AC3 | doc | PROPOSAL block in ml-and-decision-design.md; merges only with owner review (Tier B) | ✅ (proposal) |

## Implementation history
- 2026-09-27: researcher subagent ran the search; references verified at source; report persisted by the main session (the subagent could not write files).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
