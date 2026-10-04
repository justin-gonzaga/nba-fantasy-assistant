# Runbook: hosting the web API and the website (owner steps)

What runs where (D-59, D-62):
- **Website**: Firebase Hosting, deployed by CI. Without `VITE_API_URL` it shows sample data.
- **API**: Cloud Run service `api` (australia-southeast1), deployed by CI by image digest. It reads
  `gs://nbafa-hdfo-dev-serve` and is **private** until Google sign-in exists (APP-005).
- **Data**: the 07:30 chain on your PC writes `data/` and, when `SERVE_ROOT` is set, copies the day's outputs
  to the serve bucket (`publish` job).

## 1. Create the cloud resources (once, ~5 minutes)
From the repo root, on `main`:

First, tell the API who may sign in (this file is git-ignored, so your email never reaches the repo):

```powershell
Copy-Item infra/terraform/envs/dev/owner.auto.tfvars.example infra/terraform/envs/dev/owner.auto.tfvars
notepad infra/terraform/envs/dev/owner.auto.tfvars   # put your Google account's email
```
Without it the API refuses to start (it fails closed).

```powershell
git checkout main; git pull
terraform -chdir=infra/terraform/envs/dev init -upgrade
terraform -chdir=infra/terraform/envs/dev apply
```
Check the plan says **34 to add, 0 to change, 0 to destroy** before typing `yes`: Firebase Hosting + sign-in, the image
registry, the serve bucket, 5 secret names (no values), the `api` Cloud Run service and their permissions.

Cost: within the free tiers, apart from about US$0.05/month of image storage.

## 2. Turn on the CI deploys (GitHub → Settings → Secrets and variables → Actions → Variables)
- `FIREBASE_ENABLED` = `true`: every merge deploys the website; PRs get preview links.
- `CLOUD_RUN_ENABLED` = `true`: every merge builds, pushes and deploys the API image.

## 3. Publish the daily outputs to the bucket
Add one line to `.env` (Claude never reads that file):

```
SERVE_ROOT=gs://nbafa-hdfo-dev-serve
```
Your PC's Google login (`gcloud auth application-default login`, already done for BigQuery) can write there.
The next 07:30 run then copies the brief, the week projection and the run log.

## 4. Enable Google sign-in (once, 1 minute)
Firebase console -> project `nbafa-hdfo-dev` -> Authentication -> Get started -> Sign-in method -> Google ->
Enable -> Save. The API checks every sign-in token and your email (APP-005).

Then let the sign-in run on the site's own domain (browsers that block third-party storage break a
cross-site popup with `auth/internal-error`): Google Cloud console -> APIs & Services -> Credentials ->
OAuth 2.0 Client IDs -> "Web client (auto created by Google Service)" -> Authorised redirect URIs -> Add
`https://nbafa-hdfo-dev.web.app/__/auth/handler` -> Save. The site's `VITE_FIREBASE_AUTH_DOMAIN` is
`nbafa-hdfo-dev.web.app` (terraform output `web_build_env`).

## 5. Switch the website to live mode (Claude can do this once the apply is done)
`terraform -chdir=infra/terraform/envs/dev output web_build_env` prints five public values (not secrets). Each
becomes a GitHub repo variable of the same name (`VITE_API_URL`, `VITE_FIREBASE_API_KEY`,
`VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_APP_ID`). The next deploy then shows
"Sign in with Google"; until all five are set, the site stays on sample data.

## Users and invites (APP-008, D-64)
Who may sign in now lives in Firestore, written only by the API (the `api-sa` identity, `roles/datastore.user`);
the database's security rules deny every browser/mobile client. `ALLOWED_EMAILS` (`api_allowed_emails` in your
`owner.auto.tfvars`) only bootstraps the **first owner**: the first allowlisted Google account to sign in while
no owner exists becomes the owner. After that, access comes from invites, and editing the allowlist changes nothing.

**1. Apply (owner, once per env, ~2 minutes).** `terraform -chdir=infra/terraform/envs/dev plan` should add only:
the `firestore.googleapis.com` and `firebaserules.googleapis.com` services, the `(default)` Firestore Native
database in `australia-southeast1`, the deny-all rules (ruleset + `cloud.firestore` release), the API's
`roles/datastore.user` binding and the `app_raw` BigQuery dataset. Then `apply`.
**Then switch the API to Firestore**: add `users_backend = "firestore"` to `owner.auto.tfvars` and `apply` again
(it only changes the API's `USERS_BACKEND` env). Until then the API keeps the old behaviour (`memory`: the allowlist
bootstraps you as owner on each start), so deploying this code before your apply never breaks sign-in.
Sign in on the website once: you're the owner (`GET /me`).
Prod's database is delete-protected; dev's isn't.

**2. Stream to BigQuery (owner, once per env, ~10 minutes).** Install the Firebase extension "Stream Firestore
to BigQuery" (`firebase/firestore-bigquery-export`) twice, once per collection:
```
firebase ext:install firebase/firestore-bigquery-export --project nbafa-hdfo-dev
```
| Parameter | users instance | invites instance |
|---|---|---|
| Instance id | `bq-users` | `bq-invites` |
| Collection path | `users` | `invites` |
| Dataset ID | `app_raw` | `app_raw` |
| Table ID | `users` | `invites` |
| BigQuery dataset location | `australia-southeast1` | `australia-southeast1` |
| Cloud Functions location | `australia-southeast1` | `australia-southeast1` |

The extension creates `app_raw.<table>_raw_changelog` and a `<table>_raw_latest` view, and its own service
account with BigQuery access. It runs a small Cloud Function per write (users change rarely: ~US$0 in the free
tier). Check it: sign in once (updates your `lastSeenAt` at most every 15 min) or invite someone, then within
5 minutes
`bq query --use_legacy_sql=false 'SELECT document_id, operation, timestamp FROM app_raw.users_raw_changelog ORDER BY timestamp DESC LIMIT 5'`
shows the row. Invited people's emails land in this dataset: it's private like the rest of the project.

**3. Invite someone (until the admin screen, WEB-015).** As the owner, with your sign-in token from the website
(browser dev tools → a request's `Authorization: Bearer …` header):
```
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"email":"friend@example.com"}' <service URL>/invites           # 201, or 200 if already invited
curl -H "Authorization: Bearer $TOKEN" <service URL>/invites           # status open | expired | claimed
curl -H "Authorization: Bearer $TOKEN" <service URL>/members
curl -X DELETE -H "Authorization: Bearer $TOKEN" <service URL>/members/<uid>   # locked out on their next request
```
They sign in with that Google account within 14 days; the first sign-in claims the invite and binds it to their
account (uid), so a later email change keeps their access. `{"email": …, "role": "owner"}` makes a co-owner;
the last owner can't be removed.

**Local tests against Firestore.** The contract tests (`apps/api/tests/test_users_store.py`) run on the Firestore
emulator: `gcloud components install cloud-firestore-emulator` (needs Java 21+ on PATH), then
`gcloud emulators firestore start --host-port=127.0.0.1:8681` and
`FIRESTORE_EMULATOR_HOST=127.0.0.1:8681 uv run pytest apps/api/tests/test_users_store.py`. Without it they skip;
CI always runs them (an emulator container in the `test-py` job).

## 6. Later (Claude does these)
- INFRA-006: move the 07:30 chain itself to Cloud Run jobs + Cloud Scheduler, so your PC can be off.

## Checking it works
- `gcloud run services describe api --region australia-southeast1 --project nbafa-hdfo-dev`
- As the owner (authorised): `curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" <service URL>/system/freshness`
