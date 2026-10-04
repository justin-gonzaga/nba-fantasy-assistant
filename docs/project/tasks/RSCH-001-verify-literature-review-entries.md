---
id: RSCH-001
title: "Verify literature review entries"
epic: EP-02 Research
phase: 0
component: docs
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: []
areas: [docs/research/**]
standards: [ml]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# RSCH-001 — Verify literature review entries

## Objective
Confirm bibliographic details and applicability of each [R-xx]; clear '(to read)' flags.

## Context to read (only these)
- `docs/research/ml-literature-review.md`

## Acceptance criteria
- [x] AC1: Every entry R-01…R-66 is checked against a primary source (DOI / arXiv / publisher / JSTOR page, URL + access date), and its status is set to **Verified**, **Corrected** (details fixed), or **Not found** (removed + citations updated).
      Verify: docs/research/lit-verification-*.md tables (one row per entry)
- [x] AC2: Each Verified entry has a 2–3 sentence summary of its key result, the claim we rely on, a support rating (supports / partially / does not support), and the access level (full text / abstract only).
      Verify: the same tables
- [x] AC3: `ml-literature-review.md` is updated: "(to read)" flags are removed only for Verified entries, and corrections are applied.
      Verify: `grep -c "to read"` shows only the entries not yet verifiable
- [x] AC4: Any claim in the ML design that the source does *not* support is flagged for RSCH-004.
      Verify: the "Flags for the plan" list in the verification files

## Test requirements
n/a (research). Reproducibility: every row carries a URL.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | report | docs/research/lit-verification-part-a.md (18 entries), lit-verification-part-b.md (22 entries); each row has a primary-source URL and access date | 40/40 found: 36 Verified, 4 Corrected (R-01 title, R-43 pages, R-61 chapter caveat, R-66 subtitle), 0 Not found |
| AC2 | report | same files: key result, claim relied on, support rating, access level | all support their use; R-16 partially (soccer cohort); access level recorded (22 abstract-only) |
| AC3 | command | `grep -c "to read" docs/research/ml-literature-review.md` → 0; new "Verification status" table + corrections applied | done |
| AC4 | report | "Flags for the plan" sections in both files (R-04 NHL example, R-15 proxy not chemistry, R-16 partial, R-61 chapter, abstract-only list) | flagged for RSCH-004 |

## Implementation history
### 2026-09-25 — owner mandate (verified literature before any ML)
- Two researcher subagents ran in parallel (R-01…R-31; R-40…R-66), each writing its own verification file. Many publisher sites return 403 to automated fetches, so the citations were cross-checked against a second independent index, and the access level was recorded honestly.
- Merged into ml-literature-review.md with an access rule: abstract-only entries can't be the sole basis for a G-19 decision without a full-text read.
- Reviewer: PASS (cross-document consistency on 5 entries; the corrections were confirmed applied). Minor: the R-01 lead title was swapped to the current one, and the areas were widened.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
