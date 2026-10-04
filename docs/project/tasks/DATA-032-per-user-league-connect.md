---
id: DATA-032
title: "A member connects their own Yahoo league (per-user OAuth, league-keyed runs)"
epic: EP-20 Ingestion
phase: 8
component: ingest
status: todo
ready: false
size: M
autonomy: gated
gate: G-25
depends_on: [APP-008, APP-009]
areas: [packages/ingest/**, apps/pipeline/**, apps/api/**, infra/terraform/**]
standards: [data-engineering, security]
assignee:
created: 2026-10-02
completed:
---
# DATA-032 — Per-user league connection

## Objective
D-31's second half: a member connects their own Yahoo account (OAuth tokens per user in Secret Manager), and the
daily chain runs per league, with every output keyed by league, so each user's pages show their own league.
Placeholder: split into S/M slices and refine when APP-008/009 are done (likely: OAuth connect flow; league-keyed
paths in the workspace root; a per-league fan-out in the cloud job; API reads scoped to the user's league).

## Acceptance criteria
_To be refined (ready: false)._

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-02 — Placeholder from D-64 (Q3a: second user's own league comes after identity + settings).

## Decisions
_None yet._

## Known issues
- Yahoo's developer terms for multi-user personal apps need checking before build (see `commercial-view.md`).

## Follow-ups
_None._
