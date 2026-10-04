# ADR-0018: Yahoo scoring formats as pluggable objectives

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-14
- **Related**: spec FR-S1–S4, `system-architecture.md` §4.3, `[R-01, R-02, R-03, R-04, R-61]`

## Context
The owner requires support for every Yahoo NBA scoring format:
- H2H Categories
- H2H One Win
- H2H Points
- Rotisserie
- Points

The formats differ in what "good" means, not in how players perform.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. A shared simulation + a `ScoringObjective` strategy per format; lineup weights = ∂objective/∂stat** | One engine; formats are isolated and golden-tested; follows the dynamic-valuation literature [R-02, R-03] | The objective derivatives need care (estimated from simulation with common random numbers [R-61]) |
| B. Separate engines per format | Simple individually | Duplication; drift |
| C. Static player values (Z/G-score [R-01]) for all formats | Simple | Ignores team context and matchup; wrong for One Win and roto dynamics [R-02] |

## Decision
Option A. Z/G-scores are kept as baselines and for explanations. The MILP lineup optimiser [R-04] consumes format-specific weights.

## Consequences
- Adding a format means adding one objective class plus a golden fixture.
- Accepted: we need settings fixtures for formats the owner's league doesn't use (synthetic if necessary).

## Revisit triggers
Yahoo adds a new format, or a new paper shows better H2H objectives.
