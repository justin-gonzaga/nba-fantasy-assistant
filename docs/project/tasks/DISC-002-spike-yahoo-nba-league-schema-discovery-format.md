---
id: DISC-002
title: "Spike: Yahoo NBA league schema discovery + format confirmation"
epic: EP-01 Discovery
phase: 0
component: ingest
status: blocked
ready: true
size: M
autonomy: auto
gate: G-02
depends_on: [DISC-001]
areas: [docs/research/**, packages/ingest/tests/fixtures/yahoo/** (scrubbed)]
standards: [data-engineering, security]
assignee:
created: 2026-09-24
completed:
---
# DISC-002 — Spike: Yahoo NBA league schema discovery + format confirmation

## Objective
Map every Yahoo resource we need for NBA and confirm the league's scoring format and rules.

## Context to read (only these)
- `docs/research/yahoo-api.md`
- `docs/specification/project-spec.md §5.2`

## Acceptance criteria
- [ ] AC1: Fetched (format=json) and saved scrubbed samples: game stat_categories, league settings, standings, scoreboard (current week), all team rosters, players (FA + waivers, with ownership), transactions, matchups (a completed week), player stats (date + week)
- [ ] AC2: NBA stat_id -> stat name/abbrev mapping table recorded
- [ ] AC3: League format, categories/modifiers, roster slots, lock cadence, acquisition/games limits, waiver type, playoff weeks recorded (A-01 validated or corrected)
- [ ] AC4: Prior-season league accessibility confirmed or refuted (A-04)
- [ ] AC5: docs/research/yahoo-api.md lists endpoints, pagination (count/start limits), and payload quirks
- [ ] AC6: Settings samples captured or synthesised for all 5 scoring formats (for FR-S4)

## Test requirements
Fixtures load as JSON; scrubber leaves no manager names/emails (grep check).

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
Blocked 2026-09-25: the Yahoo Fantasy API is closed to existing apps (ADR-0025). Resumes only if YAHOO-001 is approved; meanwhile DISC-011/DATA-026 (assisted import) replace it.

## Follow-ups
_None._
