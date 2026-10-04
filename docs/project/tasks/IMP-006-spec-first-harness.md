---
id: IMP-006
title: "Spec-first harness: user stories and edge cases in task specs"
epic: EP-10 Foundation
phase: 7
component: harness
status: in_progress
ready: true
size: S
autonomy: review
gate: none
depends_on: []
areas: [tools/tasks.py, tools/tests/**, docs/project/tasks/README.md, docs/project/tasks/_template.md, .claude/skills/**, CLAUDE.md]
standards: [testing]
assignee: claude
created: 2026-10-02
completed:
---
# IMP-006 — Spec-first harness

## Objective
The owner (2026-10-02): "we should be creating relevant tasks and specs and thinking through them before
implementation. and updating harness". WEB-005 code had started while its spec was a placeholder. Make spec-first the
default: user-facing specs carry user stories and edge cases, the validator checks it, and the skills say what to do
when scope is added mid-task.

## Context to read (only these)
- `docs/project/tasks/README.md` (T1–T4), `tools/tasks.py` `spec_issues`

## Acceptance criteria
- [ ] AC1: `tasks.py validate` warns when a ready, unfinished `web`/`api` task lacks `## User stories and edge cases`,
      errors at `review`, and ignores internal or done tasks.
      Verify: `uv run pytest -q tools/tests/test_tasks_cli.py` → 53 passed (5 new)
- [ ] AC2: the template, the README standard (new T5), `/new-task`, `/work-task` and CLAUDE.md §4 describe the
      section and the "scope added mid-task → spec first" rule.
      Verify: `git diff origin/main -- docs/project/tasks/_template.md docs/project/tasks/README.md .claude/skills CLAUDE.md`
- [ ] AC3: the current backlog validates with 0 errors.
      Verify: `python tools/tasks.py validate` → 0 errors

## Test requirements
Unit tests on `spec_issues` with tmp task files (existing fixtures).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | tools/tests/test_tasks_cli.py::test_user_facing_task_without_stories_warns_then_errors_at_review[web,api], ::test_user_facing_task_with_stories_passes, ::test_stories_not_required_for_internal_or_finished_tasks[ingest-review,web-done] | 53 passed |
| AC2 | diff | template section; README T5 + section list; new-task step 4; work-task step 1; CLAUDE.md §4 step 2 | present |
| AC3 | command | `python tools/tasks.py validate` | 0 errors |

## Implementation history
- 2026-10-02 — TDD: 5 failing tests (2 failed before the change), then the rule in `spec_issues`. Docs and skills
  updated. Lessons: lesson 36.

## Decisions
- Only `web`/`api` components are "user-facing"; done tasks are grandfathered (no retro-specs).

## Known issues
_None._

## Follow-ups
_None._
