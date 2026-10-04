# Definition of Done

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

A task is **done** only when every applicable item below is true **and verified by a command**, not asserted.
The `reviewer` subagent checks this list, and `just ship` refuses to merge if the automated items fail.
Items marked (auto) are enforced by `just ci-local` / CI.

## 1. Code
- [ ] Implements every acceptance criterion in the task file. Each criterion maps to at least one test or a validation command, recorded in the task file.
- [ ] (auto) `ruff format --check`, `ruff check`, and `mypy --strict` are clean. Import-linter contracts pass.
- [ ] No TODOs without a linked follow-up task ID.
- [ ] Changes stay within the task's declared `areas:`. Anything outside them is explained in the implementation history.

## 2. Tests
- [ ] TDD evidence: tests were written for each acceptance criterion (see testing standard §1).
- [ ] (auto) All tests pass. Coverage floors are met for touched packages.
- [ ] Bug fixes include a regression test that failed before the fix.
- [ ] Time-dependent code is tested with `FrozenClock`, and no test touches the network.

## 3. Data (if the task touches ingest, dbt, or features)
- [ ] (auto) The Pydantic contract + recorded fixture + contract test exist for any new or changed source endpoint.
- [ ] (auto) `dbt build` passes on fixtures. New models have primary-key, relationship, and range tests, and freshness is set for new sources.
- [ ] A full refresh equals the incremental result (tested for incremental models).
- [ ] (auto) A leakage test exists for any new feature view.
- [ ] `just dq` passes on real local data, with the results noted in the task file.

## 4. Evaluation (if the task touches models, decisions, or evaluation)
- [ ] Baseline comparison run, with its report committed in `docs/evaluation/reports/`.
- [ ] The promotion gate was evaluated (`just eval-gate`) if a model is being promoted. On PASS, promotion happens automatically (MLflow `champion` + GCS export + Telegram note). The task links the promotion record.
- [ ] The model card or method doc cites its grounding `[R-xx]`.
- [ ] (auto) The golden tests for every scoring format pass.

## 5. Documentation
- [ ] Component README / public interface docs are updated.
- [ ] An ADR is written (status Proposed) if a decision is hard to reverse, costs money, or changes a boundary.
- [ ] A runbook is added or updated for any new operational procedure.
- [ ] `docs/project/STATUS.md` is updated if the task changes what exists or what's next.
- [ ] `docs/project/commercial-view.md` is updated (plain English) if the task hits a milestone, adds a user-visible capability, or changes a commercial blocker, cost, or risk.
- [ ] `docs/project/cv-tracker.md` is updated if the task completes the evidence for a CV bullet (measured numbers only, with an evidence link).
- [ ] `paper/README.md` section log is updated if the task produced paper-relevant methods, results or figures.

## 6. Observability
- [ ] New jobs emit a `JobResult` to `ops.job_runs`, with structured logs carrying `run_id`.
- [ ] New failure modes surface on `/system/health` or in `just status`, and alert if they need action.

## 7. Security
- [ ] (auto) gitleaks is clean. No secrets, `.env`, `data/`, or unscrubbed league data are committed.
- [ ] (auto) `pip-audit` / `pnpm audit` show no new HIGH/CRITICAL issues with an available fix.
- [ ] New dependencies are justified in the PR description.

## 8. Reproducibility
- [ ] Runs from a clean checkout with `just setup` + the documented commands. No undocumented manual steps.
- [ ] (auto) The lockfiles are updated and committed when dependencies change.
- [ ] Seeds are recorded for anything stochastic.

## 9. CI and Git
- [ ] (auto) CI is green on the PR.
- [ ] The branch is named per the git workflow. The squash commit uses Conventional Commits with the `Task: <ID>` trailer.
- [ ] The merge tier was respected (A: auto; B/C: owner approved).

## 10. Task state
- [ ] Every AC is ticked and has a `Verify:` line. `## Evidence` has **one row per AC**, with a reproducible reference and result (task specification standard T1–T2); `tasks.py done` enforces this.
- [ ] The task file has `status: done`, a completion date, and an implementation-history entry covering:
  - summary
  - commands run and their results
  - decisions made
  - known issues
  - follow-up task IDs (created as files)
  - skills/agents used, the number of attempts, and any human interventions
- [ ] `just task board` has been regenerated. Newly unblocked tasks are listed in the report to the owner.

## Spikes and research tasks (reduced DoD)
Only sections 5, 9 and 10 apply, plus:
- the findings are written in `docs/research/`
- the assumptions (`A-xx`) are updated
- any spike code is **discarded**; it is not merged
