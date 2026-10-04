---
id: PERF-002
title: "Cut latency and make the API and web app safe for concurrent users"
epic: EP-70 Dashboard
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-33
depends_on: [PERF-001]
areas: [apps/api/**, apps/web/**, infra/terraform/**, firebase.json, tools/**, justfile, .github/**]
standards: [backend, frontend, testing, performance]
assignee:
created: 2026-10-04
completed:
---
# PERF-002 — Latency and concurrency work

## Objective
Act on the measured bottlenecks of PERF-001 so the SLOs hold at the agreed concurrency, without adding services or
spend beyond what D-71 approves. Scope is fixed *after* the baseline: the items below are the candidate list from
code reading, and only items that PERF-001 shows to matter get built (the rest are dropped with the evidence).

## Context to read (only these)
- `perf-baseline.md` (PERF-001), D-71, `apps/api` app factory, `apps/web` vite config, `firebase.json`

## Candidate items (to be confirmed or dropped by the baseline)
| # | Item | Why it might matter |
|---|---|---|
| 1 | HTTP caching for published files: `Cache-Control` + strong ETag/304 on the serve files, `immutable` on hashed assets, a short `max-age` with `stale-while-revalidate` for daily data | the same large files fetched on every visit |
| 2 | Compression: brotli/gzip for JSON and the web bundle (Firebase Hosting does it for static; check the API) | payload size on mobile |
| 3 | Payload shape: paginate / trim `/players`, drop unused fields, send the table columns only; a slim list endpoint plus a detail endpoint | parse time and memory on phones |
| 4 | Route-level code splitting of the draft room, replay and charts; preload the likely next route | JS to first paint |
| 5 | In-process caching of parsed serve files with version check, so each instance parses once | CPU per request |
| 6 | Cloud Run: concurrency per instance, CPU boost, min instances (cost: D-71), request timeout; keep the app async with no blocking calls in handlers | cold starts and queueing |
| 7 | Firestore: batch and cache `/me/*` reads, avoid read-modify-write races (already CAS), index review, bounded fan-out for sims | per-request store round trips |
| 8 | Client: TanStack Query `staleTime`, request de-duplication, abort on navigation, no refetch on focus for static data | duplicate requests |
| 9 | Practice draft engine: run bot turns in a Web Worker or time-sliced so a 224-pick sim never blocks input (INP) | main-thread long tasks |
| 10 | Rate limiting and per-user quotas on write routes so one user cannot starve others | fairness under load |

## User stories and edge cases
| Situation | Expected |
|---|---|
| Returning visitor | the board loads from cache and revalidates; no full re-download when unchanged |
| New data published at 07:45 | clients see the new version within the stated freshness window; no mixed old/new within one page load (version in the URL or ETag) |
| 25 users, some editing settings | no lost update (CAS), no 5xx, p95 within SLO |
| One heavy user | rate limit returns 429 with `Retry-After`; others unaffected |
| Slow phone | no task > 100 ms in the draft room during a bot sim (long-task observer) |
| Cache poisoning / auth | `/me/*` and any user data are `private, no-store`; shared caches only hold public files |
| Rollback | each item behind a config value or an independent commit so it can be reverted alone |

## Acceptance criteria
- [ ] AC1: a scope table in the task lists each candidate as "do" or "drop" with the PERF-001 evidence row; only "do"
      items below are built.
      Verify: the table in this file's Plan references rows of `perf-baseline.md`
- [ ] AC2: caching headers: published files return a strong ETag and honour `If-None-Match` (304); user routes are
      `private, no-store`; hashed assets are `immutable`.
      Verify: `uv run pytest -q apps/api/tests/test_http_cache.py`; `curl -I` output for three URLs pasted in Evidence
- [ ] AC3: every "do" item has a before/after measurement with the same PERF-001 scenario, and every touched SLO row
      meets its target at 25 virtual users (or the report states the gap and the owner's decision).
      Verify: `docs/evaluation/reports/perf-after.md` table "baseline vs after vs SLO"
- [ ] AC4: concurrency correctness: a test fires 50 parallel writes at one settings document and at the draft-settings document (APP-011); the
      final state equals one valid serial order, no 5xx, losers get 412 (never silently lost).
      Verify: `uv run pytest -q apps/api/tests/test_concurrency.py` (memory store) and the CI emulator job
- [ ] AC5: if item 9 is built: no long task over 100 ms during a seeded full bot draft on the throttled profile.
      Verify: e2e `draft-perf.spec.ts` (PerformanceObserver `longtask` count and max); else n/a with the baseline
      evidence that it was not needed
- [ ] AC6: bundle budgets are enforced: the draft route chunk and the entry chunk stay under the sizes set in the
      scope table, checked in CI.
      Verify: `just web build` then `node apps/web/scripts/check-chunk-size.mjs` fails when a chunk grows past its budget (unit test
      of the checker; shared with DRAFT-020)
- [ ] AC7: rate limiting returns 429 with `Retry-After`, per user and per instance (a global limit across Cloud Run instances would need shared state, which this task
      does not add), and the limits are config values.
      Verify: `uv run pytest -q apps/api/tests/test_rate_limit.py`
- [ ] AC8: no regression: all existing API tests and web tests and the persona e2e pass.
      Verify: `just ci-local` (Python) and `just web test` plus `just web-e2e` (web)

## Test requirements
Unit tests for headers, rate limit and the checker; concurrency tests against both stores; before/after load runs
as evidence. Terraform changes only plan/validate here; apply happens through CI (dev) as always.

## Evaluation requirements
The before/after table with medians of three runs.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified. Waits on PERF-001 and G-33. Not on the critical path for 18 Oct.

## Decisions
- Measure first, then build only what the data supports (no speculative caching layers, no new services such as Redis
  or a CDN beyond Firebase Hosting unless the baseline demands it and D-71 approves the cost).

## Known issues
_None._

## Follow-ups
- A shared cache service or multi-region only if the user base outgrows a single region.
