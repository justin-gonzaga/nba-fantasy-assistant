# ADR-0005: Immutable raw snapshots and a bitemporal point-in-time model

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-00 (retention aspect: G-04)
- **Related**: `[R-60]` (leakage by legitimacy), `[R-65]` (bitemporal modelling), data-engineering standard §1, §5

## Context
- Honest evaluation and replay require knowing **what was known when** (spec NFR4).
- Yahoo FA pools, ownership, and injury designations change over time, and the APIs expose only the current state. That history is lost unless we capture it ourselves.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. Append-only raw payloads with `observed_at` + SCD2 state tables + `AsOfReader(t)`** | Exact replay; leakage testable; rebuildable | More storage (still small: MBs/day) |
| B. Keep only the latest state (upserts) | Simple | Makes leakage-free backtests impossible |
| C. Event sourcing from diffs | Compact | Complex; fragile |

## Decision
Option A. Every read by features, models, decisions, or evaluation goes through `AsOfReader(t)`, which filters `observed_at <= t`, and a per-feature-view test enforces this.

## Consequences
- Replay is reproducible.
- Snapshot collection must start **before the 2026-10-20 tip-off**, because it cannot be backfilled.
- There is a retention tension with the Yahoo ToU (G-04).

## Revisit triggers
Storage grows beyond 20 GB (then compact duplicate-content payloads into Parquet), or G-04 forbids retention.

## Amendment (2026-09-24, before acceptance)
Yahoo payloads are **pseudonymised before the raw write** (G-04 A2): other managers → 'Team N', GUIDs → salted hashes. Raw storage is GCS (ADR-0020). `just purge-yahoo` deletes all Yahoo-derived data.
