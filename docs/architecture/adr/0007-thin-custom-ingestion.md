# ADR-0007: Thin custom ingestion framework

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-00
- **Related**: `technology-evaluation.md` §3, ADR-0005

## Context
There are four sources, and immutable raw capture with `observed_at` is the core requirement. The Yahoo payloads are deeply nested, and the injury reports are PDFs.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. Own `Source` protocol + httpx + tenacity + Pydantic contracts + `SnapshotStore`** | Exact control of raw snapshots; small (about 400 LOC) | We maintain it |
| B. dlt | Schema inference, incremental state | Normalises away raw payloads by default; a second state model |
| C. Use yfpy / nba_api objects directly | Fast start | Parsed objects instead of raw payloads; library coupling |

## Decision
Option A. `nba_api` is used only for stats.nba.com request mechanics (headers/endpoints), and `yfpy` only as a reference during spikes.

## Consequences
- Every source is swappable behind `Source`. For example, the BALLDONTLIE fallback plugs in without affecting downstream code.

## Revisit triggers
More than 8 sources, or a need for connectors we'd otherwise hand-write.

## Amendment (2026-09-24, before acceptance)
Writes go to GCS via the storage abstraction; the pseudonymiser runs before the write; pre-NBA league sources are added later (Phase 9).
