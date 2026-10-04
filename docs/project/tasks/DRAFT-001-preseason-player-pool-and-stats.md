---
id: DRAFT-001
title: "Preseason player pool + last 3 seasons of stats (local download)"
epic: EP-15 Draft assistant
phase: 1
component: draft
status: done
ready: true
size: S
autonomy: auto
gate: G-22
depends_on: [FND-007, DISC-003, DATA-027]
areas: [packages/models/**, packages/ingest/**, apps/pipeline/**]
standards: [ml, testing]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DRAFT-001 — Preseason player pool + last 3 seasons of stats (local download)

## Objective
Download from the home IP, as immutable raw snapshots (data-pipeline-design §1 S1–S4; D-49 Q4):
- `LeagueGameLog` player (P) and team (T) logs, seasons 2015-16 … 2025-26
- `LeagueDashPlayerStats` season totals (includes AGE), same seasons
- `CommonTeamRoster` × 30 teams for 2026-27
- `DraftHistory` (all years: 2026 draftees + the history for rookie priors)

Built on the approved thin ingestion stack (httpx + tenacity + fsspec snapshot store; technology-evaluation §ingestion), shaped so DATA-001/002 can harden it rather than replace it.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-42 (draft assistant)
- `docs/research/ml-literature-review.md` R-01, R-02, R-11, R-13

## Acceptance criteria
- [x] AC1: Game logs + season stats for 2015-16…2025-26, 2026-27 rosters and draft history are stored as raw snapshots with `observed_at` and a manifest row each
      Verify: `uv run pytest packages/ingest/tests/test_draft_pool.py` (fixture-based) + a manifest row count recorded
- [x] AC2: Every rostered 2026-27 player has either at least 1 season of NBA stats or a rookie/draft record
      Verify: coverage check command → 100 %, and the list of exceptions (two-way/undrafted) is recorded
- [x] AC3: Pacing is at least 0.6 s/request and the download is resumable
      Verify: test_rate_limiter + an interrupt/resume run logged

## Test requirements
Unit tests with fixtures (no network). Property tests where noted. TDD for the package code.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests + live run | `uv run pytest packages/ingest/tests/test_draft_pool.py test_snapshot.py` (fixture-based) pass; live `python -m fantasy_pipeline draft-pool --root data` → 64 snapshots (11 seasons × P/T logs + season totals, 30 rosters, draft history), 322,572 rows in the manifest sidecars; mirrored to `gs://nbafa-hdfo-dev-raw/raw/nba_stats` (128 objects = payload + meta) | ✅ |
| AC2 | coverage command | `python -m fantasy_pipeline draft-pool-coverage --root data` → rostered=589, missing=48, **all 48 EXP=R undrafted free-agent rookies** (camp/two-way signings; no draft record by definition). Coverage of everyone else = 100 % | ✅ (48 documented exceptions) |
| AC3 | tests + live interrupt | `test_http.py` (0.6 s floor enforced, pacing via fake clock, retries on 5xx/429/timeouts only); live: run killed after 9/64 snapshots, rerun → `fetched=55 skipped=9` | ✅ |
| Checks | just ci-local | 128 passed, coverage 99.88 % (floor 85 %) | ✅ |

## Implementation history
- 2026-09-25 plan:
  1. `fantasy_ingest.snapshot.SnapshotStore` (fsspec root; write-once; JSONL manifest; `has()` for resume)
  2. `fantasy_ingest.http.PacedClient` (browser headers, ≥ 0.6 s min interval via an injected clock/sleep, tenacity retries on timeouts/5xx/429)
  3. `fantasy_ingest.nba_stats` request specs for the 4 endpoints
  4. `fantasy_ingest.draft_pool`: plan → skip-existing → fetch → store; plus the coverage check
  5. `python -m fantasy_pipeline draft-pool` CLI
  6. live run to `data/` (local) then copy to `gs://nbafa-hdfo-dev-raw`
- 2026-09-25: built 1–5 test-first. Live run found `leaguedashplayerstats` returns HTTP 500 when unset filters are sent as the literal "None" the API echoes; fixed to empty strings + regression test. Interrupt/resume verified live. Core logging now resolves stdout per call (a closed test stream broke later tests).

## Decisions
_None yet._

## Known issues
- The dev raw bucket expires objects after 30 days (I3). Re-running the backfill is cheap (~2 min); prod raw ingestion comes with the Cloud Run jobs (INFRA-004).
- Undrafted rookies (48) have no prior: DRAFT-002 treats them as a league-minimum rookie prior, flagged low confidence.

## Follow-ups
_None._
