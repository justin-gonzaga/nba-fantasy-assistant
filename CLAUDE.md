# CLAUDE.md — NBA Fantasy Decision Assistant

A personal decision-support system for one Yahoo NBA Fantasy league. It covers all Yahoo scoring formats, and:
- ingests NBA and Yahoo data into a medallion platform (raw on GCS → dbt → BigQuery), with point-in-time history, on GCP serverless (Cloud Run + Cloud Scheduler, Terraform)
- projects player outcomes as calibrated distributions
- turns them into explained, logged, evaluated recommendations

Full spec: `docs/specification/project-spec.md`. **This file is an index. Read other docs only when your task's context list names them.**

## 1. Start of every session
1. Run `python tools/tasks.py status` (later `just status`). Read `docs/project/STATUS.md` (≤ 60 lines).
2. If asked to work: use `/work-task <ID|next>`. If asked what's up: `/status`, `/next`, `/gate list`.
3. **Do not** re-read the architecture, standards, or research unless the task's "Context to read" lists them. **Cite, don't re-research**: `docs/research/` is the cache.

## 2. Repository map
| Path | What |
|---|---|
| `docs/specification/` | project spec (goals, scope, requirements, success criteria) |
| `docs/architecture/` | system architecture, ML & decision design, technology evaluation, `adr/` |
| `docs/research/` | source research, the literature review `[R-xx]`, and assumptions `A-xx` |
| `docs/standards/` | engineering standards (Accepted), the Definition of Done |
| `docs/agents/` | agent/skill architecture and the autonomous loop |
| `docs/project/` | roadmap, `STATUS.md`, `tasks/` (one file per task + BOARD.md), `human-approval-gates.md`, decision menus, `commercial-view.md` (plain-English commercial lens; update at milestones), `cv-tracker.md` (resume bullets; ✅ only with measured evidence) |
| `paper/` | IEEE-style research paper (LaTeX), a living plan in `paper/README.md`; claims only from committed results |
| `tools/` | deterministic scripts (the `tasks.py` task CLI) |
| `.claude/` | settings, skills, subagents (Tier B to change) |
| _planned_ `packages/{core,ingest,features,models,decision,evaluation}` | Python libraries (uv workspace) |
| _planned_ `apps/{pipeline,api,web}` | pipeline CLI (Cloud Run jobs), FastAPI + Telegram webhook + NL agent, React SPA (+ `apps/ios` SwiftUI later) |
| _planned_ `warehouse/` | dbt-bigquery project: staging → intermediate → marts |
| _planned_ `infra/terraform` | GCP: projects, buckets, BigQuery, IAM/WIF, Secret Manager, Cloud Run, Scheduler |

**Layering** (import-linter enforced):
- `core ← ingest`
- `core ← features ← models ← decision`
- `evaluation` may read features/models/decision
- apps may import packages; packages never import apps

## 3. Non-negotiables
- **Point-in-time correctness**: time-varying data is read only via `AsOfReader(t)`. Never call `datetime.now()` in domain code; inject a `Clock`. Timestamps are UTC; the NBA game date is US/Eastern.
- **Bronze is immutable.** Never modify or delete `raw/`.
- **Separate artefact types**: facts, derived metrics, predictions, optimisation outputs, rules, recommendations, explanations (architecture §2).
- **Baselines before ML.** ML ships only through `just eval-gate`. Every method cites **verified** `[R-xx]` entries (ML standard §0). **No ML/projection code before the approved methodology plan (G-19).**
- **Format-agnostic engine**: scoring formats differ only through `ScoringObjective` (ADR-0018). Never branch on the format elsewhere.
- **Explanations** come only from structured evidence. No LLM-invented facts.
- **Secrets**: never read, print, or commit `.env*` or `secrets/`. Check configuration with `just doctor`.
- **Environments**: Claude works in the **dev** GCP project, with read-only prod logs/metrics for diagnosis. Prod changes happen only via CI (merge → dev; CalVer tag → prod).
- **Privacy**: other managers are pseudonymised at ingestion; live Yahoo data is never shown publicly (the repo is public after SEC-001).

- **Layers (D-46, D-58)**: `platform-manifest.yaml` classifies every file as harness, platform, mixed or domain. Harness and platform files must stay project-agnostic (platform code never imports domain code). Put project specifics in domain files. Record reusable lessons in `docs/platform/lessons.md`.

