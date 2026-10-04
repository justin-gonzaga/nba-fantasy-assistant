---
id: STD-001
title: "Finalise engineering standards from owner selections"
epic: EP-00 Governance
phase: 0
component: docs
status: done
ready: true
size: S
autonomy: review
gate: G-10
depends_on: []
areas: [docs/standards/**, docs/project/standards-decisions.md, docs/architecture/adr/**]
standards: [documentation]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# STD-001 — Finalise engineering standards from owner selections

## Objective
Turn the owner's S-01..S-31 selections into final standards and remove DRAFT banners.

## Context to read (only these)
- `docs/project/standards-decisions.md`
- `docs/standards/README.md`

## Acceptance criteria
- [x] AC1: Every S-xx selection is recorded in standards-decisions.md with the date
      Verify: script: count S-items in standards-decisions.md lacking `Selected` → 0
- [x] AC2: Each affected standard reflects the selected option (non-recommended picks are propagated to architecture/tech-eval/ADRs)
      Verify: review of the devops/security rewrites + patched standards in commit 38cd555
- [x] AC3: DRAFT banners removed; standards README states Accepted
      Verify: `git grep 'DRAFT — pending' -- docs/standards` → 0; standards README states Accepted
- [x] AC4: Linked ADRs (0006, 0008, 0013, 0014, 0017) statuses updated per owner decisions
      Verify: ADR index statuses for 0006/0008/0013/0014/0017
- [x] AC5: `python tools/tasks.py validate` passes
      Verify: `python tools/tasks.py validate` → 0 errors

## Test requirements
Doc link check (manual grep until FND-006 CI exists).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | inline Python check (2026-09-24) | 0 S-items without a selection (S-01…S-31) |
| AC2 | commit | 38cd555 (devops.md, security.md rewritten; 8 standards patched) | Matches the selections |
| AC3 | command | `git grep 'DRAFT — pending' -- docs/standards` | 0 matches |
| AC4 | report | ADR index | 0006/0008/0013/0017 Accepted (amended); 0014 Superseded by 0021 |
| AC5 | command | `python tools/tasks.py validate` | 0 errors |

## Implementation history
### 2026-09-24 — session 1
- All standards set to Accepted per the S-01…S-31 selections: devops.md and security.md rewritten (GCP, Terraform, WIF, Secret Manager, app login, public repo); backend/data-engineering/testing/git-workflow/ml/frontend/DoD patched; DRAFT banners removed.
- Checks: `python tools/tasks.py validate` passed; a stale-reference sweep was run (see the commit).
- Skills/agents: none (main session). Attempts: 1. Interventions: owner decisions via panels.
- **Next step**: the owner reviews via G-00 panels, then squash-merge to main (Tier B).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
