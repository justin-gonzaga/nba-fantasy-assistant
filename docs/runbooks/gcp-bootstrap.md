# Runbook: GCP bootstrap (INFRA-001)

The one-time creation of the GCP foundation from `infra/terraform/bootstrap`: three projects (admin, dev, prod), their APIs, the Terraform state bucket, Workload Identity Federation (WIF) for GitHub Actions, the deploy and Claude service accounts, and the billing budget.

- **Who runs it**: the owner, with owner credentials. Claude never runs `apply` on this stack.
- **How often**: once, then only for rare changes (a new API, a new env).
- **What gets created**: `docs/infra/bootstrap-plan-summary.md` (plain English, with costs and what can't be undone).

> If a command isn't found, reload PATH first:
> ```powershell
> $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
> ```

## Part A: Owner prerequisites (done once, ~10 min)
These match Step 2 of `docs/runbooks/owner-setup.md`.

1. **Billing account**: console.cloud.google.com → Billing → create a billing account (card required). Note: its currency is fixed at creation; this account is **AUD**, so the budget is expressed in AUD.
2. **tfvars**: copy `infra/terraform/bootstrap/terraform.tfvars.example` to `terraform.tfvars` (gitignored) and set `billing_account`. Optional overrides:
   - `org_id = "…"`: create the projects under your organisation instead of with no parent (see the decision in the plan summary).
   - `prefix = "…"`: only if the default project IDs turn out to be taken.
3. **Login** (each opens a browser):
   ```powershell
   gcloud auth login
   gcloud auth application-default login
   ```
4. **Check** (read-only):
   ```powershell
   gcloud auth list                     # your account is ACTIVE
   gcloud billing accounts list         # OPEN = True
   terraform version                    # >= 1.16
   ```

## Part B: Plan, review, apply
Run from `infra/terraform/bootstrap`.

1. Initialise and check:
   ```powershell
   terraform init
   terraform fmt -check
   terraform validate
   ```
2. Plan and save it. PowerShell 5.1 splits `-out=a.b` at the dot, so quote the flag:
   ```powershell
   terraform plan "-out=bootstrap.tfplan"
   ```
   Expect `Plan: 54 to add, 0 to change, 0 to destroy.` Compare with `docs/infra/bootstrap-plan-summary.md`.
3. **Owner approval point.** Applying creates billable projects with permanent IDs. Apply only the saved plan:
   ```powershell
   terraform apply bootstrap.tfplan
   ```
4. If the first apply fails part-way with an error such as `SERVICE_DISABLED`, `API has not been used in project … or it is disabled`, or `Permission 'iam.serviceAccounts.create' denied` shortly after a project was created: API enablement takes a minute or two to propagate. Wait two minutes, then run `terraform plan "-out=bootstrap.tfplan"` and `terraform apply bootstrap.tfplan` again. Terraform only creates what is still missing.
5. If it fails with `Cloud billing quota exceeded`: the billing account has a limit on linked projects. Request an increase at https://support.google.com/code/contact/billing_quota_increase and re-run.
6. Record the outputs (not secrets, but keep them out of public issues):
   ```powershell
   terraform output
   ```
7. Delete the saved plan (it contains the billing account ID in cleartext): `Remove-Item bootstrap.tfplan`.

## Part C: Migrate the state to GCS (right after the first apply)
The bootstrap starts with **local** state because its bucket doesn't exist until the first apply.

1. In `backend.tf`, uncomment the `terraform { backend "gcs" { … } }` block. Check that `bucket` equals `terraform output -raw state_bucket` (default `nbafa-hdfo-tfstate`), and keep `prefix = "bootstrap"`.
2. Migrate:
   ```powershell
   terraform init -migrate-state
   ```
   Answer `yes` when asked to copy the existing state to the new backend.
3. Verify:
   ```powershell
   terraform plan                                   # expect: No changes.
   gcloud storage ls gs://nbafa-hdfo-tfstate/bootstrap/   # default.tfstate is listed
   ```
4. Remove the local copies: `Remove-Item terraform.tfstate, terraform.tfstate.backup`.
5. Commit the uncommented `backend.tf` on a branch (INFRA-001 follow-up commit; Tier B review).

Later stacks use the same bucket with their own prefix: `envs/dev`, `envs/prod`.

**Rollback of the migration**: comment the block out again and run `terraform init -migrate-state` to copy the state back to a local file.

## Part D: Point Claude at dev only (AC5)
Claude's local gcloud should impersonate the `claude-agent` service account, which has dev access plus read-only prod logs/metrics. Run this once in your own terminal, **after** the apply:

```powershell
$SA = terraform output -raw claude_service_account
gcloud config configurations create claude-dev
gcloud config set account <your-google-account-email>
gcloud config set project nbafa-hdfo-dev
gcloud config set auth/impersonate_service_account $SA
gcloud auth application-default login --impersonate-service-account=$SA
```

- Verify (should succeed): `gcloud projects describe nbafa-hdfo-dev`.
- Verify (should fail with PERMISSION_DENIED): `gcloud storage buckets list --project=nbafa-hdfo-prod`.
- To run the bootstrap again as yourself: `gcloud config configurations activate default` and `gcloud auth application-default login` (without impersonation). Switch back afterwards.

Your own user credentials still exist on the laptop, so this is a configured default plus the agent `PreToolUse` hook (security standard §6), not a hard boundary. Prod changes still happen only through CI.

## Part E: Wire CI (INFRA-002 onward)
GitHub Actions authenticates with `google-github-actions/auth` using the outputs:
- `workload_identity_provider`
- `deploy_service_accounts.dev` / `.prod`

The job needs `permissions: id-token: write`. A workflow run from any branch or PR can impersonate `deploy@…-dev`. Only runs on `refs/heads/main` or a `refs/tags/v*` tag can impersonate `deploy@…-prod`. Protect `v*` tags with a ruleset so only the owner can create them.

## Troubleshooting
| Symptom | Cause / fix |
|---|---|
| `The billing account … currency … does not match` on the budget | Set `budget_currency` to the account's currency (`gcloud billing accounts describe <ID> --format="value(currencyCode)"`). |
| `Your application is authenticating by using local Application Default Credentials. The billingbudgets.googleapis.com API requires a quota project` | The `google.billing` provider alias sets the admin project as the quota project. Re-run apply once `admin/billingbudgets` is enabled. |
| `Requested entity already exists` on a project | The project ID is taken globally. Choose a new `prefix` (before the first successful apply only). |
| `Error acquiring the state lock` (after migration) | Another plan/apply is running. If a crashed run left the lock: `terraform force-unlock <LOCK_ID>`, only when sure nothing else is running. |
