---
id: FND-010
title: "Package stubs for all components + import-linter contracts"
epic: EP-10 Foundation
phase: 1
component: tooling
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: [FND-007]
areas: [packages/**, apps/pipeline/**, pyproject.toml]
standards: [software-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-24
---
# FND-010 — Package stubs for all components + import-linter contracts

## Objective
Create empty, typed packages (ingest, features, models, decision, evaluation, apps/pipeline) and enforce layering.

## Context to read (only these)
- `docs/architecture/system-architecture.md §3`

## Acceptance criteria
- [x] AC1: Typed stub packages exist (ingest, features, models, decision, evaluation, apps/pipeline), each importable, with a README stating its responsibility, planned interface and allowed dependencies.
      Verify: `uv run pytest -q` → an import test per package passes; a README is present in each package dir
- [x] AC2: import-linter contracts encode architecture §3 (the layers, ingest depending only on core, analytics never importing ingest) and run in `just check`.
      Verify: `uv run lint-imports` → all contracts kept; a deliberate violation (core importing decision) makes it fail (output recorded), then it's reverted
- [x] AC3: No knowledge skills are created yet (there's no real code); the rule is documented.
      Verify: Decisions section of this task + agent-architecture §3 note

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | `just ci-local`: tests/test_import.py in ingest, features, models, decision, evaluation, apps/pipeline; a README per package | 41 passed (6 new import tests); mypy strict clean over 27 files |
| AC2 | command | `uv run lint-imports`; a deliberate `import fantasy_decision` added to fantasy_core/errors.py, then reverted | normal: 3 kept, 0 broken. Violation: "Analytical layering … BROKEN — fantasy_core.errors -> fantasy_decision", exit 1. After the revert: 3 kept |
| AC3 | doc | this task's Decisions + docs/agents/agent-architecture.md §3 ("knowledge skills are created by the tasks that first need them") | no knowledge skills created |

## Implementation history
### 2026-09-25 — overnight session (loop)
- Generated 5 library stubs + the `apps/pipeline` app (uv_build src layout, py.typed, README, import test). The workspace now includes `apps/*`. Package dependencies follow the layering.
- import-linter in the dev deps and in `just check`, with three contracts: the layers (pipeline > evaluation > decision > models > features > core); ingest → core only; core/analytics never import ingest (they read the warehouse, not the sources).
- The mypy path uses comma separators (Windows-safe). Attempts: 2 (a docstring line-length fix). Reviewer: not required (S, Tier A). Interventions: none.

## Decisions
- Knowledge skills (ingest/dbt/ml/api/web) are deferred until each package has real code, so they describe code as it actually is.
- Analytics packages are forbidden from importing ingest: they read the warehouse through `AsOfReader`, never the source clients.

## Known issues
_None._

## Follow-ups
_None._
