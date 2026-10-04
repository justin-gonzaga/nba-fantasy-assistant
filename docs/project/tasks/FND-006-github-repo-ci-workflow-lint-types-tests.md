---
id: FND-006
title: "GitHub repo + CI workflow (lint, types, tests, docs checks)"
epic: EP-10 Foundation
phase: 1
component: ci
status: done
ready: true
size: M
autonomy: review
gate: G-01
depends_on: [FND-003, FND-005]
areas: [.github/**]
standards: [devops, security]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# FND-006 — GitHub repo + CI workflow (lint, types, tests, docs checks)

## Objective
Create the remote repo and CI that runs `just ci-local` equivalents on PRs and main.

## Context to read (only these)
- `docs/standards/devops.md §2`
- `docs/standards/git-workflow.md`

## Acceptance criteria
- [x] AC1: Private repo created per G-01; default branch main; remote pushed
      Verify: `gh api repos/justin-gonzaga/nba-fantasy-assistant` → private; default branch main
- [x] AC2: ci.yml: lint-type, test-py, docs (tasks validate), security (gitleaks, pip-audit), terraform (fmt + policy tests)
      Verify: .github/workflows/ci.yml
- [x] AC3: Actions pinned by SHA; least-privilege permissions
      Verify: ci.yml uses: lines pinned to SHAs; `permissions: contents: read`
- [x] AC4: PR template with DoD checklist; Dependabot config (weekly, grouped)
      Verify: .github/pull_request_template.md, .github/dependabot.yml
- [x] AC5: CI green on a sample PR; runtime < 8 min
      Verify: PR #29 checks

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | repo | private GitHub repo, default branch main (exists since M0) | ✅ |
| AC2 | workflow | .github/workflows/ci.yml: lint-type, test-py, docs, security (gitleaks + pip-audit: no known vulnerabilities), terraform. ADR-index/link checks deferred (no checker yet) | ✅ (partial: docs = task validation) |
| AC3 | review | actions pinned by SHA (checkout v7.0.1, setup-uv v10.2.0, setup-terraform v4.0.1); least-privilege `contents: read` | ✅ |
| AC4 | files | PR template with the DoD checklist; Dependabot weekly, grouped (github-actions, uv) | ✅ |
| AC5 | CI run | PR #29, run 36286866667: all 5 jobs pass; slowest 1 m 24 s (< 8 min) | ✅ |
| Extra | ruleset | "main: PRs with passing CI" (id 24059050): PR required, 5 required checks, branch up to date, no deletion/force-push, no bypass | ✅ |

## Implementation history
### 2026-09-25 — ahead of task (owner setup)
- Owner ran `gh auth login` (justin-gonzaga). The repo already existed (created by the owner on 2026-09-24, private, empty) and was verified empty before pushing. `git push -u origin main` succeeded. Visibility: PRIVATE (it goes public only after SEC-001).
- A pre-push secret scan (git grep for key/token patterns) found nothing.
- The rest of AC1 (and AC2 onwards: CI workflows) remains.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- dbt job in CI (ephemeral ci_pr<N> datasets): grant the dev deploy SA read access to the raw bucket and the raw dataset (INFRA follow-up).
- ADR index / link / [R-xx] citation checks in the docs job.
