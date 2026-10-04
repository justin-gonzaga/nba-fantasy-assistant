# ADR-0015: In-repo markdown task system and agent operating model

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-11 · **Standards**: S-20, S-29, S-31
- **Related**: `docs/agents/agent-architecture.md`, `docs/project/tasks/README.md`

## Context
- The owner wants task tracking in markdown files in the repo, rather than Jira.
- Agents must resume work across sessions without conversational memory.
- Claude Pro usage must be minimised.

## Decision
- One markdown file per task, with YAML front matter (ID, status, dependencies, acceptance criteria, areas, autonomy tier).
- `tools/tasks.py` (Python standard library only) validates the files, selects the next eligible task, claims and completes tasks, and generates `BOARD.md`.
- A single working session uses on-demand skills. There are only two subagents: `reviewer` and `researcher`.

## Consequences
- The state is diffable and phone-readable, and the logic is deterministic.
- Accepted: no Kanban UI (BOARD.md stands in for one).

## Revisit triggers
More than 300 active task files, or the owner wants GitHub Projects integration.
