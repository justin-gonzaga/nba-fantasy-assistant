---
id: FND-002
title: "uv workspace skeleton + Python tooling config"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: review
gate: none
depends_on: [FND-001, STD-001, ARCH-001]
areas: [pyproject.toml, .python-version, packages/core/**, uv.lock]
standards: [python]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# FND-002 — uv workspace skeleton + Python tooling config

## Objective
Create the uv workspace with packages/core as first member and all lint/type/test config.

## Context to read (only these)
- `docs/standards/python.md`

## Acceptance criteria
- [x] AC1: The root `pyproject.toml` declares a uv workspace with members `packages/*` (and `apps/*` once apps exist), and `.python-version` pins 3.13.
      Verify: `uv sync` succeeds and `uv run python -c "import sys; print(sys.version)"` prints 3.13.x
- [x] AC2: `packages/core` uses the src layout (`fantasy_core`, typed via `py.typed`) and has a passing test.
      Verify: `uv run pytest packages/core -q` → 1+ passed
- [x] AC3: Ruff (rule set per python.md), mypy --strict, pytest (importlib mode) and coverage (fail_under 85) are configured in the root pyproject.
      Verify: `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, `uv run pytest --cov` → all exit 0, coverage ≥ 85 %
- [x] AC4: A clean clone reproduces all of the above.
      Verify: `git clone` into a temp dir → `uv sync --frozen` → pytest/ruff/mypy all pass; output recorded in Evidence

## Test requirements
The sample test itself; clean-clone check.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | `uv sync`; `uv run python -c "import sys; print(sys.version)"` (commit df1386c) | exit 0; 3.13.14 |
| AC2 | test | packages/core/tests/test_package.py::test_package_exposes_version | 1 passed |
| AC3 | command | `uv run ruff check .` / `ruff format --check .` / `mypy` / `pytest --cov` | all pass; mypy: no issues in 4 files; coverage 100 % (≥ 85) |
| AC4 | command | clean `git clone --branch task/FND-002-uv-workspace` → `uv sync --frozen` + full checks (also re-run independently by the reviewer) | all exit 0 |

## Implementation history
### 2026-09-25 — overnight session (loop)
- Refined the ACs to the task spec standard (Verify lines). TDD: wrote the failing import test first, then built the workspace.
- Root `pyproject.toml`: a virtual uv workspace (members `packages/*`; `apps/*` gets added when the first app exists, since uv rejects empty globs), plus ruff (the python.md rule set), mypy --strict, pytest importlib mode, and coverage fail_under 85. `packages/core`: uv_build src layout with `py.typed`.
- **Outside `areas:` (explained per DoD §1)**: `tools/tasks.py` and `tools/doctor.py` now fall under the repo-wide ruff/mypy scope, so they were fixed:
  - line lengths
  - typed `deps` accessor
  - renamed shadowed loop variables
  - `check=False` on subprocess
  - `cmd_done` completion date is now `datetime.now(UTC).date()` instead of the naive `date.today()` (DTZ rule). Behaviour change: near local midnight the recorded date may differ by a day from Sydney time. This is intentional (all stored timestamps are UTC).
- Reviewer subagent: PASS (3 minor notes, all addressed here). Attempts: 1 (plus one round of lint fixes). Interventions: none.

## Decisions
- `apps/*` is left out of the workspace members until the first app exists.
- Coverage is enforced via `pytest --cov` in `just check`/CI (FND-003), not in the default addopts, so quick local test runs stay fast.

## Known issues
_None._

## Follow-ups
_None._
