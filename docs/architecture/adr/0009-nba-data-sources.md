# ADR-0009: NBA data sources

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-05
- **Related**: research §2, spikes DISC-003/004/005

## Context
There is no official, free NBA stats API. The unofficial endpoints differ in how reachable they are:
- stats.nba.com blocks cloud IPs.
- cdn.nba.com reportedly works from anywhere.
- Official injury reports are public PDFs, with history back to 2021-22.

## Options considered
| Option | $/mo | Pros | Cons |
|---|---|---|---|
| **A. cdn.nba.com (schedule, box scores) + stats.nba.com via nba_api (history, run locally) + official injury PDFs** | 0 | Most complete; free | Unofficial; can change without notice |
| B. BALLDONTLIE ALL-STAR | 9.99 | Documented API; injuries included | Cost; less depth (no box scores or lineups below $39.99) |
| C. Basketball-Reference scraping | 0 | Deep history | 20 req/min limit; licensing; fragile |

## Decision
- Option A as the primary source, behind the `Source` protocol.
- Option B is a documented, pre-evaluated fallback, adopted only via a new gate if A breaks.
- C is rejected.

## Consequences
- Contract tests plus a monthly live contract check detect breakage early.
- Backfills are a local-only job.

## Revisit triggers
Any primary endpoint failing for more than 48 h, or a ToS change.

## Amendment (2026-09-24, before acceptance)
Owner decision: stay on free sources (G-05 A). MySportsFeeds (~$5/mo personal) and BALLDONTLIE are evaluated fallbacks (DISC-009).
