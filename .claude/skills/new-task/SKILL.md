---
name: new-task
description: Create a new backlog task, or refine a placeholder task (ready false → true), following the task specification standard (testable ACs with Verify lines, evidence section). Use when the owner or a workflow needs new work captured, or before starting a task that isn't ready.
arguments: [mode, subject]
metadata:
  version: 0.1.0
  inputs: "'create <description>' or 'refine <TASK-ID>'"
  outputs: "a validated task file under docs/project/tasks/"
---

Standard: `docs/project/tasks/README.md` → "Task specification standard" (T1–T4). Template: `docs/project/tasks/_template.md`.

## Procedure
**create**
1. Pick the prefix (table in the README) and the next free number (`ls docs/project/tasks/<PREFIX>-*`).
2. Copy `_template.md` to `<ID>-<slug>.md` (slug: ≤ 7 kebab words) and fill in the front matter:
   - epic, phase, component
   - `size` S or M. If it would be bigger, **split it** into several tasks with `depends_on`.
   - `autonomy` per the git-workflow tiers
   - `gate`, `depends_on`
   - `areas`, `standards`
3. Write the Objective (the outcome + why, linking the requirement/decision/ADR) and a **narrow** context list.
4. For user-facing tasks (`component: web` or `api`), write `## User stories and edge cases` first (T5): each
   persona or situation (phone, keyboard, demo visitor, stale data, API down, no permission), their story in their
   words, and what can go wrong. Then make sure every edge case lands in an AC or is ruled out of scope.
5. Write the ACs, following T1:
   - Each AC is observable and measurable.
   - Each one gets an indented `Verify:` line with the exact test id, command + expected output, or report path.
   - Cover the unhappy paths (errors, empty data, leakage).
   - Point ML ACs at the gate and cite `[R-xx]`.
6. Test requirements: the layers, the fixtures, and TDD notes. Evaluation requirements: metrics, baselines, the report path, or `n/a`.
7. Leave `## Evidence` as the template table. Set `ready: true` only if every AC has a Verify line and the dependencies are known.

**refine <ID>**: open the placeholder and complete steps 3–7 against the code as it exists now. Set `ready: true`.

**Always finish with**:
1. `python tools/tasks.py validate -w`. The new or refined task must have no errors or warnings.
2. `python tools/tasks.py board`
3. Report the ID, a one-line objective, the ACs count, and what it depends on or unblocks.

## Must not
- Write vague ACs ("works", "is implemented", "handles errors").
- Create L-sized tasks.
- Duplicate an existing task: check first with `git grep -il "<keyword>" docs/project/tasks`.
