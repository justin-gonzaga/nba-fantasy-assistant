# DevOps Standard

Status: **Accepted** (owner selections 2026-09-24: F4–F6, I1–I6, S-18–S-23, S-28; ADR-0017, ADR-0019).

## 1. Command surface
- **`just` is the single entry point** for humans, agents, and CI. CI calls `just` recipes, never raw commands, so local and CI behaviour match.
- Core recipes:

  | Recipe | Does |
  |---|---|
  | `setup` | installs the toolchain + deps |
  | `check` | fast checks: format, lint, types, unit tests for changed packages |
  | `ci-local` | the full CI suite |
  | `test` | tests |
  | `dq` | data-quality results |
  | `pipeline <job>` | runs a pipeline job |
  | `backfill` | historical backfill |
  | `eval-gate` | model promotion gate |
  | `replay` | historical decision replay |
  | `task …` | task CLI |
  | `status` | project + system status |
  | `doctor` | tool versions + which config/credentials are present (never their values) |
  | `ship` | merges the task branch |
  | `release` | creates a CalVer release tag |
  | `rollback <tag>` | redeploys a previous release |
  | `tf-plan` / `tf-apply ENV` | Terraform plan/apply |
  | `paper` | builds the research paper |

## 2. CI (GitHub Actions; public repo → rulesets on `main`)
| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | PR, push to main | `lint-type` (ruff, mypy, import-linter); `test-py` (pytest + coverage, offline); `dbt` (build + test against an **ephemeral BigQuery dataset** `ci_pr_<n>` in the dev project, dropped afterwards); `web` (tsc, eslint, vitest, Playwright once the web app exists); `security` (gitleaks, pip-audit, pnpm audit, tflint/tfsec); `docs` (task validation, ADR index, links, `[R-xx]` check) |
| `eval.yml` | PR touching features/models/decision | eval smoke on fixtures with a fixed threshold. The full gate runs locally with MLflow, and its report is committed |
| `build.yml` | push to main | Docker build → Trivy → push to **Artifact Registry** → **deploy to the dev project** |
| `deploy.yml` | tag `v*` (CalVer) | promote the *same image digest* to **prod** Cloud Run; health check; automatic rollback on failure |
| `terraform.yml` | PR touching `infra/` | fmt/validate/tflint + `plan` posted to the PR; apply to dev on merge; apply to prod on release tag |
| `paper.yml` | PR touching `paper/` | build the PDF (latexmk) and upload it as an artefact |

- GCP auth uses **Workload Identity Federation** (no keys). The prod deploy identity is only usable from `main`/tags.
- Permissions are least-privilege. Third-party actions are pinned by SHA.
- Target: PR CI under 8 minutes.

## 3. Containers
- One multi-stage image: an SPA build stage (Node) → a Python stage (uv) → a runtime stage (`python:3.13-slim`, **non-root**).
- Entrypoints:
  - `api`: Cloud Run service (FastAPI + Telegram webhook)
  - `job <name>`: Cloud Run jobs (the pipeline CLI)
- A Docker Compose file exists for local parity only. Production is Cloud Run.
- Deploys pin images by digest. Trivy blocks HIGH/CRITICAL vulnerabilities that have a fix.

## 4. Environments
- Local, CI, dev and prod (architecture §7). Config differs **only** by env vars / Secret Manager values and the GCP project.
- Merges to `main` deploy to dev; CalVer tags deploy to prod.

## 5. Infrastructure as code (Terraform)
- The layout:
  - `infra/terraform/bootstrap` (projects, state bucket, WIF, budget)
  - `infra/terraform/modules/*`
  - `infra/terraform/envs/{dev,prod}`
- State lives in a versioned, locked GCS bucket. There are no manual console changes: drift is detected by a scheduled `plan`.
- IAM follows the per-workload service accounts in the security standard.

## 6. Scheduling
- Schedules are declared once in `apps/pipeline/schedules.yaml`, including each user's awake window. **Cloud Scheduler** jobs are generated from it by Terraform.
- Locally, the same CLI runs on demand. Task Scheduler is optional and used only for the one-off stats.nba.com history download.

## 7. Monitoring and alerting
- Job results go to `ops.job_runs`, DQ results to `ops.dq_results`, and freshness is checked. All of them feed `/system/health`.
- Cloud Monitoring alert policies cover job failures, staleness, and budget. Alerts go to the **Telegram bot** as "system" messages.
- A **healthchecks.io** dead-man's switch catches the case where no job runs at all.
- Structured JSON logs go to Cloud Logging.

## 8. Backups and rollback
- Prod raw bucket: versioning + a retention policy. A weekly BigQuery export goes to GCS, and BigQuery time travel covers 7 days. A monthly restore drill task tests it.
- Rollback: redeploy the previous image digest (`just rollback`). Schema changes are additive, so a code rollback never requires a data rollback. The marts can always be rebuilt from raw.
