---
id: DISC-005
title: "Spike: official injury report ingestion"
epic: EP-01 Discovery
phase: 0
component: ingest
status: done
ready: true
size: S
autonomy: auto
gate: G-05
depends_on: []
areas: [docs/research/**]
standards: [data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# DISC-005 — Spike: official injury report ingestion

## Objective
Decide how to ingest official NBA injury reports (live + since 2021-22).

## Context to read (only these)
- `docs/research/2026-09-initial-research.md §2`

## Acceptance criteria
- [x] AC1: The report URL pattern and publication cadence are verified.
      Verify: docs/research/nba-data.md §DISC-005 (two filename formats, switch between Nov 2025 and Jan 2026)
- [x] AC2: The `nbainjuries` package is evaluated (licence, maintenance, output quality) against our own pdfplumber parser.
      Verify: same section (MIT; needs a JVM → rejected as a runtime dependency)
- [ ] AC3: 10 historical PDFs are parsed correctly, including multi-page/team-continuation edge cases. **Partially met: 9/12 (2023-05 → 2026-03) parse correctly; the 3 oldest (2022 → 2023-03) use an older layout, not solved within the 3-attempt cap → moved to DATA-007 AC.**
      Verify: prototype run + a spot-check of 12 rows against the PDF
- [x] AC4: The recommendation is recorded (dependency vs own parser).
      Verify: docs/research/nba-data.md §Recommendation

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | spike download of 12 dates, 2022–2026 (scratchpad) | legacy `_05PM` (= the 5:30 PM report) through Nov 2025; `_05_00PM` by Jan 2026; 403 for missing files |
| AC2 | command | `uv run --with nbainjuries` → import fails: JVMNotFoundException; metadata MIT v1.1.1 | rejected as a runtime dependency |
| AC3 | command | positional parser prototype v2 over 12 PDFs | **partial**: 9/12 OK (18–165 rows each, 0 missing reason/context); 3 old-layout PDFs → 0 rows (follow-up DATA-007) |
| AC4 | report | docs/research/nba-data.md | own parser recommended |

## Implementation history
### 2026-09-25 — overnight loop
- Attempt 1: line-regex parser → 0 rows (plain-text extraction drops spaces; reasons wrap around the player line).
- Attempt 2: positional parser → 0 rows (the header wasn't detected at tight word spacing).
- Attempt 3: header found with default spacing → 9/12 reports parse cleanly. **Stopped at the 3-attempt cap.** The old layout (2022–early 2023) is left for DATA-007.
- Closed as a spike with AC3 honestly marked partial. The decision the spike existed to make (own parser vs dependency) is made.
- Interventions: none.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- DATA-007 AC added: parse the 2021-22 → early 2022-23 old layout (fixture `Injury-Report_2022-01-10_05PM.pdf`).
