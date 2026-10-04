---
id: DATA-034
title: "Yahoo market prices: pre-draft average auction cost and % drafted"
epic: EP-20 Ingestion
phase: 6
component: ingest
status: todo
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [packages/ingest/**, apps/pipeline/**, warehouse/**]
standards: [data-engineering, security]
assignee:
created: 2026-10-02
completed:
---
# DATA-034 — Yahoo market prices

## Objective
WEB-020's Market indicator needs what other Yahoo drafters pay: Yahoo's pre-draft `draft_analysis` per player
(average auction cost, average pick, percent drafted), via the read-only OAuth already approved (G-03). Snapshot it
daily until the draft (raw, immutable), so the indicator shows the latest market and we can study price drift.

## Context to read (only these)
- `packages/ingest/src/fantasy_ingest/` Yahoo client and contracts; `docs/runbooks/` Yahoo auth
- Privacy rules (CLAUDE.md §3): market data is aggregate, no other managers' data

## User stories and edge cases
| Situation | Handling |
|---|---|
| Yahoo returns no auction data yet (early pre-season) | store the snapshot with nulls; indicator absent |
| A player missing from Yahoo's list | no market value; not an error |
| Name/ID mapping Yahoo → NBA id | the existing Yahoo↔NBA id map; unmapped players reported in the run log |
| OAuth token expired | the job fails loudly with the re-auth runbook step (owner action) |

## Acceptance criteria
- [ ] AC1: a contract-validated fetch of `players;out=draft_analysis` for the league's game key writes a raw snapshot.
      Verify: `packages/ingest/tests/test_yahoo_market.py` (recorded fixture → contract → snapshot)
- [ ] AC2: a staging/mart table `market_prices` (nba_player_id, avg_cost, avg_pick, pct_drafted, as_of) and a published
      `predictions/market_prices.parquet`.
      Verify: dbt test + `apps/pipeline/tests/test_publish.py::test_market_prices_published`
- [ ] AC3: ≥ 95 % of our top-200 by value map to a Yahoo market row on a real run (unmapped listed).
      Verify: run log line `market: mapped N/200`

## Test requirements
Recorded Yahoo fixture (no live calls in tests).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-02 — Specified for WEB-020's Market indicator.

## Decisions
_None yet._

## Known issues
- Needs the owner's Yahoo OAuth to be valid when run (owner action if it has expired).

## Follow-ups
_None._
