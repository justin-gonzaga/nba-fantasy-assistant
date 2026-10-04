---
id: DISC-011
title: "Spike: assisted import of Yahoo pages (league settings, roster, matchup schedule)"
epic: EP-01 Discovery
phase: 0
component: ingest
status: blocked
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [docs/**, packages/ingest/**, apps/**]
standards: [data-engineering, security]
assignee:
created: 2026-09-25
completed:
---
# DISC-011 — Spike: assisted import of Yahoo pages (league settings, roster, matchup schedule)

## Objective
Using sample screenshots/pastes provided by the owner, test extraction of league settings (format, categories/modifiers, roster slots, limits, playoffs), all team rosters, and the matchup schedule into validated structures. Recommend a parser vs LLM-extraction approach, with a confirmation step.

## Context to read (only these)
- docs/research/yahoo-api.md
- docs/architecture/adr/0025-yahoo-api-closed-assisted-import.md

## Acceptance criteria
- [ ] AC1: The owner provides samples: the league settings page, one roster page (or the league rosters), and the matchup schedule (screenshot or paste)
      Verify: files under docs/research/samples/yahoo/ (pseudonymised; not committed if they contain other managers' names)
- [ ] AC2: Extraction accuracy on the samples is measured field by field (settings 100 % correct; roster names mapped to NBA player IDs)
      Verify: docs/research/yahoo-api.md §assisted import
- [ ] AC3: Recommendation recorded: paste parsing vs LLM extraction from screenshots, the confirmation UX, and the cost per import
      Verify: same

## Test requirements
Per the testing standard.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
Needs the owner's sample pages. It replaces the API-based discovery (DISC-002).

Blocked 2026-09-27 (owner): no rosters exist until the draft (Sun 18 Oct 2026), and Yahoo hasn't released the matchup schedule. League settings are already imported (yahoo-api.md). Resume after the draft: the owner pastes the league rosters page and, once released, the matchup schedule (text preferred over screenshots).

## Follow-ups
_None._
