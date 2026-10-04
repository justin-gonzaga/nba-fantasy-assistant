# ADR-0003: Local-first single node; hybrid production path

- **Status**: Superseded by ADR-0019 · **Date**: 2026-09-24 · **Gate**: G-06
- **Related**: `system-architecture.md` §6, research §2–3

## Context
- There is one user, the data is under 5 GB, and the cost target is at most US$10/month.
- stats.nba.com blocks datacenter IPs, which rules out cloud hosting for historical backfills.
- The owner wants mobile operation via Remote Control, which runs on the local machine anyway.

## Options considered
| Option | $/mo | Pros | Cons |
|---|---|---|---|
| A. Local only + Tailscale | 0 | Simplest; stats.nba.com works | Needs the laptop on at run times |
| B. Hybrid: VPS (compose) for daily jobs + API; local for stats.nba backfills | ~5 | Always on; same image | Small ops burden |
| C. Serverless (Cloud Run + GCS) | 0–3 | Scale to zero | DuckDB-on-object-storage awkwardness; more moving parts |

## Decision
- Phases 0–7 run **Option A** (local).
- Phase 8 moves to **Option B**, subject to G-06.
- All code is written so the move is only a change of config (`DATA_ROOT`, env vars) and image deployment.

## Consequences
- $0 until Phase 8.
- Missed runs while the laptop is off are handled by catch-up jobs.

## Revisit triggers
Missed daily recommendations more than twice a month → pull Option B forward.
