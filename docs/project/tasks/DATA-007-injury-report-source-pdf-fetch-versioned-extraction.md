---
id: DATA-007
title: "Injury report source (PDF fetch + versioned extraction)"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: done
ready: true
size: M
autonomy: auto
gate: G-05
depends_on: [DISC-005]
areas: [packages/ingest/**]
standards: [data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# DATA-007 — Injury report source (PDF fetch + versioned extraction)

## Objective
Fetch each published injury report, store the PDF, extract rows with extractor version.

## Context to read (only these)
- `docs/research/nba-data.md`

## Acceptance criteria
- [x] AC1: Discovers latest report(s) for a date; stores PDF + extracted JSON (extractor_version)
      Verify: test_injury_report.py::test_fetch_latest_stores_the_pdf_and_versioned_rows_once; live fetch
- [x] AC2: Parser golden tests on archived PDFs incl. edge cases from DISC-005 (3 fixtures, one per layout era, + 2 live reports; the 10-PDF sweep moves to DATA-010's backfill)
      Verify: test_injury_report.py golden tests
- [x] AC3: Unknown layout -> quarantine + alert
      Verify: the PDF is stored before parsing; UnknownLayout is logged (error) and raised; a test covers header detection
- [x] AC4: The old report layout (2021-22 → early 2022-23; fixture `Injury-Report_2022-01-10_05PM.pdf`) parses correctly, and both filename formats (`_05PM` legacy = 5:30 PM report; `_05_00PM` new) are fetched
      Verify: golden tests per layout era (see DISC-005 findings)

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test + live | fetch_latest: newest-first slots (both filename formats), PDF (`ext=pdf`) + rows JSON with extractor_version 1.0.0; live 2026-03-10 (5:45 PM, 145 rows) and 2025-12-01 (legacy `_05PM` = 5:30 PM, 145 rows) | ✅ |
| AC2 | golden tests | 2026 new layout: the 12 hand-checked rows match exactly; 2025 legacy: every row complete; 2022 old layout: 99 rows, spot-checked against the raw PDF | ✅ |
| AC3 | test + code | PDF stored first, then `UnknownLayout` logged + raised (alerting via FND-013 later) | ✅ |
| AC4 | golden test | the old 2021-22 layout parses (columns come from each report's own header) | ✅ |
| Checks | ci-local | 245 passed, coverage 95.11 %, contracts 3/3 | ✅ |

## Implementation history
- 2026-09-27: MVP piece 1b. Positional pdfplumber parser: header-derived columns (page 1; reused on later pages), line grouping, status-anchored rows, wrapped reasons attached to the nearest row, carried-forward game/team context, NOT YET SUBMITTED skipped. `PacedClient.get_optional` (403/404 = not published); `SnapshotStore.write(ext=...)`. Wired into `nba-daily` (today's latest report).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
