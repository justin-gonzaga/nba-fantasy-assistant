# ADR-0001: Record architecture decisions

- **Status**: Accepted
- **Date**: 2026-09-24
- **Deciders**: owner (by requesting ADRs in the project brief), Claude

## Context
The project will be developed over many Claude Code sessions with no shared conversational memory. The reasons behind decisions must survive in the repository.

## Decision
We use lightweight ADRs (the template in `0000-template.md`) following the process in `README.md`. Agents may propose ADRs, and only the owner accepts them.

## Consequences
- A new session can read *why* something was decided without asking.
- There is a small overhead per significant decision.

## Revisit triggers
The ADR count grows past about 60 and the index becomes hard to navigate. If that happens, group the ADRs by area.
