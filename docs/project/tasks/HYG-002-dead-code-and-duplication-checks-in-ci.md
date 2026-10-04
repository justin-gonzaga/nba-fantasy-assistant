---
id: HYG-002
title: "Gate unused code and copy-pasted code in CI"
epic: EP-10 Foundation
phase: 7
component: infra
status: todo
ready: true
size: M
autonomy: gated
gate: G-35
depends_on: [HYG-001]
areas: [tools/hygiene*.py, tools/hygiene-baseline.json, tools/vulture_whitelist.py, tools/tests/test_hygiene.py, .github/workflows/ci.yml, justfile, pyproject.toml, apps/web/package.json, apps/web/knip.json, .jscpd.json]
standards: [software-engineering, devops, testing]
assignee:
created: 2026-10-04
completed:
---
# HYG-002 — No dead code, no copies

## Objective
The second half of the owner's request that nothing is duplicated or orphaned: find unused Python and TypeScript and
copy-pasted blocks, on every task. The tools add dependencies and a CI job, so the owner picks them first (S-41, asked in
G-35). This task does not start until that is answered.

## Context to read (only these)
- `docs/project/standards-decisions.md` S-41; HYG-001 (the traceability half)
- `justfile`, `.github/workflows/ci.yml`

## The checks (★ recommendation in S-41; the owner may change the tools)
1. **Dead Python**: `vulture` over `packages/` and `apps/`, a whitelist for framework entry points (FastAPI routes,
   Typer commands, pytest fixtures), confidence ≥ 80.
2. **Dead TypeScript**: `knip` for unused files, exports and dependencies in `apps/web`.
3. **Duplication**: `jscpd` over Python and TypeScript; generated files (`schema.gen.ts`, `openapi.json`) ignored; the
   baseline is recorded and the check fails on an increase.

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Claude finishing a task | "tell me what I left behind" | the message names file and line; no output when clean |
| New framework entry point | "a route is not dead" | the whitelist is checked so a route function is never reported |
| Generated or vendored code | "not my duplication" | the ignore list is explicit and tested |
| Cold CI | works | Python check offline; Node checks use the lock file |

## Acceptance criteria
- [ ] AC1: `just check` and `ci.yml` run the three checks as separate named steps; a seeded unused function, a seeded
      unused export and a seeded 30-line copy each fail the right check.
      Verify: `uv run pytest -q tools/tests/test_hygiene.py` (fixtures with seeded defects); `just check` exits 0 on a
      clean tree
- [ ] AC2: the repository passes today: each existing finding is fixed (delete the dead code) or allow-listed with a
      one-line reason; the counts are printed.
      Verify: `just check` exits 0; the PR body lists fixed versus allow-listed
- [ ] AC3: the duplication baseline is in `tools/hygiene-baseline.json` and the check fails when the percentage rises by
      more than 0.2 points.
      Verify: `uv run pytest -q tools/tests/test_hygiene.py -k baseline`

## Test requirements
Seeded-defect fixtures; the Node and vulture tools run in CI.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Split out of HYG-001 in review (new dependencies need an owner decision).

## Decisions
_Pending S-41._

## Known issues
_None._

## Follow-ups
_None._
