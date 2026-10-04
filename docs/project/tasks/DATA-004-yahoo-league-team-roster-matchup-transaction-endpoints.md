---
id: DATA-004
title: "Yahoo league/team/roster/matchup/transaction endpoints + contracts"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: blocked
ready: true
size: M
autonomy: auto
gate: G-04
depends_on: [DATA-003, DISC-002]
areas: [packages/ingest/**]
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
# DATA-004 — Yahoo league/team/roster/matchup/transaction endpoints + contracts

## Objective
Snapshot league settings, standings, scoreboard, all rosters, transactions into bronze.

## Context to read (only these)
- `docs/research/yahoo-api.md`

## Acceptance criteria
- [ ] AC1: Endpoints implemented with Pydantic contracts for consumed fields
- [ ] AC2: Contract tests on DISC-002 fixtures
- [ ] AC3: Pagination handled; one run snapshots whole league
- [ ] AC4: G-04 A2 implemented:
  - a versioned pseudonymiser runs before the bronze write (other managers' names become 'Team N'; GUIDs and emails become salted hashes; unused personal fields are dropped; the owner's team stays identified)
  - a test asserts that no real manager names or emails reach disk
  - `just purge-yahoo` deletes all Yahoo-derived data across bronze, silver and gold

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

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
