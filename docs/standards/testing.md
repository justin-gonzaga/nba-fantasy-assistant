# Testing Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

## 1. TDD by default
1. Write or extend a failing test that encodes an acceptance criterion.
2. Make it pass with the simplest code.
3. Refactor with the tests green.
4. Repeat for each criterion.

Exceptions (documented in the task's implementation history): spikes, pure configuration, and generated code.

## 2. Test layers
| Layer | Scope | Location / marker | Runs in |
|---|---|---|---|
| Unit | pure functions, single classes | `tests/unit/` | `just check`, CI |
| Property | invariants (e.g. the lineup is always legal; adding a dominant player never lowers the objective; ratio stats are computed from totals) | `tests/unit/`, hypothesis | CI |
| Contract | source payload fixtures ↔ Pydantic contracts; OpenAPI snapshot; dbt model contracts | `tests/contract/` | CI; `just contracts-live` monthly (local) |
| Integration | job → an ephemeral BigQuery CI dataset on fixtures; API ↔ that dataset | `tests/integration/`, `@pytest.mark.integration` | CI |
| Data quality | dbt tests, reconciliation | `warehouse/tests/` | CI (fixtures), every pipeline run (real data) |
| Leakage | instrumented `AsOfReader` per feature view | `packages/features/tests/leakage/` | CI |
| ML evaluation | eval smoke on a fixture season, with fixed thresholds | `packages/evaluation/tests/` | CI (smoke); `just eval-gate` (full, local) |
| Golden / regression | scoring-format objectives; recommendation outputs for frozen contexts; explanation text | `tests/golden/` with approved snapshots | CI |
| E2E | Playwright, top 3 flows | `apps/web/e2e/` | CI (once web exists) |

## 3. Fixtures
- **Recorded, sanitised real payloads** are preferred over hand-written ones. `just record-fixture <source> <endpoint>` captures and scrubs them.
- Scrubbing: team and manager names, emails, and GUIDs are replaced with stable fakes. League IDs are hashed.
- The fixture season: a small, frozen "mini-season" (about 30 days, two leagues: 9-cat H2H + points) is committed. The integration, dbt, and eval smoke tests all run on it.
- Each Yahoo scoring format has a settings fixture (FR-S4).

## 4. Rules
- Tests are deterministic: no network, no wall clock (use `FrozenClock`), seeded RNG.
- The unit suite runs in < 60 s and the full CI suite in < 8 min.
- A bug fix starts with a failing regression test.
- Flaky tests are quarantined with `@pytest.mark.flaky_quarantine` and a linked task. They must never be ignored silently.
- Don't assert on log output or private internals. Test behaviour.
