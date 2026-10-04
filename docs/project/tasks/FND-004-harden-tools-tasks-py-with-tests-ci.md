---
id: FND-004
title: "Harden tools/tasks.py with tests + CI validation"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [FND-002]
areas: [tools/**, tests/tools/**]
standards: [testing]
assignee:
created: 2026-09-24
completed: 2026-09-24
---
# FND-004 — Harden tools/tasks.py with tests + CI validation

## Objective
Make the task CLI trustworthy: unit tests for parsing, eligibility, cycle detection, claim/done.

## Context to read (only these)
- `docs/project/tasks/README.md`
- `tools/tasks.py`

## Acceptance criteria
- [ ] AC1: Tests on temporary task directories cover front-matter parsing, blockers (deps, gates, ready), eligibility ordering, cycle detection, claim conflict, and `done` (prints newly unblocked tasks; refuses without evidence); `tools/tasks.py` line+branch coverage ≥ 85 %
      Verify: `uv run pytest tools/tests/test_tasks_cli.py -q` → all pass; `uv run pytest tools --cov=tools --cov-branch --cov-report=term --cov-fail-under=0` → `tools\tasks.py` row ≥ 85 % (the repo-wide 85 % gate covers packages/apps only)
- [ ] AC2: `validate` runs in `just check` (and therefore `just ci-local`) and fails the recipe on errors
      Verify: tools/tests/test_tasks_cli.py::test_validate_is_wired_into_just_check + tools/tests/test_tasks_cli.py::test_validate_returns_nonzero_on_errors; `just check` → last line `N tasks, 0 errors, …`
- [ ] AC3: Board regeneration is deterministic: the same tasks in any file/insertion order produce byte-identical `BOARD.md`, phases ascending and IDs sorted within a phase
      Verify: tools/tests/test_tasks_cli.py::test_board_is_deterministic + ::test_board_orders_phases_and_ids

## Test requirements
pytest with temporary task directories.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test + command | `uv run pytest tools/tests/test_tasks_cli.py -q`; `uv run pytest tools --cov=tools --cov-branch --cov-report=term --cov-fail-under=0` | 48 passed; `tools\tasks.py` 308 stmts / 150 branches → **99 %** (missed: `main`'s unreachable `return 2`, the `__main__` guard, one loop branch) |
| AC2 | test + command | tools/tests/test_tasks_cli.py::test_validate_is_wired_into_just_check, ::test_validate_returns_nonzero_on_errors; `just check` | 2 passed; `just check` ends `uv run python tools/tasks.py validate` → `146 tasks, 0 errors, 149 warnings`; `just ci-local` exit 0 (95 passed, coverage gate 100 %) |
| AC3 | test | tools/tests/test_tasks_cli.py::test_board_is_deterministic, ::test_board_orders_phases_and_ids | 2 passed: byte-identical BOARD.md across file-creation and dict-insertion orders; phases ascending, IDs sorted |

## Implementation history
### 2026-09-25 — agent session (worktree, branch `task/FND-004-tasks-tests`)
- Refined the ACs (Verify lines, coverage threshold, `done` refusal).
- Wrote tools/tests/test_tasks_cli.py first (48 tests; a `repo` fixture monkeypatches `ROOT`/`TASK_DIR`/`GATES_FILE`/`BOARD_FILE` onto `tmp_path`).
- **Bug found by the tests**: `cmd_done` flipped the task to `done` in memory *before* snapshotting the eligible set, so "Newly unblocked" was always `none`. Fixed by taking the snapshot first (tools/tasks.py `cmd_done`).
- Commands: `uv run pytest tools/tests/test_tasks_cli.py -q` → 1 failed (the bug) then 48 passed; `just ci-local` → exit 0 after a `ruff format` and replacing a 6-arg parametrised test signature (PLR0917).
- Attempts: 3 ci-local runs (format, lint, green). Skills/agents: none. Human interventions: none.

## Decisions
- Kept tests stdlib+pytest only (no YAML/markdown libs), matching the stdlib-only CLI.

## Known issues
- `uv run pytest tools --cov=tools` without `--cov-fail-under=0` exits 1: the aggregate is 82 % because `tools/doctor.py` (0 %) and `tools/yahoo_login.py` (39 %) are barely tested. `tools/` is outside `[tool.coverage.run] source`, so `just ci-local` is unaffected.

## Follow-ups
- Consider a small task to test `tools/doctor.py` / `tools/yahoo_login.py` and add `tools` to the coverage source (not created; owner's call).
