---
id: DATA-001
title: "Bronze SnapshotStore + manifest + quarantine"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: M
autonomy: auto
gate: G-00
depends_on: [FND-007, FND-010, ARCH-001, INFRA-002]
areas: [packages/ingest/**]
standards: [data-engineering, testing]
assignee:
created: 2026-09-24
completed:
---
# DATA-001 — Bronze SnapshotStore + manifest + quarantine

## Objective
Immutable raw payload storage with manifest rows and content-hash dedupe (ADR-0005).

## Context to read (only these)
- `docs/standards/data-engineering.md §1`
- `docs/architecture/adr/0005-immutable-snapshots-bitemporal.md`

## Acceptance criteria
- [ ] AC1: write(payload) stores gz JSON/PDF via the storage abstraction (local path in tests, `gs://…-raw-{env}` otherwise) under raw/{source}/{endpoint}/dt=/ and appends manifest row with all fields from data-engineering §1
- [ ] AC2: Identical content -> new manifest row, no new blob
- [ ] AC3: Quarantine path for contract failures with reason
- [ ] AC4: Never overwrites existing files (tested)
- [ ] AC5: The manifest is readable in BigQuery (external table over GCS), and the pseudonymisation hook runs before the write for Yahoo sources

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
_None._

## Follow-ups
_None._
