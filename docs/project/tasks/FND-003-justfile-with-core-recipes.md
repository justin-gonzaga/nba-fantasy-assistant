---
id: FND-003
title: "justfile with core recipes"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: review
gate: none
depends_on: [FND-002]
areas: [justfile]
standards: [devops]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# FND-003 — justfile with core recipes

## Objective
Single command surface: setup, check, ci-local, test, status, task, doctor.

## Context to read (only these)
- `docs/standards/devops.md §1`

## Acceptance criteria
- [x] AC1: The `justfile` provides the recipes `setup`, `check` (fast), `ci-local` (full: check + coverage), `test`, `status`, `task` (proxy to tasks.py), and `doctor` (presence-only).
      Verify: `just --list` shows all 7; each recipe runs and exits 0 on the current repo (`doctor` exits 1 only for owner-pending items)
- [x] AC2: The recipes behave identically when invoked from PowerShell, Git Bash, and Linux.
      Verify: `just check` from PowerShell and from Git Bash → exit 0; Linux: `just check` inside WSL Ubuntu (or the CI ubuntu job, if WSL isn't usable unattended) → exit 0
- [x] AC3: `just check` finishes in under 60 s on the current repo.
      Verify: measured wall time (Measure-Command) recorded in Evidence

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command + test | `just --list`; tools/tests/test_justfile.py::test_required_recipes_exist | 7 recipes listed; each exits 0 (`doctor` exits 1 only for the owner-pending Docker engine) |
| AC2 | command + test | `just check` from PowerShell, from Git Bash, and in WSL2 Ubuntu (clean clone of 611e23d; uv 0.12.18, just 1.58.0); test_recipes_are_shell_portable | exit 0 on all three (re-run independently by the reviewer) |
| AC3 | command | Measure-Command around `just check` / `just ci-local` | check 2.3 s; ci-local 3.3 s (Linux 6 s incl. setup) — well under 60 s |

## Implementation history
### 2026-09-25 — overnight session (loop)
- Refined the ACs (Verify lines). The justfile uses `windows-shell` = PowerShell, and recipes only call `uv`/`python`, so there's no shell-specific syntax.
- Verified on PowerShell, Git Bash, and Linux (WSL2 Ubuntu: installed uv + just in WSL, cloned with `-c safe.directory=*` because of Windows file ownership).
- Reviewer subagent: PASS. Acted on its suggestion by adding tools/tests/test_justfile.py (the recipe surface, shell portability, and the coverage gate in ci-local).
- Attempts: 2 (the first WSL run failed on git safe.directory; fixed). Interventions: none.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
