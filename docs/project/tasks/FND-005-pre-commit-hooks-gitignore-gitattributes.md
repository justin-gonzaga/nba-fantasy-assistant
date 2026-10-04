---
id: FND-005
title: "pre-commit hooks + gitignore/gitattributes"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [FND-002]
areas: [.pre-commit-config.yaml, .gitignore, .gitattributes]
standards: [security, python]
assignee:
created: 2026-09-24
completed: 2026-09-24
---
# FND-005 — pre-commit hooks + gitignore/gitattributes

## Objective
Block secrets and noise before commit.

## Context to read (only these)
- `docs/standards/security.md §1`

## Acceptance criteria
- [ ] AC1: `.pre-commit-config.yaml` runs ruff format + ruff check, gitleaks, end-of-file-fixer, trailing-whitespace, check-yaml, check-added-large-files and nbstripout; `pre-commit` is in the dev dependency group and `just setup` installs the git hook
      Verify: tools/tests/test_precommit.py (hook ids, dev dependency, `setup` recipe) + `uv run pre-commit run --all-files` → every hook Passed/Skipped, exit 0
- [ ] AC2: `.gitattributes` normalises text to LF (`* text=auto eol=lf`), keeps `*.ps1`/`*.bat`/`*.cmd` CRLF, and marks PDFs/images/archives binary
      Verify: tools/tests/test_precommit.py::test_gitattributes_rules + `git ls-files --eol` → every text file `i/lf`, PDFs `-text`; `git add --renormalize .` stages no content changes
- [ ] AC3: gitleaks rejects a realistic fake secret before it can be committed (demonstrated on a throwaway untracked file, then deleted)
      Verify: `uv run pre-commit run gitleaks --files <tmp file with fake AWS key>` → gitleaks Failed, exit 1, "leaks found"; output recorded in Evidence
- [ ] AC4: `just ci-local` stays green with the hooks and attributes in place
      Verify: `just ci-local` → exit 0, coverage ≥ 85 %

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test + command | tools/tests/test_precommit.py::test_precommit_runs_required_hooks, ::test_precommit_is_a_dev_dependency, ::test_setup_installs_the_git_hook; `uv run pre-commit run --all-files` | 3 passed; all 8 hooks Passed (nbstripout Skipped: no notebooks yet), exit 0 (pre-commit 4.6.2; pre-commit-hooks v6.0.0, gitleaks v8.30.0, nbstripout 0.9.1; ruff from uv.lock) |
| AC2 | test + command | tools/tests/test_precommit.py::test_gitattributes_rules; `git ls-files --eol`; `git add --renormalize .` | 1 passed; every text file `i/lf attr/text=auto eol=lf`, the 3 PDFs `-text`, only the empty `py.typed` files are `i/none`; renormalize staged no extra changes (the index was already LF, only CRLF working copies on Windows) |
| AC3 | command | staged an untracked `tmp_gitleaks_demo.py` holding a fake AWS key id + secret, `uv run pre-commit run gitleaks --files tmp_gitleaks_demo.py`, then `git rm --cached` + deleted | `Detect hardcoded secrets ... Failed`, exit 1, `leaks found: 2` (rules `aws-access-token` line 1, `generic-api-key` line 2, secrets REDACTED); file removed, never committed |
| AC4 | command | `just ci-local` | exit 0; ruff/mypy/lint-imports clean, 51 passed, validate 0 errors, coverage 100 % (gate 85 %) |

## Implementation history
### 2026-09-25 — agent session (worktree, branch `task/FND-005-precommit`)
- Refined the ACs (Verify lines; added AC4 for ci-local). Tests first: tools/tests/test_precommit.py (4 tests, red → green).
- Added `.pre-commit-config.yaml` (pre-commit-hooks, gitleaks, nbstripout, local `uv run --frozen ruff format/check --fix` hooks), `.gitattributes`, `pre-commit>=4.0` in the dev group, `uv run pre-commit install` in `just setup`. `pre-commit autoupdate` pinned the latest revs; gitleaks' golang hook bootstraps its own Go toolchain (no Go install needed).
- First `pre-commit run --all-files` fixed trailing whitespace / missing final newlines in ~110 task files (mostly empty `assignee: ` / `completed: ` front-matter values). It also appended newlines to JSON fixtures under `packages/ingest/tests/fixtures/`; reverted those and excluded that path from the two fixers so captured payloads stay byte-exact.
- Line endings: the index was already all-LF (`git ls-files --eol`: 283 `i/lf`); the CRLF warnings came from `core.autocrlf=true` working copies. With `eol=lf` Windows checkouts become LF from the next checkout; no content renormalisation was needed.
- Did **not** run `pre-commit install` from this worktree: git hooks are shared with the main checkout, which has no config yet on `main`, so an installed hook would block commits there. Run `just setup` after merging.
- Attempts: 1 (plus the fixture exclusion). Skills/agents: none. Human interventions: none.

## Decisions
- ruff runs as local `uv run` hooks rather than the ruff-pre-commit mirror, so the hook version always equals the locked ruff that CI uses.
- `check-added-large-files` limit 1024 KB (largest tracked file is well under; bronze data lives outside git).
- Areas touched beyond the list (justified): `justfile`, `pyproject.toml`, `uv.lock`, `tools/tests/test_precommit.py`, and the whitespace fixes in `docs/project/tasks/*.md`.

## Known issues
- The git hook is not yet installed on the owner's machine: run `just setup` once after merging.

## Follow-ups
_None._
