# ADR-0002: Monorepo with a uv workspace

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-00 · **Standards**: S-01, S-02
- **Related**: `technology-evaluation.md` §1, `system-architecture.md` §3

## Context
The project brief requires a single monorepo in which components can be developed and tested independently. The components are mostly Python (ingest, features, models, decision, evaluation, API), plus a dbt project and a TypeScript SPA.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| A. uv workspace: `packages/*` (libraries), `apps/*` (deployables), `warehouse/` (dbt), `apps/web` (pnpm) | One lockfile; per-package deps and tests; fast | Two ecosystems (uv + pnpm) |
| B. A single Python package with subpackages | Simplest | Boundaries aren't enforced; everything depends on everything |
| C. Nx/Pants/Bazel | Strong build graph | Heavy; overkill |

## Decision
Option A. The package boundaries follow the architecture's layering, and `import-linter` enforces it. The repository layout is in `CLAUDE.md` §2.

## Consequences
- Each package can be tested in isolation (`uv run --package fantasy-ingest pytest`).
- An agent can work in one package with a small context.
- Accepted cost: a little workspace boilerplate.

## Revisit triggers
Build or CI time exceeds 10 min because of cross-package rebuilds.
