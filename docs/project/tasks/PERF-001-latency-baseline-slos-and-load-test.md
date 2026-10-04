---
id: PERF-001
title: "Latency baseline, SLOs and a repeatable load test for the API and web app"
epic: EP-70 Dashboard
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-33
depends_on: [APP-009]
areas: [apps/api/**, apps/web/**, tools/**, docs/evaluation/**, justfile, .github/**]
standards: [backend, testing, performance]
assignee:
created: 2026-10-04
completed:
---
# PERF-001 — Measure before optimising

## Objective
The owner (2026-10-04): "improve latency and scalability so eventually multiple users can interact with the site at
once." Nothing has been measured. Establish the **baseline** (how fast is it now, for one user and for N), the
**service-level objectives** to hold it to, and a **repeatable load test** that PERF-002 and DRAFT-018 are judged by.
Costs (min instances, load-test tooling) are decision D-71 / gate G-33.

## Context to read (only these)
- D-71, `docs/architecture/` deployment section (Cloud Run settings), `apps/api` app factory and routes
- `apps/web` build config, `firebase.json` hosting headers, the persona e2e setup

## What is measured
| Layer | Measures | Where |
|---|---|---|
| Web | LCP, INP, CLS, JS transferred, requests per page load, TTI on a throttled phone profile (4× CPU, Fast 3G) | Lighthouse CI against the deployed dev site (`/`, `/today`, `/players`, `/draft`, `/practice`) |
| API | p50/p95/p99 latency and error rate per route; cold-start time; instance count and CPU/memory under load | load test against dev, plus Cloud Run metrics |
| Data | bytes and parse time of the serve files (`/players`, board, replay) | script reading the serve root |
| Store | Firestore reads/writes per request for `/me/*` | counted in tests with a counting store |

## Proposed SLOs (the owner confirms in G-33)
Per-route, on warm instances, with 25 concurrent users: p95 ≤ 300 ms for reads of published files; p95 ≤ 500 ms for
`/me/*`; error rate < 0.5 %; cold start ≤ 3 s for the first request; web LCP ≤ 2.5 s and INP ≤ 200 ms on the
throttled phone profile; JS for the draft route ≤ 250 KB gzip. Numbers are targets to be **replaced by measured
baseline + a justified margin** before PERF-002 starts.

## User stories and edge cases
| Situation | Expected |
|---|---|
| Owner alone, phone on mobile data | pages usable within the web SLO |
| 25 friends join on draft night | latency and error SLOs hold; no 5xx |
| Cold instance after idle | first request within the cold budget, or the min-instance decision (D-71) covers it |
| A load run against production | forbidden: the tool refuses any host other than the dev project |
| A run costs money | each run is capped (duration, request count) and prints the estimated cost first |
| Noisy results | each scenario repeats 3 times and reports the median and spread; a regression gate uses the median |

## Acceptance criteria
- [ ] AC1: `just load-test --scenario <name>` runs a scripted scenario (read-mix, settings write-mix, practice-draft
      session) against the dev project with a ramp to N virtual users, a hard cap on duration and requests, and prints
      p50/p95/p99 and the error rate per route; refuses non-dev hosts.
      Verify: `uv run pytest -q tools/tests/test_load_test.py` (host guard, caps, report maths on a fake server) and
      one real run recorded under AC3
- [ ] AC2: Lighthouse CI (or the equivalent headless run) records the web metrics for the five pages on the throttled
      profile and stores the JSON.
      Verify: `just web-perf` writes `docs/evaluation/reports/perf-web-<date>.json`
- [ ] AC3: the baseline report states current numbers for every row in "What is measured" (API rows at 1, 10 and 25 virtual
      users; web rows once per page on the throttled profile; Firestore rows as counts per request), the instance configuration used, the estimated cost of the run, and a table "SLO proposed vs measured".
      Verify: `docs/evaluation/reports/perf-baseline.md` exists with all three load levels and the table
- [ ] AC4: the top three bottlenecks are identified from the data (not guessed), each with the evidence row and a
      proposed fix mapped to a PERF-002 item.
      Verify: `perf-baseline.md` § Bottlenecks references measured rows
- [ ] AC5: a regression guard: `just perf-check` compares a fresh short run to the stored baseline and fails if a
      route's p95 is worse by more than the agreed margin; wired as a non-blocking CI job for the dev deploy.
      Verify: `uv run pytest -q tools/tests/test_perf_check.py`; the CI job file exists and passes on a no-change run

## Test requirements
Unit tests for the report maths, host guard, caps and comparison; the real runs are evidence, not tests. No
secrets in the scenario files; `/me/*` scenarios need a dev identity: use the existing test-auth mechanism if the dev API has one, else run those
scenarios against a local API with the in-memory store and say so in the report. Creating a real dev credential is an
owner step (nothing is invented here).

## Evaluation requirements
Report with medians of 3 runs per scenario and the spread.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified. Needs G-33 (tool choice and the cost of runs and min instances).

## Decisions
- Pending D-71: load tool (k6 vs Locust vs a small asyncio script), where it runs (local vs a Cloud Run job).
  Recommendation: a small asyncio + httpx script in `tools/`, no new service, within the Python stack, free.

## Known issues
- Lighthouse CI is a new dev tool and the CI job is new workflow YAML (Tier B): both are part of the D-71 decision (Q2).
- Dev project quotas and the free tier bound how high N can go; the report states the ceiling reached.

## Follow-ups
- PERF-002 acts on AC4.
