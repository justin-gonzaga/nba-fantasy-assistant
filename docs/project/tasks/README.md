# Task System

This is a markdown-in-repo task tracker (ADR-0015, S-29). **The repository is the project state.** A new
session needs nothing from past conversations.

## Hierarchy
- **Project**: `docs/specification/project-spec.md`
- **Roadmap**: `docs/project/roadmap.md` (phases, milestones)
- **Epic**: the `epic:` field (`EP-xx Name`), listed in the roadmap
- **Component**: the `component:` field
- **Task**: one file here, containing:
  - acceptance criteria
  - implementation (the task's branch)
  - tests
  - evaluation
  - docs
  - completion (the DoD)

## File format
`docs/project/tasks/<ID>-<slug>.md`. The front matter is restricted YAML: only scalars and inline `[a, b]` lists.

```yaml
---
id: DATA-004                 # PREFIX-NNN, unique
title: "..."
epic: EP-20 Ingestion
phase: 2                     # roadmap phase
component: ingest
status: todo                 # todo | in_progress | blocked | review | done | cancelled
ready: true                  # false = placeholder; refine just-in-time before starting
size: M                      # S (<= ~1h agent time) | M (<= 1 session). No L: split it.
autonomy: auto               # auto (Tier A) | review (Tier B) | gated (Tier C)
gate: G-04                   # approval gate that must be APPROVED, or none
depends_on: [DATA-003, DISC-002]
areas: [packages/ingest/**]  # expected files touched; leaving these needs justification
standards: [data-engineering]
assignee:
created: 2026-09-24
completed:
---
```

Body sections, in order:
1. **Objective**
2. **Context to read (only these)**
3. **User stories and edge cases** (user-facing tasks: `component: web` or `api`; IMP-006): personas, their
   stories, and the edge cases, each covered by an AC or ruled out of scope
4. **Acceptance criteria**, as checkboxes `AC1…`
5. **Test requirements**
6. **Evaluation requirements**
7. **Evidence**: filled at completion (T2)
8. **Implementation history**: append-only, one entry per session. Record:
   - date
   - summary
   - commands and results
   - attempts
   - skills/agents used
   - human interventions
   - the next step if unfinished
9. **Decisions**
10. **Known issues**
11. **Follow-ups**: new task IDs

## Prefixes
| Prefix | Meaning |
|---|---|
| STD | standards |
| DISC | discovery spikes |
| RSCH | research |
| FND | foundation / harness |
| DATA | ingestion and warehouse |
| ANL | semantics, baselines, first value |
| EVAL | evaluation |
| DEC | decision engine |
| ML | models |
| APP | API |
| WEB | frontend |
| PROD | production |
| IMP | agent/process improvement |
| EXP | experiments |

## Task specification standard (owner selections T1–T4, 2026-09-24)
**T1: Acceptance criteria are testable and carry a `Verify:` line.**
- Each AC is an *observable, measurable* outcome: no "works well", no "is implemented".
- Use thresholds and numbers where relevant (latency, coverage, MAE with CI, counts).
- Each AC has an indented `Verify:` line naming the exact proof:
  - a test id (`file::test`)
  - a command + its expected output
  - an evaluation report path
  - a screenshot, for UI only
- ML/decision ACs reference the gate and `[R-xx]` grounding.

**T2: Evidence table on completion.**
- `## Evidence` has **one row per AC**: type (test / command / report / screenshot / commit), an exact reference (test id, CI run link, commit SHA, report path), and the result (with numbers).
- Evidence must be reproducible. "Looks fine" is not evidence.

**T3: Enforcement.**
- `tasks.py validate` (runs in `just check` and CI) checks, for `ready` tasks:
  - the required sections (Objective, Acceptance criteria, Test requirements, Evidence)
  - `- [ ] ACn:` items
  - a `Verify:` line for each AC
- Missing items are warnings while a task is `todo`/`in_progress`, and **errors at `review`/`done`**.
- `tasks.py done` refuses unless every AC has an evidence row.
- The `reviewer` subagent judges *quality*: are the ACs truly testable and complete, and does the evidence actually prove them?

**T5: Spec before code, and scope changes go through the spec (owner, 2026-10-02; IMP-006).**
- No implementation starts on a task that is `ready: false` or whose ACs don't cover the request.
- User-facing tasks carry `## User stories and edge cases`; `tasks.py validate` warns without it and errors at
  `review`.
- When the owner adds scope mid-task ("also add images"), update the spec (stories, ACs, Verify lines) first, then build.
- Architectural asks become a decision menu (D-xx + gate) and specced, gated tasks, not code.

**T4: Creation via `/new-task` from `_template.md`.**
- The skill scaffolds, fills in the fields, and validates.
- Size is S or M only (split anything bigger).
- Later-phase tasks stay `ready: false` until refined just-in-time, and refining means writing the ACs + Verify lines.

## Rules
- **Eligible** = `status: todo` + `ready: true` + all `depends_on` done + the gate APPROVED. This is computed by `python tools/tasks.py next`, never by hand.
- **Just-in-time refinement**: tasks after Phase 2 are `ready: false` placeholders. Refine a task (write its ACs and context list) when its dependencies are nearly done, so its spec matches the real code.
- **Claim before work**: `tasks.py claim <ID>`. This prevents two sessions from taking the same task.
- **Finish**: `tasks.py done <ID>` regenerates `BOARD.md` and prints any newly unblocked tasks.
- **Blocked**: set `status: blocked` and write the reason and the needed decision in *Known issues*. If it is a decision, add it to `human-approval-gates.md`.
- Never delete task files; use `cancelled` with a reason.

## Commands
```
python tools/tasks.py validate | next [-n 3] | show <ID> | why <ID> | board | status | gates | claim <ID> | done <ID>
```
(Once `just` exists, these become `just task …`.)
