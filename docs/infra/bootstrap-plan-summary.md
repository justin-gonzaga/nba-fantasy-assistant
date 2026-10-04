# Cloud bootstrap: what `terraform apply` would create (INFRA-001)

Plan date: 2026-09-25 · **Applied 2026-09-25 after owner approval** (54 added; re-plan: no changes).
Decision needed: approve `apply` (D-47 Q3). Applying creates Google Cloud resources, so it is a Tier B action.

## In plain English
1. **Three Google Cloud projects** under your billing account: `nbafa-hdfo-admin` (shared plumbing), `nbafa-hdfo-dev` (where Claude works) and `nbafa-hdfo-prod` (the live system). Project IDs are permanent once created.
2. **The services each project needs are switched on** (47 of the 54 items): BigQuery, Cloud Run, Scheduler, Storage, Secret Manager, Artifact Registry, IAM, logging/monitoring, billing. Switching a service on costs nothing by itself.
3. **A budget alarm**: A$15/month (about US$10, the G-08 ceiling) across all three projects, with emails at 50 %, 90 % and 100 %. It is an alert only. It does **not** stop spending.
4. **A private bucket for Terraform's own state**: `nbafa-hdfo-tfstate` in Sydney (australia-southeast1). It is versioned, public access is blocked, and it can't be deleted by accident.
5. **GitHub → Google login without stored keys (Workload Identity Federation)**:
   - Only this repository can sign in. It is matched on the repository's permanent numeric ID and owner ID, not just its name.
   - Any branch can deploy to **dev**.
   - Only `main` or a `v*` release tag can deploy to **prod**.
6. **Claude's access**: a `claude-agent` service account that only your own login can "act as".
   - **dev**: Editor, so Claude can build and test freely there.
   - **prod**: read-only access to logs and metrics. No data access and no write access.

## Cost
Essentially **$0 at idle**. Projects, enabled services, service accounts, the budget and WIF are free. The state bucket holds a few KB, well inside the free tier. Real spend begins only with later tasks (BigQuery queries, Cloud Run jobs), and the budget alert covers those.

## Risks and how they're handled
| Risk | Mitigation |
|---|---|
| Billing account ID leaks | It lives only in the gitignored `terraform.tfvars`. Saved plan files are also gitignored, because they contain it in cleartext. |
| A branch deploys to prod | The prod deploy account trusts only `main` or `v*` tags from this repo's numeric ID. |
| Claude damages prod | Claude has no prod write role. Prod changes go through CI after a PR merge. |
| Claude's dev role (Editor) is broad | Accepted for dev only. It will be narrowed to specific roles when the dev datasets and jobs exist (INFRA-002). |
| State bucket or pool deleted by mistake | `force_destroy = false` on the bucket, versioning plus 7-day soft delete, and `prevent_destroy` on the WIF pool. |
| The budget doesn't cap spend | This is a known GCP limitation. A spend-cap kill switch is a later task, if ever needed at this scale. |

## What happens on approval
1. Claude runs `terraform apply bootstrap.tfplan` from your laptop, using your gcloud login.
2. The state is moved into the new bucket (`terraform init -migrate-state`).
3. `terraform plan` is re-run, and must show **no changes** (AC evidence).
4. INFRA-002 (datasets and buckets for the draft slice) follows as its own PR and plan.
