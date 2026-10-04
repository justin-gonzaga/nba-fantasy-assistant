---
id: FND-008
title: "`just ship` + branch policy hooks + PR template"
epic: EP-10 Foundation
phase: 1
component: tooling
status: todo
ready: true
size: S
autonomy: review
gate: G-11
depends_on: [FND-006]
areas: [tools/**, justfile, .github/pull_request_template.md, .githooks/**]
standards: [devops]
assignee:
created: 2026-09-24
completed:
---
# FND-008 — `just ship` + branch policy hooks + PR template

## Objective
Implement the merge path from git-workflow §4 and local protection from §6.

## Context to read (only these)
- `docs/standards/git-workflow.md §4, §6`

## Acceptance criteria
- [ ] AC1: `just ship` rebases, runs ci-local, pushes, opens PR, waits for checks, squash-merges only for Tier A (reads task autonomy)
- [ ] AC2: Refuses on failing checks, stale branch, or Tier B/C
- [ ] AC3: pre-push hook rejects direct push to main outside ship/release
- [ ] AC4: Demonstrated on a trivial docs task

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC (`| ACn | test / command / report / screenshot | exact reference | result |`)._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
