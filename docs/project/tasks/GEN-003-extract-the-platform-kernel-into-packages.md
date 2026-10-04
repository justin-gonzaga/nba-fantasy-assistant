---
id: GEN-003
title: "Extract the platform kernel, slice 1: store, time, jobs (dikit)"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [GEN-002]
areas: [packages/**, apps/pipeline/**, pyproject.toml, platform-manifest.yaml]
standards: [software-engineering, testing]
assignee:
created: 2026-09-27
completed: 2026-09-28
---
# GEN-003 — Extract the platform kernel, slice 1: store, time, jobs (dikit)

## Objective
Create the `dikit` kernel package (D-60) and move the purely domain-neutral foundations into it:
clock/as-of, errors, logging, the job runner, the raw snapshot store and the paced HTTP client, with
import-linter forbidding kernel -> domain imports. The rest of the kernel follows in GEN-006 (evaluate),
GEN-007 (methods) and GEN-008 (decide, settings/gamedate splits, backtest reproduction).

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml

## Acceptance criteria
- [x] AC1: `packages/dikit` exists and its source and tests contain no project terms
      Verify: packages/dikit/tests/test_neutral.py (a term grep over source and tests: 0 hits)
- [x] AC2: import-linter contract: dikit never imports fantasy_* packages
      Verify: `uv run lint-imports`
- [x] AC3: No behaviour change: the moved modules differ only in import paths, the error base-class name
      and neutral comments; the NBA client still sends browser headers; the full suite passes
      Verify: `just ci-local`; packages/ingest/tests/test_http.py

## Test requirements
TDD for new platform code; existing tests must pass unchanged.

## Evaluation requirements
None for this slice (no computation moved); backtest reproduction is GEN-008's AC.

## Plan (2026-09-28)
Slice 1 of the kernel extraction (one package `packages/dikit`, D-60). The reviewer flagged that
merging several slices under one task breaks one-task-one-PR, so later slices are sibling tasks
GEN-006, GEN-007 and GEN-008.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest packages/dikit/tests/test_neutral.py` | 2 passed; failed first on 3 comments; fault injection caught by the reviewer |
| AC2 | command | `uv run lint-imports` | 4 contracts kept, 0 broken (incl. "The dikit kernel never imports domain code") |
| AC3 | command | `just ci-local` | 348 passed, coverage 92.81 %; reviewer byte-diff: import paths, DikitError rename, 2 comments only |

## Implementation history
- 2026-09-28 slice 1: `git mv` of clock, errors (FantasyError -> DikitError), logging, jobs, snapshot and http + their
  tests into `packages/dikit`; 50 importers rewritten; `tests/test_neutral.py` scans kernel source and tests for
  project terms (failed first on 3 comments, then fixed); import-linter contract "dikit never imports domain code"
  (4 contracts kept); settings.py reclassified as mixed (it holds league/bot fields). `just ci-local`: 348 passed,
  coverage 92.81 %.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- GEN-006 (evaluate), GEN-007 (methods), GEN-008 (decide + splits + backtest reproduction).
