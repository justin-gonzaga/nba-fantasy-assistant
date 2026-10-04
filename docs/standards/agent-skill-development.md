# Agent & Skill Development Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

The agent system is software: it is specified, versioned, tested, reviewed, and measured.
The design rationale is in `docs/agents/agent-architecture.md`.

## 1. Choosing the mechanism (in order of preference)
1. **Deterministic script / `just` recipe**: if the behaviour can be scripted, script it. There is zero token cost and it is reproducible.
2. **Hook** (`.claude/settings.json`): for rules that must *always* hold (block destructive commands, auto-format, inject status at session start).
3. **CLAUDE.md line**: for always-on guidance that is short and universal. Every line must be worth its token cost on every session.
4. **Skill** (`.claude/skills/<name>/SKILL.md`): for procedures or knowledge needed *sometimes*. They load on demand.
5. **Subagent** (`.claude/agents/<name>.md`): **only** when a separate context window pays off. Cases:
   - independent review (avoids self-review bias)
   - heavy research that would pollute the main context
   - parallel isolated work in a worktree

## 2. Skill specification
```yaml
---
name: work-task                # kebab-case, equals the directory name
description: <one or two sentences: WHEN to use it + WHAT it produces. Written as the trigger>
disable-model-invocation: true # for procedures with side effects (commit, ship)
allowed-tools: …               # minimal
paths: [ "warehouse/**" ]      # for knowledge skills scoped to an area
metadata:
  version: 1.2.0               # SemVer: major = changed contract/outputs
  owner: agent-architecture
  inputs: "task ID"
  outputs: "branch, PR, updated task file"
---
```
Body sections, in order:
- **Purpose**
- **Inputs**
- **Preconditions** (what must be true, and how to check it)
- **Procedure** (numbered, with commands)
- **Outputs**
- **Validation** (commands that prove success)
- **Failure handling**
- **Must not**

Limits: the body is ≤ 150 lines. Push details into referenced files in the skill directory (progressive disclosure).

## 3. Subagent specification
- Frontmatter: `name`, `description` (a crisp delegation trigger), `tools` (an **allowlist**, minimal), `model` (the cheapest that passes its evals), `maxTurns`, plus `isolation: worktree` if it writes.
- The body defines:
  - role
  - what the agent receives (the caller must pass: task ID, file paths, the question)
  - what it may modify (explicit paths)
  - its output format (a fixed markdown schema, so the caller can parse the verdict)
  - stop conditions
- Subagents return **summaries**, not file dumps.

## 4. Handoffs
- The task file is the handoff medium, not the conversation. Before ending any session mid-task, the agent appends a checkpoint to the task's *Implementation history*:
  - done so far
  - next step
  - open questions
  - branch name
- A subagent's result is written into the task file (review verdicts, research summaries) by the caller.

## 5. Testing agents and skills
- Every skill or subagent has an **eval file**: `.claude/evals/<name>.yaml`, containing 2–5 scenarios.
- Each scenario has:
  - a setup (a fixture repo state or task)
  - a prompt
  - **checkable assertions**: files changed, commands run, output schema, forbidden actions not taken
- `just agent-eval <name>` runs the scenarios headlessly (`claude -p` in a scratch worktree) and checks the assertions with a script. It is run on **every** change to that skill or agent, and monthly otherwise.
- Because evals cost Claude usage, keep scenarios small and never run them in CI.

## 6. Versioning and change control
- SemVer in `metadata.version`, with a changelog at the bottom of each file.
- Changes to `.claude/` are Tier B (owner review). The PR includes the eval results before and after.

## 7. Observability and effectiveness
- Each task file's implementation history records:
  - which skill or agents were used
  - the number of attempts
  - whether the validation passed the first time
  - human interventions needed
- `just agent-metrics` aggregates these across tasks, reporting:
  - first-pass validation rate
  - rework rate
  - average sessions per task size
  - intervention rate
- The monthly improvement task reviews the worst skill or agent by these metrics and proposes one change.

## 8. Anti-patterns
- An agent per job title ("frontend agent", "backend agent") that just re-reads the same context. Use `paths`-scoped skills instead.
- Long CLAUDE.md files. Instructions that duplicate standards. Asking the owner something the repo already answers.
- Subagents that write without worktree isolation while the main session also writes.
