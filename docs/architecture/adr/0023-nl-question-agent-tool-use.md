# ADR-0023: Natural-language questions answered by an LLM using vetted tools

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: D-36 A, G-08
- **Related**: ADR-0016, spec FR-UI7

## Context
The owner wants to ask plain-English questions in the dashboard (and via Telegram).

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
The Claude API with **tool use** over vetted analysis functions (projections, matchup state, what-if, comparisons, recommendation history). Every number in an answer must come from a tool result, and this is tested. Per-user and global caps apply. All Q&A is logged.

## Consequences
- Accurate, auditable answers.
- Separate API billing within G-08.
- A strong CV story (LLM agents).

## Revisit triggers
Cost exceeds the budget, or answer accuracy fails its evaluation.
