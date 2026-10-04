---
id: DATA-012
title: "dbt project skeleton (bronze sources, packages, CI on fixtures)"
epic: EP-21 Warehouse
phase: 2
component: warehouse
status: done
ready: true
size: S
autonomy: auto
gate: G-00
depends_on: [INFRA-002, DRAFT-001]
areas: [warehouse/**, justfile]
standards: [data-engineering]
assignee: claude
created: 2026-09-24
completed: 2026-09-25
---
# DATA-012 — dbt project skeleton (bronze sources, packages, CI on fixtures)

## Objective
dbt-bigquery project with dbt-native layers (staging/intermediate/marts), raw sources as external tables over GCS, dbt_utils/dbt_expectations.

## Context to read (only these)
- `docs/standards/data-engineering.md §6-7`
- `docs/architecture/adr/0006-dbt-medallion-transformations.md`

## Acceptance criteria
- [x] AC1: `just dbt build` works locally against the dev BigQuery datasets; a `ci` target writes to `ci_pr<N>_<layer>` datasets (running it in CI is FND-006)
      Verify: `just dbt build` → PASS=8; `DBT_TARGET=ci CI_PR_NUMBER=12 dbt ls` → schema ci_pr12_staging
- [x] AC2: Folder/schema layout staging/intermediate/marts per ADR-0006 (amended); naming conventions documented in warehouse/README.md
      Verify: warehouse/README.md + `just dbt ls` shows models in the right schemas
- [x] AC3: Source freshness configured
      Verify: `just dbt source freshness` output

## Test requirements
Per testing standard: a test (or validation command) for every acceptance criterion; TDD for packages/*.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | dbt run | `just dbt run-operation stage_external_sources` → 4 external tables in `nbafa-hdfo-dev.raw`; `just dbt build` → PASS=8 (1 view + 7 tests); `dbt show` → 64 snapshots (30 rosters, 1 draft, 11 season totals, 22 game logs) = the DRAFT-001 manifest | ✅ |
| AC1 (ci target) | dbt ls | `DBT_TARGET=ci CI_PR_NUMBER=12 dbt ls` → `ci_pr12_staging`; dev → `staging` (macros/generate_schema_name.sql) | ✅ (CI execution in FND-006) |
| AC2 | doc + dbt ls | warehouse/README.md (layers, datasets, naming table) | ✅ |
| AC3 | freshness | `just dbt source freshness` → 4/4 PASS (warn 45 d / error 90 d; rosters 7 d / 21 d) | ✅ |
| Checks | just ci-local | 129 passed, coverage 99.88 %; new test `test_dbt_recipe_uses_the_warehouse_group_and_repo_profiles` | ✅ |

## Implementation history
- 2026-09-25: warehouse/ dbt project (dbt-core 1.12.5, dbt-bigquery 1.12.1; packages dbt_utils, dbt_external_tables, metaplane/dbt_expectations). Raw sources are CSV-as-one-STRING external tables over the GCS snapshots; `stg_nba_stats__snapshots` parses the path. Fixed along the way: a dbt project var doesn't render env_var(), so the bucket uses env_var directly; freshness/loaded_at_field moved under `config:` (dbt 1.10+ deprecation).

## Decisions
- 2026-09-25: D-50 (owner: dbt first). Dependencies changed from [FND-002, DATA-001, INFRA-002, DATA-000] to [INFRA-002, DRAFT-001].
- dbt goes in a separate uv dependency group `warehouse`. It caps google-cloud-storage < 3.2, so the ingest gcsfs/fsspec pins were relaxed to >= 2025.3 (resolved 2025.12.0).

## Known issues
_None._

## Follow-ups
_None._
