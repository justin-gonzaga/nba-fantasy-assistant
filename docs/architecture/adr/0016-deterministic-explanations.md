# ADR-0016: Deterministic, evidence-based explanations; LLM optional

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-09
- **Related**: `ml-and-decision-design.md` §3.4, SHAP `[R-23, R-24]`

## Decision
- Explanations are rendered from templates that are filled **only from structured evidence**: facts, metrics, predictions with SHAP contributions, and rules.
- A test asserts that every number in the text exists in the evidence.
- An optional LLM rephrasing layer (the Claude API, billed separately from Claude Pro) is disabled by default. If enabled, it must pass the same number-round-trip test.

## Alternatives
- An LLM that generates explanations freely. Rejected, because of the hallucination risk.
- A laya-style classifier. Not applicable (technology evaluation §14).

## Revisit triggers
The owner finds the templated text too rigid → G-09.

## Amendment (2026-09-24, before acceptance)
The same grounding rule applies to NL answers (ADR-0023).
