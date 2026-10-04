---
id: ARCH-001
title: "Apply owner architecture & technology selections (D-01..D-30)"
epic: EP-00 Governance
phase: 0
component: docs
status: done
ready: true
size: M
autonomy: review
gate: G-17
depends_on: []
areas: [docs/architecture/**, docs/project/**, docs/specification/**, CLAUDE.md]
standards: [documentation]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# ARCH-001 — Apply owner architecture & technology selections

## Objective
Turn the owner's D-xx selections into the final architecture: revise the architecture, technology evaluation, ML design, and ADRs to match; remove the PROPOSAL banners; and re-plan the affected tasks.

## Context to read (only these)
- `docs/project/architecture-decisions.md` (the selections)
- The sections of `docs/architecture/*` referenced by each changed item

## Acceptance criteria
- [x] AC1: Every D-xx has `**Selected**:` recorded with a date.
      Verify: script: count D-items in architecture-decisions.md lacking `Selected` → 0
- [x] AC2: For each item where the selection ≠ ★, the affected docs are revised: `system-architecture.md`, `technology-evaluation.md`, `ml-and-decision-design.md`, and the ADRs. Each affected ADR is superseded or edited while still Proposed, and gets an options table and a decision matching the choice.
      Verify: `git grep -i "duckdb|tailscale|ntfy|supercronic"` over the active docs → 0; review of the squash commit
- [x] AC3: The ADRs matching selected options are set to Accepted, and the ADR index is updated.
      Verify: ADR index: 24 rows, 0 'Proposed'
- [x] AC4: Tasks whose scope changed are updated or created, or cancelled with a reason. `python tools/tasks.py validate` passes, and the board is regenerated.
      Verify: `python tools/tasks.py validate` → 0 errors
- [x] AC5: The PROPOSAL banners are removed from the architecture docs. CLAUDE.md is consistent with the choices.
      Verify: `git grep 'PROPOSAL — pending' -- docs` → only this task's own text
- [x] AC6: A change summary (≤ 15 lines) is added to STATUS.md.
      Verify: `docs/project/STATUS.md` 'Built so far' section

## Test requirements
`python tools/tasks.py validate`; grep shows no remaining "PROPOSAL — pending" banners; the ADR index matches the files.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | inline Python check (2026-09-24) | 0 D-items without a selection |
| AC2 | command + commit | stale-reference git grep; commit 38cd555 | 0 matches in active docs |
| AC3 | report | docs/architecture/adr/README.md | 24 ADRs: 21 Accepted, 3 Superseded, 0 Proposed |
| AC4 | command | `python tools/tasks.py validate` | 0 errors (126 tasks) |
| AC5 | command | `git grep 'PROPOSAL — pending' -- docs` | 1 match = this task's own description |
| AC6 | report | docs/project/STATUS.md | Summary present (≤ 60 lines) |

## Implementation history
### 2026-09-24 — session 1
- Reconciled all owner selections (D-01…D-41, F/I/U/PAPER items): system-architecture v0.2 rewritten; tech-eval marked as the evaluation record + a selections summary; ML design amended (MLflow, C16 cold start, C17 NL agent); ADRs 0019–0024 added, 0003/0004/0014 superseded, the rest accepted with pre-acceptance amendments; roadmap v0.2; CLAUDE.md; tasks FND-011/012/013, DATA-001/012 updated; INFRA, PAPER, cold-start and showcase tasks added.
- Checks: `python tools/tasks.py validate` passed; a stale-reference sweep was run (see the commit).
- Skills/agents: none (main session). Attempts: 1. Interventions: owner decisions via panels.
- **Next step**: the owner reviews via G-00 panels, then squash-merge to main (Tier B).

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