## 4. Workflow (details: `docs/agents/agent-architecture.md` §4)
1. Claim the task.
2. Read the task file and only its context list. **Spec before code (T5)**: if the spec (user stories, edge cases, ACs) doesn't cover the request, fix it first.
3. Append a plan to the task file.
4. Create branch `task/<ID>-<slug>`.
5. **TDD**: test first for each acceptance criterion.
6. Run `just check` often and `just ci-local` before finishing.
7. Evaluate, if the task touches ML or decisions.
8. Update docs, the task history, and STATUS.md.
9. Get a reviewer subagent pass (M-size or Tier B tasks).
10. Run `just ship`.
11. Run `tasks.py done <ID>`.
12. Report in ≤ 10 lines.

Before `just` exists (Phase 1), use `uv run …` / `python tools/tasks.py …` directly.

## 5. Git
- **Owner rule (2026-09-25): every change reaches `main` via a GitHub pull request**, including docs and decision records. Never commit on `main` and never push `main`. Flow: branch → push branch → `gh pr create` (summary + DoD checklist + check results) → checks → `gh pr merge --squash --delete-branch`. Until CI exists (FND-006), paste the `just check` result into the PR body.
- Trunk-based. One task = one branch = one squash commit. Conventional Commits with a `Task: <ID>` trailer. Never push to `main` directly, force-push, or rewrite history.
- **Merge tiers**: Tier A (`autonomy: auto`) merges itself when CI is green. Tier B (`review`: `.claude/`, `CLAUDE.md`, standards, architecture, CI, infra, retention) needs the owner. Tier C (`gated`) can't start until its gate is APPROVED.
- Details: `docs/standards/git-workflow.md`.

## 6. Tasks and definition of done
**Task spec standard** (`docs/project/tasks/README.md`): ACs are measurable, each with a `Verify:` line; `## Evidence` has one row per AC at completion. Create or refine tasks with `/new-task`. `tasks.py validate`/`done` enforce the format.
`docs/standards/definition-of-done.md`. A task is done when its checks are **verified by commands**, not asserted. Record the commands and results in the task file.

## 7. Stop and ask the owner (don't guess) when:
1. a gate isn't APPROVED
2. an architecture or interface change goes beyond the task
3. validation still fails after **3 focused attempts**
4. the scope grows more than 50 % beyond `areas:`
5. credentials or a human action are needed (Yahoo login, installs, accounts)
6. anything costs money
7. anything is destructive or irreversible
8. docs conflict and precedence (ADR > architecture > others) doesn't resolve it

**How to ask:**
- Write the question into the task file, and add a gate entry (options, pros/cons, recommendation, and `[R-xx]` for ML) to `docs/project/human-approval-gates.md`.
- Then continue with another eligible task.
- Batch questions. Never re-ask something the repo already answers.

**The owner decides, from options.** Architecture, technology, implementation-approach, and standards choices are never made unilaterally. Present them as a menu item:
- a short **Learn** primer (the owner wants to learn)
- 2–4 realistic options, with pros, cons, and cost
- a justified ★ recommendation
- `[R-xx]` references for ML and statistics
- a **CV value** note where options differ in resume/job-market relevance (the owner will put this on a DE/DS CV)

Add the item to `docs/project/architecture-decisions.md` (D-xx) or `standards-decisions.md` (S-xx). Until the owner picks, docs describing a choice are marked PROPOSAL/DRAFT.

## 8. Compaction and environment gotchas
- **When compacting, always preserve**: the current task ID and branch, each AC's status + its Verify target, the commands that were run and their results, open questions, and the next step.
- Windows machine: the Bash tool wraps commands, so **inline heredoc scripts containing apostrophes break**. Write longer scripts to the scratchpad and run them. After installing tools, PATH changes appear only in new shells (or reload PATH from the registry).

## 9. Token economy (Claude Pro)
- Prefer scripts over reasoning: task selection, validation, status, eval metrics.
- Read files narrowly (Grep, offsets).
- One task per session; `/checkpoint` before stopping mid-task.
- Subagents only per the agent architecture: `reviewer`, `researcher`.
- Keep reports short: phone-readable, conclusion first.
