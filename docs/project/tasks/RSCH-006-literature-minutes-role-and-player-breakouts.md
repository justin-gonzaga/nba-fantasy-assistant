---
id: RSCH-006
title: "Literature: predicting playing time/role changes and player improvement (breakouts)"
epic: EP-15 Draft assistant
phase: 1
component: research
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [RSCH-005]
areas: [docs/research/**]
standards: [ml, documentation]
assignee:
created: 2026-09-25
completed: 2026-09-25
---
# RSCH-006 — Literature: predicting playing time/role changes and player improvement (breakouts)

## Objective
Find and **verify** academic references (D-53) for:
1. predicting NBA (or other team-sport) playing time / minutes / role changes season to season
2. predicting player improvement or "breakout" seasons (development curves, early-career growth, the signal in per-minute efficiency at low minutes)
3. opportunity effects (teammate departures, trades, depth-chart changes) on playing time and production
4. evaluating rare-event / top-k predictions (precision@k, calibration of probabilities) where not already covered

Record the results in docs/research/lit-breakouts.md, using the same verification table as lit-draft-slice.md, and merge them into ml-literature-review.md as new R-xx IDs.

## Context to read (only these)
- docs/research/ml-literature-review.md (the access rule and existing R-70…R-83)
- docs/research/lit-draft-slice.md (format)

## Acceptance criteria
- [x] AC1: At least 6 candidate references across topics 1–3, each verified (DOI/URL resolves; title, authors, venue and year match) or marked not found
      Verify: docs/research/lit-breakouts.md verification table
- [x] AC2: Each verified reference has a one-line key result and a design note for DRAFT-007; gaps (no peer-reviewed support) are listed explicitly
      Verify: same file, "Gaps" section
- [x] AC3: New IDs merged into ml-literature-review.md with their statuses
      Verify: ml-literature-review.md §10

## Test requirements
Doc only.

## Evaluation requirements
n/a

## Evidence
| AC | Verify | Result |
|---|---|---|
| AC1 | `docs/research/lit-breakouts.md` table | 8 new IDs (R-84…R-91); 6 span topics 1–3 (R-84, R-85, R-86, R-87, R-88, R-91), 2 span topic 4 (R-89, R-90). All 8 verified at Abstract or Full-text level against a primary source (DOI/RePEc/IDEAS/publisher landing page); none marked "not found" this pass. 2 (R-86, R-87) read in full text; the other 6 are Abstract-level only (publisher pages returned HTTP 403/404/405, or the self-archived PDF for R-84 could not be parsed) and are flagged as not sufficient alone for a gated decision. |
| AC2 | `docs/research/lit-breakouts.md` "Key result" / "Supports design choice" columns + "Gaps" section | Every row has a one-line key result and a DRAFT-007 design note. "Gaps" section lists 4 explicit gaps: no dedicated NBA minutes/role-change forecasting model (topic 1), no dedicated NBA breakout-season classifier or peer-reviewed support for the low-minutes-efficiency latent-talent signal (topic 2), no individual-level coaching-change minutes study or empirical vacated-usage split (topic 3), no sport-specific precision@k/calibration application to breakout prediction (topic 4). |
| AC3 | `ml-literature-review.md` §10 | Added "## 10. Breakout references (R-84…; verified 2026-09-25)" with a summary table (ID / Topic / Status / Access) for R-84…R-91 and a gaps callout, placed before "## 8. Known gaps", matching the §9 pattern. |

## Implementation history
- 2026-09-25: the main session independently re-checked all 8 DOIs against the Crossref API: titles, authors and venues match. Campbell et al. (2013) and Kuehn and Rebessi (2022) show online-first years; the print issues are 2014 and 2023.
- 2026-09-25: Researched and verified 8 references (R-84…R-91) for minutes/role prediction, breakout/regression-to-mean, opportunity effects (trades, coaching changes, usage redistribution, team fit), and rare-event/top-k evaluation. Wrote `docs/research/lit-breakouts.md` and merged summary into `ml-literature-review.md` §10. Ran out of search turns before reading full text of 6 abstract-level entries or finding a dedicated NBA-specific breakout-classifier or minutes-forecasting paper; logged as explicit gaps and follow-ups rather than left unresearched. Status set to `review` for owner/reviewer sign-off before merge.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
