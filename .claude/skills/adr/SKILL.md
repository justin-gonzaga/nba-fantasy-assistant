---
name: adr
description: Draft a new Architecture Decision Record (status Proposed) with options and trade-offs, and link it to an approval gate if owner approval is required. Use when a decision is hard to reverse, costs money, changes a boundary, or selects an ML/decision method.
arguments: [title]
metadata:
  version: 0.1.0
  outputs: "docs/architecture/adr/NNNN-<slug>.md + index row (+ gate entry)"
---

## Procedure
1. Take the next number from `docs/architecture/adr/README.md`. Copy `0000-template.md` to `NNNN-<slug>.md`.
2. Fill in the Context, citing `docs/research/…`. If the research is missing, use the `researcher` subagent first and persist the result.
3. Options: at least 2 real alternatives in a table (pros, cons, cost). For ML or decision methods, add the grounding `[R-xx]` for each option. Add missing references to the literature review first, flagged "(to read)".
4. Decision: phrase it as the recommendation. **Status: Proposed.**
5. Add consequences and concrete revisit triggers.
6. Add a row to the index.
7. If owner approval is needed, add a gate to `docs/project/human-approval-gates.md` in the standard format (options, recommendation, what happens if there's no answer, what it blocks, `[R-xx]` for ML). Add it to the summary table too.
8. Report ≤ 8 lines: the decision, the recommendation, and the gate ID.

## Must not
- Mark an ADR Accepted. Only the owner can, via `/gate`.
