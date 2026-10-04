---
id: GEN-002
title: "Platform manifest with layers and lesson capture"
epic: EP-11 Platform generalisation
phase: 1
component: platform
status: done
ready: true
size: S
autonomy: review
gate: G-01
depends_on: [GEN-001]
areas: [platform-manifest.yaml, .claude/skills/work-task/**, docs/platform/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-27
completed: 2026-09-27
---
# GEN-002 — Platform manifest with layers and lesson capture

## Objective
Tag every asset as harness / platform / domain, and make capturing a lesson part of closing a task.

## Context to read (only these)
- docs/platform/generalisation-plan.md
- platform-manifest.yaml

## Acceptance criteria
- [x] AC1: platform-manifest.yaml becomes platform-manifest.yaml with harness, platform and domain sections covering every package, app, warehouse and infra path
      Verify: a script lists unclassified paths: 0
- [x] AC2: The /work-task close-out appends a lesson row to docs/platform/lessons.md (or records 'none')
      Verify: .claude/skills/work-task/SKILL.md step 8

## Test requirements
TDD for new platform code; existing tests and backtests must reproduce unchanged.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | script + test | `python tools/manifest_check.py --summary`: harness 56, platform 109, mixed 13, domain 333, unclassified 0; tools/tests/test_manifest_check.py (3); runs in `just check` and the CI docs job | ✅ |
| AC2 | skill | .claude/skills/work-task/SKILL.md step 7: the lessons row (or `Lessons: none`) + the manifest check; CLAUDE.md layers bullet | ✅ |

## Implementation history
- 2026-09-28: platform-manifest.yaml replaces harness-manifest.yaml (4 sections; 13 mixed files are GEN-003's split list). Lessons: the ledger already holds 24 rows; capture is now part of every task close.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
