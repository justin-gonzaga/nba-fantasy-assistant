---
id: BRAND-002
title: "Rename the GitHub repository to courtside and update every pointer"
epic: EP-70 Dashboard
phase: 7
component: infra
status: todo
ready: true
size: S
autonomy: gated
gate: G-35
depends_on: [BRAND-001, BRAND-003]
areas: [README.md, docs/**, .github/**, pyproject.toml]
standards: [devops, documentation]
assignee:
created: 2026-10-04
completed:
---
# BRAND-002 — Rename the repository

## Objective
The repository, clone URL and local folder still say `nba-fantasy-assistant`. After BRAND-001 this is the last visible
trace of the old concept. A rename is a shared-state change (GitHub redirects the old URL, but clones, CI badges, the
public-repo audit and external links all point at it), so the owner does it, and this task fixes what the rename breaks.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-73
- `infra/terraform/bootstrap/wif.tf` (the trust uses `attribute.repository_id`, so the rename must not break CI auth)
- `docs/guides/local-development.md` (clone instructions)

## Human steps (owner)
1. GitHub: Settings → Rename repository → `courtside`.
2. Locally: `git remote set-url origin <new url>`; rename the working folder only between sessions (worktrees under
   `../nbafa-*` are git-linked and need `git worktree repair`).

## Acceptance criteria
- [ ] AC1: after the rename, the first CI run on a PR is green, including the WIF-authenticated jobs (proves the
      trust survived by repository id).
      Verify: the PR's checks on GitHub; `gh run list --limit 1` shows success
- [ ] AC2: docs, badges, the clone command and the `pyproject.toml` `[project] name` use the new name (the
      `USER_AGENT` text was done in BRAND-001); `uv.lock` is regenerated; `uv run pytest -q` passes.
      Verify: `uv lock --check` exits 0; `uv run pytest -q tools/tests/test_brand.py` passes with the allow-list shrunk by
      the old repository entries
- [ ] AC3: the old URL still redirects and no document links to a path that 404s.
      Verify: `gh api repos/<owner>/nba-fantasy-assistant --jq .full_name` returns the new name; link check from
      the docs task passes

## Test requirements
CI only. No code logic.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
_None yet._

## Known issues
- Renaming the Python distribution name regenerates the lock file; the import names (`fantasy_*`) stay.

## Follow-ups
_None._
