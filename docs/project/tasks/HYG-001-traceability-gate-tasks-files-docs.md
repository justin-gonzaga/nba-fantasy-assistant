---
id: HYG-001
title: "Traceability gate: every task has files, every file a task, every doc a link"
epic: EP-10 Foundation
phase: 7
component: infra
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: []
areas: [tools/trace_check.py, tools/tests/test_trace_check.py, tools/tasks.py, tools/tests/test_tasks_cli.py, .github/workflows/ci.yml, justfile, platform-manifest.yaml, docs/standards/software-engineering.md]
standards: [software-engineering, devops, testing]
assignee:
created: 2026-10-04
completed:
---
# HYG-001 — Keep the whole project tracked: no orphans, no duplicate ownership

## Objective
Courtside is about to gain a large new surface (accounts, leagues, auth, data handling). The owner asked that the
harness keeps tracking the whole project so that nothing is left orphaned or owned twice. Today the harness checks that
every file has a layer (`manifest_check.py`) and that packages respect their layering (`lint-imports`), but nothing finds
**tasks with no code, code that no task explains, documents nobody links, or two tasks claiming the same file**. This
task adds that check (`tools/trace_check.py`, stdlib only) to `just check` and CI. Unused code and copy-paste detection
need third-party tools and an owner decision, so they are HYG-002.

## Context to read (only these)
- `docs/agents/agent-architecture.md` §4 (the workflow) and `docs/standards/software-engineering.md`
- `tools/manifest_check.py` (the model for a small stdlib check), `tools/tasks.py`, `justfile`, `.github/workflows/ci.yml`

## The check
`tools/trace_check.py` reports, with file and task named:
1. every `done` or `in_progress` task's `areas:` globs match at least one tracked file;
2. every tracked source file under `packages/`, `apps/`, `warehouse/`, `infra/` is covered by the `areas:` of at least one
   task (an orphan has no spec), with an allow-list for scaffolding, each entry with a reason;
3. every `docs/**` file is linked from at least one other doc or the task index (an unreferenced document is an orphan);
4. no two tasks claim the same non-glob file as an `areas:` entry (duplicate ownership);
5. every `depends_on` and `gate` named in a task exists (already in `tasks.py validate`; the trace check reuses it).

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Claude finishing a task | "the gate tells me what I left behind" | the message names file, line and the task to fix; a clear exit code; no output when clean |
| Owner reviewing a PR | "I can trust the check, not read the diff for leftovers" | false positives go in the allow-list with a reason, never by weakening the rule |
| A refactor moves a file | "the trace follows" | a path covered by a glob is accepted; a renamed file shows as a new orphan until the task's `areas:` is updated |
| Spec-only tasks (`ready: false` or `todo`) | not nagged | rule 1 applies to `done` and `in_progress` tasks only |
| Offline or CI cold start | works | stdlib only, no network |

## Acceptance criteria
- [ ] AC1: `just check` runs the trace check and `ci.yml` runs it as a named step; a seeded task with no matching file,
      a seeded source file outside every task, an unreferenced doc and a duplicate single-file claim each fail the
      right rule.
      Verify: `uv run pytest -q tools/tests/test_trace_check.py` (temp git repo with seeded defects) and `just check`
      exits 0 on a clean tree
- [ ] AC2: the repository passes today: every existing finding is fixed (link the doc, widen a task's `areas:`) or
      allow-listed with a one-line reason; the number of allow-list entries is printed.
      Verify: `just check` exits 0 on this branch; the PR body lists findings fixed versus allow-listed
- [ ] AC3: `tools/tasks.py done` refuses a task whose `areas:` match no file or whose changed files fall outside its
      `areas:` (the "scope grew" rule in `CLAUDE.md` §7.4 becomes a check).
      Verify: `uv run pytest -q tools/tests/test_tasks_cli.py -k "areas"`
- [ ] AC4: `platform-manifest.yaml` classifies every new file (harness), and `docs/standards/software-engineering.md`
      gains one short paragraph "every file has a task, every doc is linked, no dead code or copies" pointing at the
      checks (HYG-002 for the last two). `CLAUDE.md` is not lengthened.
      Verify: `uv run python tools/manifest_check.py` exits 0; `python tools/tasks.py validate`

## Test requirements
Unit tests with a temp git repo for the trace check. No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified after the owner asked that the harness tracks the whole project (no duplicates, no orphans).
- 2026-10-04 — Narrowed in review: unused-code and copy-paste tooling split out to HYG-002 (needs a decision, S-41).

## Decisions
- A custom checker is used only for the project-specific part (tasks ↔ files ↔ docs).

## Known issues
_None._

## Follow-ups
- HYG-002 adds the dead-code and duplication tools.
- Run the check on each new task spec in the accounts slice (APP-012..027, WEB-030..038) before it is claimed.
