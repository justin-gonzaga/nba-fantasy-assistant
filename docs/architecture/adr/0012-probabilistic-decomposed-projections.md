# ADR-0012: Decomposed probabilistic projections, baselines first, statistical promotion gate

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-14
- **Related**: `ml-and-decision-design.md` §1–4; standards S-14, S-16, S-17

## Context
- Decisions in category and points leagues need **distributions**, not just point estimates. Win probabilities depend on variance [R-01, R-02].
- Minutes and availability dominate error.
- The owner requires literature-grounded methods.

## Options considered
| Option | Pros | Cons | Grounding |
|---|---|---|---|
| **A. Decomposed: availability × minutes × per-minute rates, with calibrated distributions; empirical-Bayes baseline first** | Each part is testable, explainable, and separately improvable | More components | EB shrinkage [R-10–R-12]; GBM [R-20, R-21]; quantiles [R-22]; count models [R-30]; calibration [R-42, R-46, R-47] |
| B. One end-to-end GBM per stat | Fewer parts | Entangles availability and role; poor uncertainty | [R-20] |
| C. Hierarchical Bayesian model (PyMC) | Principled uncertainty | Slow; harder to maintain and explain to agents | EB is its practical approximation [R-11] |
| D. Deep sequence models | Flexible | Data-hungry; opaque; no evidence they beat GBM on small tabular data | — |

## Decision
- Option A.
- Baselines (Marcel-style + EB shrinkage [R-11, R-13]) ship first and act as incumbents.
- ML components replace them only through the promotion gate: walk-forward evaluation [R-50, R-51] with a paired block-bootstrap CI [R-54, R-55], and a Diebold–Mariano test reported [R-53].

## Consequences
- Value is delivered early from baselines. The ML work is measurable.
- Accepted risk: the ML may never beat the baseline for some stats, which is itself an acceptable finding.

## Revisit triggers
The baseline beats the ML across all stats for a full season → simplify. Or a new citable method shows large gains → a new ADR.

## Amendment (2026-09-24, before acceptance)
Cold start (D-40): translated pre-NBA priors + EB. Until the Phase 9 data work lands, draft/age/position priors only. Tracking via MLflow (ADR-0021).
