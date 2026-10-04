# ADR-0011: Decision engine separated from models; typed artefact classes

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-00
- **Related**: `system-architecture.md` §2, `ml-and-decision-design.md` §3, `[R-63]`

## Context
The brief requires a clear separation of raw facts, derived metrics, predictions, optimisation outputs, rules, recommendations, and explanations, for debugging and evaluation. Tangling models and decisions is a known source of ML technical debt [R-63].

## Decision
- `packages/models` produces **predictions only**.
- `packages/decision` consumes predictions + a `DecisionContext`, and produces **recommendations**.
- Each artefact class has its own Pydantic type and storage (the architecture §2 table).
- Recommendations reference their evidence by ID/as_of, together with the model versions, snapshot IDs, git SHA, and seed.

## Consequences
- Models and decisions are evaluated separately.
- Any recommendation can be replayed.
- A little more plumbing than a monolith.

## Revisit triggers
None expected.
