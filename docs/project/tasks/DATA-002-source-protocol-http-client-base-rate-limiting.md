---
id: DATA-002
title: "Source protocol, HTTP client base, rate limiting, retries"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: [DATA-001]
areas: [packages/ingest/**]
standards: [data-engineering, testing]
assignee:
created: 2026-09-24
completed:
---
# DATA-002 — Source protocol, HTTP client base, rate limiting, retries

## Objective
Common machinery for all sources.

## Context to read (only these)
- `docs/standards/data-engineering.md §2, §8`

## Acceptance criteria
- [ ] AC1: Source protocol: fetch(request) -> RawPayload; requests canonicalised
- [ ] AC2: httpx client with per-source token-bucket limiter, tenacity backoff+jitter, Retry-After respected
- [ ] AC3: Contract validation hook -> quarantine on failure
- [ ] AC4: Tests with respx (no network)

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
