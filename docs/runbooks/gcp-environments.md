# GCP environments: storage, datasets and identities (INFRA-002)

Stacks: `infra/terraform/envs/{dev,prod}` → module `infra/terraform/modules/env`. State: `gs://nbafa-hdfo-tfstate/envs/<env>`.
Bootstrap (projects, WIF, budget) is separate: [gcp-bootstrap.md](gcp-bootstrap.md).

## Naming convention
| Thing | Pattern | Example |
|---|---|---|
| Bucket | `<prefix>-<env>-<purpose>` | `nbafa-hdfo-prod-raw`, `nbafa-hdfo-dev-exports` |
| Dataset | `<layer>` (one project per env) | `raw`, `staging`, `intermediate`, `marts`, `features`, `predictions`, `recs` |
| Service account | `<workload>-sa@<prefix>-<env>.iam.gserviceaccount.com` | `ingest-sa@nbafa-hdfo-dev…` |
| CI dataset | `ci_pr<N>_<layer>`, label `ci=true` (dev only) | `ci_pr12_staging` |

Datasets use the dbt-native layer names (S-10 B), not bronze/silver/gold.

## Buckets
| Bucket | Dev | Prod |
|---|---|---|
| raw | objects deleted after 30 days (I3); unversioned | versioned; retention policy (default 30 days, **unlocked**); never expires |
| exports | deleted after 30 days | deleted after 90 days |

Retention lock is irreversible. It stays unlocked, because a locked policy would also block `just purge-yahoo` (security §5) until the period ends.

## Who can do what (least privilege, I5)
| SA | Can | Cannot |
|---|---|---|
| ingest-sa | create + read raw objects | delete or overwrite raw objects; any BigQuery data |
| transform-sa | edit staging…recs; read the raw dataset + raw files; run jobs; write exports | edit raw |
| api-sa | read marts, predictions, recs; run query jobs | write anything |
| scheduler-sa | invoke Cloud Run (jobs arrive in INFRA-004) | data access |
| deploy (bootstrap) | dev: create/own CI datasets (`bigquery.user`); Cloud Run deploy roles arrive in INFRA-004 | prod data |
| dev ingest-sa / transform-sa | **read** the prod raw bucket (I3 A) | write to prod |

## CI ephemeral datasets
- CI (FND-006) creates `ci_pr<N>_*` datasets in dev with the label `ci=true`, runs dbt, and drops them at the end.
- `.github/workflows/ci-dataset-cleanup.yml` deletes leftovers older than 2 days, daily at 03:17 AEDT. It needs the repo variable `GCP_WIF_PROVIDER` (the bootstrap output `workload_identity_provider`).

## Apply (owner-approved, Tier B)
```powershell
terraform -chdir=infra/terraform/envs/dev init; terraform -chdir=infra/terraform/envs/dev plan -out=env.tfplan
terraform -chdir=infra/terraform/envs/dev apply env.tfplan     # dev first (prod references dev SAs)
# then the same for envs/prod
```

## Checks
- `terraform -chdir=infra/terraform/modules/env test`: plan-time policy tests (mock provider; nothing touches GCP).
- After apply: `python tools/iam_negative_tests.py` runs Policy Troubleshooter checks (e.g. ingest cannot delete raw; api cannot write).
