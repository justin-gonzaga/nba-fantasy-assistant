# warehouse: dbt-bigquery project

dbt-native layers (S-10 B, ADR-0006 amended): **raw → staging → intermediate → marts**, all in BigQuery.
Auth is the caller's Google credentials: gcloud ADC locally, the job service account on Cloud Run, WIF in CI. `profiles.yml` holds no secrets.

## Run
```powershell
just dbt deps                                  # first time: dbt_utils, dbt_external_tables, dbt_expectations
just dbt run-operation stage_external_sources  # (re)create the raw external tables over GCS
just dbt build                                 # models + tests
just dbt source freshness
```
Targets (set with `DBT_TARGET`): `dev` (default, project `nbafa-hdfo-dev`), `ci` (datasets `ci_pr<N>_<layer>`, `CI_PR_NUMBER`), `prod`.
`DBT_RAW_BUCKET` overrides the raw bucket (default `nbafa-hdfo-dev-raw`).

## Layout and naming (data-engineering standard §7)
| Layer | Dataset | Folder | Name pattern | Materialisation |
|---|---|---|---|---|
| raw | `raw` | sources in `models/staging/<source>/_<source>__sources.yml` | `<source>__<endpoint>` (external tables over `gs://<bucket>/raw/<source>/<endpoint>/*`) | external |
| staging | `staging` | `models/staging/<source>/` | `stg_<source>__<entity>` | view |
| intermediate | `intermediate` | `models/intermediate/` | `int_<purpose>` | table |
| marts | `marts` | `models/marts/` | `dim_<entity>`, `fct_<process>`, `mart_<decision_area>` | table |

- Columns are `snake_case`; IDs end in `_id`, UTC timestamps in `_at`, dates in `_date`.
- The schema name is the layer name in dev/prod (one project per environment); the `ci` target prefixes it per PR (`macros/generate_schema_name.sql`).

## Raw files
Each snapshot is one line of JSON at `raw/<source>/<endpoint>/<key>/<observed_at>.json`, with a `.meta.json` sidecar (fantasy_ingest.snapshot).
The external tables read each file as a single `payload` STRING (tab-delimited CSV with no quoting, which is safe because JSON never contains raw tabs).
`stg_nba_stats__snapshots` drops the sidecars and parses `endpoint`, `snapshot_key` and `observed_at` from `_FILE_NAME`.

## Quality
- Every model: primary key `unique` + `not_null`. Also relationships for foreign keys and ranges for stats (standard §6).
- Every source has freshness thresholds, based on the capture time in the file name.
