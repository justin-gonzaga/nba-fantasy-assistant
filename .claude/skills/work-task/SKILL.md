---
name: work-task
description: Implement one backlog task end-to-end (claim, TDD, validate, document, ship, report). Use when the owner says "implement <ID>", "work on the next task", or "keep going".
disable-model-invocation: true
arguments: [task_id]
metadata:
  version: 0.1.0
  inputs: "task ID or 'next'"
  outputs: "merged or PR'd change, updated task file, STATUS.md, report"
---

## State (injected)
!`python tools/tasks.py status`

## Preconditions
- If `$task_id` is `next` or empty, use the first ID from `python tools/tasks.py next -n 1`.
- `python tools/tasks.py claim <ID> --by claude` must succeed. If it reports blockers, stop and report them. If the task is already `in_progress`, **resume**: read the last *Implementation history* entry and continue from its "next step".

## Procedure
1. **Load context narrowly**:
   - the task file
   - each item in its "Context to read" list
   - `CLAUDE.md` §3 (already in context)
   - Nothing else unless it's needed. If `ready: false`, refine it first with `/new-task refine <ID>`, then stop for the owner if the task is Tier B/C.
   - **Scope added mid-task** (the owner asks for more while you work): update the task's stories, ACs and Verify
     lines first and record it in *Decisions*; if it is architectural, write a decision menu + gated tasks instead (T5).
   - **Task spec check**: every AC must be measurable and have a `Verify:` line (the task specification standard, T1). If any is missing or vague, fix it now (`/new-task refine`) *before* writing code, and record the change in *Decisions*.
2. **Plan**: append a dated plan to *Implementation history*: approach, files, and the tests per AC. For M-size or multi-file tasks, explore in plan mode first.
   - **Set a goal (S-36)**: `/goal All ACs of <ID> are proven by their Verify commands, and `just ci-local` passes.` A separate evaluator re-checks it every turn, and the Stop hook (FND-009) blocks ending while `just check` fails.
3. **Branch**: `git switch -c task/<ID>-<slug>` from an up-to-date main. (Before a remote exists, work locally.)
4. **TDD per acceptance criterion**:
   1. Write a failing test.
   2. Write the minimal code to pass it.
   3. Refactor.
   4. Run `just check` (or `uv run pytest -q <pkg>` + `uv run ruff check` + `uv run mypy <pkg>` before `just` exists).
   5. Commit (`test:`/`feat:`/`refactor:`, `Task: <ID>` trailer).
5. **Validate**: run the full `just ci-local`. On failure, take a focused fix attempt. **After 3 failed attempts, stop**: write a checkpoint with the diagnosis, set `status: blocked`, and report.
6. **Evaluate** (ML, decision, or evaluation tasks): run the required eval commands and commit the report. Cite `[R-xx]`.
6b. **UI tasks (component web)**: run the visual QA loop in design-language §9 (`just web-screens`, review the
   images against the checklist, fix, re-capture) and note the before/after review in the task file.
7. **Document**: component README, runbooks/ADR if applicable, the task-file history (commands + results, attempts, skills/agents used, interventions), and STATUS.md if it changed.
   - If the task completed a milestone, added a user-visible capability, or changed a commercial blocker, cost, or risk, also update `docs/project/commercial-view.md`: the progress table, and a change-log line of ≤ 3 plain-English lines with no jargon.
   - If the task completes the evidence for a bullet in `docs/project/cv-tracker.md`, fill its `{placeholders}` with **measured** values only, set it to ✅, link the evidence, tick the keywords, and add a change-log line. Never invent or round up metrics.
   - If the task produced paper-relevant material (a method as built, a result, or a figure), append a line to the *Section log* in `paper/README.md` with the evidence link.
   - **Lessons (D-58)**: append a row to `docs/platform/lessons.md` for anything learned that another task or project should reuse or avoid (what we tried, the outcome, the evidence, the lesson, the layer). If nothing was learned, write `Lessons: none` in the task history. New files: add them to `platform-manifest.yaml` (`python tools/manifest_check.py` must pass).
8. **Review**: if size M or Tier B, **first fill `## Evidence` and the implementation history** (the reviewer checks them), then invoke the `reviewer` subagent with the task ID and branch. On FAIL, fix and re-run it (this counts toward the 3-attempt cap).
9. **Ship**:
   - Tier A: `just ship` (auto-merge on green).
   - Tier B: open a PR and stop for the owner.
   - Before FND-008 exists: squash-merge locally only for Tier A, with CI-equivalent checks green.
10. **Close**: fill `## Evidence` with **one row per AC** (type, exact reference: test id / CI run / commit / report path, and the result with numbers), and tick the AC checkboxes. Then run `python tools/tasks.py done <ID>`, which refuses without full evidence. Record the newly unblocked tasks.
11. **Report** (≤ 10 lines): what changed, the evidence (test/eval numbers), follow-ups, newly unblocked tasks, and any owner action needed.
12. **Continue?** Only if the owner asked to keep going, the next task is Tier A and eligible, and nothing needs the owner. Otherwise end and suggest `/clear` before the next task.

## Stop conditions
The CLAUDE.md §7 list. Ask by writing to the task file and the gates file, then pick another eligible task, or end.

## Must not
- Work outside the task's `areas:` without recording why.
- Skip tests, mark ACs done without evidence, weaken tests to pass, or `--no-verify`.
- Merge Tier B/C work yourself.
