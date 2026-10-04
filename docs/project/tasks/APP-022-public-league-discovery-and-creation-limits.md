---
id: APP-022
title: "Public league discovery (search, filters, paging) and creation limits"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-014, APP-024]
areas: [apps/api/src/fantasy_api/leagues/discovery*.py, apps/api/src/fantasy_api/leagues/limits*.py, apps/api/tests/test_discovery.py, apps/api/tests/test_league_limits.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-022 — Discovery and limits

## Objective
The Leagues panel needs a list of public leagues people can find and join, and the platform needs limits so one
account cannot flood it. Spec: `docs/specification/leagues-and-accounts.md` §4 (discovery), §8, §10.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §4, §8, §10; APP-014's league service

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Visitor browsing | "I see open leagues" | only `public`, not `hidden`, `status: setup`; newest first, 20 per page, opaque cursor; a result of zero is a normal 200 |
| Searching | "find by name" | prefix search on `nameLower`; special characters are escaped; max 40 characters |
| Filtering | "only ones with room" | `format=` and `hasSpots=` filters combine with search without scanning private leagues |
| Private league | never exposed | never in results, counts or suggestions; cache never mixes viewers |
| Creating many leagues | "no spam" | 5 active leagues and 3 creates per day per account → 429 `league-limit`; the owner has higher caps; archived leagues don't count |
| Scale-out | consistent | the daily create counter is APP-024's shared counter (a table row), and the active-league count is a transactional read |
| Cost | bounded | 20 reads a page; response cached 30 s in process; the free read quota covers D-71's 25 concurrent users |

## Acceptance criteria
- [ ] AC1: `GET /leagues/public` is ordered newest first, cursor-paged (20), supports `q`, `format` and `hasSpots`, and
      excludes private, hidden and archived leagues.
      Verify: `uv run pytest -q apps/api/tests/test_discovery.py -k "paging or search or filters or excludes"`
- [ ] AC2: the 30 s cache never serves a private or hidden league and is keyed by query only (no per-user data in it).
      Verify: `uv run pytest -q apps/api/tests/test_discovery.py -k "cache"`
- [ ] AC3: limits (5 active, 3/day via a row in APP-024's table) are enforced under 20 concurrent creates (exactly the
      allowed number succeed); archived leagues do not count.
      Verify: `uv run pytest -q apps/api/tests/test_league_limits.py` plus the emulator job in CI
- [ ] AC4: the Firestore indexes the queries need (collection-group `members` by `uid`, public discovery) are listed in
      the code's index manifest; the emulator test fails if a query needs one that is not listed. INFRA-010 declares them.
      Verify: `uv run pytest -q apps/api/tests/test_discovery.py -k "index"`
- [ ] AC5: the league endpoints are added to the load script (PERF-001) with the D-71 targets noted; p95 ≤ 300 ms on the
      emulator-backed local run for discovery.
      Verify: `uv run python tools/load/run.py --scenario leagues --users 25` (or the PERF-001 equivalent) prints p95
- [ ] AC6: the client is regenerated with no diff.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Store contract tests; concurrency tests on the emulator; cache tests with a fake clock.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original APP-014).

## Decisions
_None yet._

## Known issues
- AC5 depends on PERF-001 existing; if it does not yet, the scenario is added there instead.

## Follow-ups
- A real search index only if discovery grows past a few thousand leagues.
