# Plan-time policy tests with a mocked provider: nothing touches Google Cloud.
# Run: terraform -chdir=infra/terraform/modules/env test

mock_provider "google" {}
mock_provider "google-beta" {}

run "dev_buckets_expire_and_are_unversioned" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_storage_bucket.raw.name == "nbafa-hdfo-dev-raw"
    error_message = "raw bucket naming convention"
  }
  assert {
    condition     = one(flatten([for r in google_storage_bucket.raw.lifecycle_rule : [for c in r.condition : c.age]])) == 30
    error_message = "dev raw bucket must expire objects after 30 days (I3)"
  }
  assert {
    condition     = google_storage_bucket.raw.versioning[0].enabled == false
    error_message = "dev raw bucket is not versioned"
  }
  assert {
    condition     = length(google_storage_bucket.raw.retention_policy) == 0
    error_message = "dev raw bucket has no retention policy"
  }
  assert {
    condition     = length(google_project_iam_member.ci_bigquery) == 2
    error_message = "dev grants the CI deploy SA BigQuery user/jobUser for ephemeral datasets"
  }
}

run "prod_raw_is_versioned_retained_and_never_expires" {
  command = plan
  variables {
    env                = "prod"
    raw_retention_days = 30
    raw_readers        = ["serviceAccount:ingest-sa@nbafa-hdfo-dev.iam.gserviceaccount.com"]
  }
  assert {
    condition     = google_storage_bucket.raw.versioning[0].enabled
    error_message = "prod raw bucket must be versioned"
  }
  assert {
    condition     = tonumber(google_storage_bucket.raw.retention_policy[0].retention_period) == 30 * 86400 && google_storage_bucket.raw.retention_policy[0].is_locked == false
    error_message = "prod raw retention policy set and not locked"
  }
  assert {
    condition     = length(google_storage_bucket.raw.lifecycle_rule) == 0
    error_message = "prod raw objects never expire"
  }
  assert {
    condition     = google_storage_bucket.raw.force_destroy == false && google_storage_bucket.exports.force_destroy == false
    error_message = "prod buckets can't be force-destroyed"
  }
  assert {
    condition     = length(google_project_iam_member.ci_bigquery) == 0
    error_message = "CI gets no BigQuery access in prod"
  }
  assert {
    condition     = google_storage_bucket_iam_member.raw_readers["serviceAccount:ingest-sa@nbafa-hdfo-dev.iam.gserviceaccount.com"].role == "roles/storage.objectViewer"
    error_message = "dev SAs get read-only access to prod raw (I3 A)"
  }
}

run "datasets_use_dbt_native_layers" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = toset(keys(google_bigquery_dataset.this)) == toset(["raw", "staging", "intermediate", "marts", "features", "predictions", "recs"])
    error_message = "dataset set"
  }
  assert {
    condition     = alltrue([for d in google_bigquery_dataset.this : d.delete_contents_on_destroy == false])
    error_message = "datasets never drop contents on destroy"
  }
}

run "least_privilege_roles" {
  command = plan
  variables {
    env = "prod"
  }
  assert {
    condition     = toset([for m in google_storage_bucket_iam_member.ingest_raw : m.role]) == toset(["roles/storage.objectCreator", "roles/storage.objectViewer"])
    error_message = "ingest may only create and read raw objects (no delete/overwrite)"
  }
  assert {
    condition     = alltrue([for m in google_bigquery_dataset_iam_member.api_view : m.role == "roles/bigquery.dataViewer"])
    error_message = "api is read-only on data"
  }
  assert {
    condition     = !contains(keys(google_bigquery_dataset_iam_member.transform_edit), "raw")
    error_message = "transform cannot edit the raw dataset"
  }
  assert {
    condition     = google_bigquery_dataset_iam_member.transform_raw_view.role == "roles/bigquery.dataViewer"
    error_message = "transform reads raw"
  }
}

run "rejects_unknown_env" {
  command = plan
  variables {
    env = "staging"
  }
  expect_failures = [var.env]
}

run "ci_reads_dev_raw_only" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = length(google_storage_bucket_iam_member.ci_raw_read) == 1 && google_storage_bucket_iam_member.ci_raw_read[0].role == "roles/storage.objectViewer"
    error_message = "CI (deploy SA) reads dev raw files, read-only"
  }
  assert {
    condition     = length(google_bigquery_dataset_iam_member.ci_raw_view) == 1 && google_bigquery_dataset_iam_member.ci_raw_view[0].role == "roles/bigquery.dataViewer"
    error_message = "CI (deploy SA) reads the dev raw dataset, read-only"
  }
}

run "ci_has_no_prod_raw_access" {
  command = plan
  variables {
    env = "prod"
  }
  assert {
    condition     = length(google_storage_bucket_iam_member.ci_raw_read) == 0 && length(google_bigquery_dataset_iam_member.ci_raw_view) == 0
    error_message = "CI must not read prod raw"
  }
}

run "website_is_hosted_and_only_ci_deploys_it" {
  command = plan
  variables {
    env = "prod"
  }
  assert {
    condition     = google_firebase_hosting_site.web.site_id == "nbafa-hdfo-prod"
    error_message = "the site id is the project id (<project>.web.app)"
  }
  assert {
    condition     = google_project_iam_member.deploy_hosting.role == "roles/firebasehosting.admin" && google_project_iam_member.deploy_hosting.member == "serviceAccount:deploy@nbafa-hdfo-prod.iam.gserviceaccount.com"
    error_message = "only the CI deploy SA gets hosting admin"
  }
}

run "images_are_registered_and_pruned" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_artifact_registry_repository.images.format == "DOCKER" && google_artifact_registry_repository.images.repository_id == "images"
    error_message = "one Docker repository per env, named images"
  }
  assert {
    condition     = length(google_artifact_registry_repository.images.cleanup_policies) == 2
    error_message = "the registry keeps recent images and deletes old untagged ones"
  }
  assert {
    condition     = google_artifact_registry_repository_iam_member.ci_push.role == "roles/artifactregistry.writer" && google_artifact_registry_repository_iam_member.ci_push.member == "serviceAccount:deploy@nbafa-hdfo-dev.iam.gserviceaccount.com"
    error_message = "only the CI deploy identity pushes images"
  }
}

run "serve_bucket_is_private_and_least_privilege" {
  command = plan
  variables {
    env = "prod"
  }
  assert {
    condition     = google_storage_bucket.serve.name == "nbafa-hdfo-prod-serve" && google_storage_bucket.serve.public_access_prevention == "enforced"
    error_message = "the serve bucket is named by convention and never public"
  }
  assert {
    condition     = google_storage_bucket_iam_member.api_serve_read.role == "roles/storage.objectViewer"
    error_message = "the api reads the serve bucket, read-only"
  }
  assert {
    condition     = google_storage_bucket_iam_member.transform_serve_write.role == "roles/storage.objectUser"
    error_message = "the pipeline (transform) publishes and replaces serve objects"
  }
}

run "secrets_have_no_values_and_scoped_readers" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = toset(keys(google_secret_manager_secret.app)) == toset(["telegram-bot-token", "yahoo-client-id", "yahoo-client-secret", "yahoo-refresh-token", "anthropic-api-key"])
    error_message = "the app's secrets exist as names only (the owner adds values)"
  }
  assert {
    condition     = alltrue([for m in google_secret_manager_secret_iam_member.readers : m.role == "roles/secretmanager.secretAccessor"])
    error_message = "readers may only access secret versions"
  }
  assert {
    condition     = length(google_secret_manager_secret_iam_member.readers) == 10
    error_message = "exactly the transform and api identities read each of the 5 secrets"
  }
}

run "api_runs_privately_as_the_api_identity" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_cloud_run_v2_service.api.template[0].service_account == "api-sa@nbafa-hdfo-dev.iam.gserviceaccount.com"
    error_message = "the API runs as the api identity (read-only on data)"
  }
  assert {
    condition     = one([for e in google_cloud_run_v2_service.api.template[0].containers[0].env : e.value if e.name == "DATA_ROOT"]) == "gs://nbafa-hdfo-dev-serve"
    error_message = "the API reads the serve bucket (D-62)"
  }
  assert {
    condition     = google_cloud_run_v2_service.api.template[0].scaling[0].min_instance_count == 0
    error_message = "scales to zero (free tier)"
  }
  assert {
    condition     = google_cloud_run_v2_service_iam_member.ci_deploy.role == "roles/run.developer" && google_cloud_run_v2_service_iam_member.ci_deploy.member == "serviceAccount:deploy@nbafa-hdfo-dev.iam.gserviceaccount.com"
    error_message = "only CI deploys revisions; no public invoker until sign-in exists (APP-005)"
  }
  assert {
    condition     = google_service_account_iam_member.ci_acts_as_api.role == "roles/iam.serviceAccountUser"
    error_message = "CI may deploy revisions that run as the api identity"
  }
}

run "api_fails_closed_without_an_allowlist" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = one([for e in google_cloud_run_v2_service.api.template[0].containers[0].env : e.value if e.name == "FIREBASE_PROJECT"]) == "nbafa-hdfo-dev"
    error_message = "sign-in tokens are checked against this env's project"
  }
  assert {
    condition     = nonsensitive(one([for e in google_cloud_run_v2_service.api.template[0].containers[0].env : e.value if e.name == "ALLOWED_EMAILS"])) == ""
    error_message = "no allowlist by default: the API refuses to start until the owner sets one"
  }
  assert {
    condition     = length(google_cloud_run_v2_service_iam_member.public) == 0
    error_message = "the API is private unless the env opts in"
  }
  assert {
    condition     = one([for e in google_cloud_run_v2_service.api.template[0].containers[0].env : e.value if e.name == "CORS_ORIGINS"]) == "https://nbafa-hdfo-dev.web.app,https://nbafa-hdfo-dev.firebaseapp.com"
    error_message = "only this env's website origins may call the API from browsers"
  }
}

run "api_public_only_when_opted_in" {
  command = plan
  variables {
    env        = "dev"
    api_public = true
  }
  assert {
    condition     = google_cloud_run_v2_service_iam_member.public[0].member == "allUsers" && google_cloud_run_v2_service_iam_member.public[0].role == "roles/run.invoker"
    error_message = "opting in lets browsers invoke the API (sign-in is enforced by the API itself)"
  }
  assert {
    condition     = contains(keys(google_project_service.firebase), "identitytoolkit.googleapis.com")
    error_message = "Firebase Auth (Google sign-in) is enabled"
  }
}

run "daily_chain_runs_in_the_cloud_on_a_schedule" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_cloud_run_v2_job.daily.template[0].template[0].service_account == "transform-sa@nbafa-hdfo-dev.iam.gserviceaccount.com"
    error_message = "the cloud chain runs as the transform identity"
  }
  assert {
    condition     = google_cloud_run_v2_job.daily.template[0].template[0].containers[0].args == tolist(["job", "cloud"])
    error_message = "the job runs `fantasy run cloud` (no NBA fetch: D-63)"
  }
  assert {
    condition     = one([for e in google_cloud_run_v2_job.daily.template[0].template[0].containers[0].env : e.value if e.name == "WORK_ROOT"]) == "gs://nbafa-hdfo-dev-serve" && one([for e in google_cloud_run_v2_job.daily.template[0].template[0].containers[0].env : e.value if e.name == "DATA_ROOT"]) == "gs://nbafa-hdfo-dev-raw"
    error_message = "it works in the serve bucket and reads raw from the raw bucket"
  }
  assert {
    condition     = google_cloud_scheduler_job.daily.schedule == "45 7 * * *" && google_cloud_scheduler_job.daily.time_zone == "Australia/Sydney"
    error_message = "07:45 Sydney, after the PC's 07:30 fetch"
  }
  assert {
    condition     = google_storage_bucket_iam_member.transform_raw_create.role == "roles/storage.objectCreator"
    error_message = "the chain may add raw snapshots (the injury report) but never overwrite or delete them"
  }
}

run "users_live_in_firestore_native_written_only_by_the_api" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_firestore_database.app.name == "(default)" && google_firestore_database.app.type == "FIRESTORE_NATIVE" && google_firestore_database.app.location_id == "australia-southeast1"
    error_message = "one Firestore Native (default) database in Sydney (G-25)"
  }
  assert {
    condition     = google_project_iam_member.api_datastore.role == "roles/datastore.user"
    error_message = "the api identity reads/writes documents (no Firestore admin)"
  }
  assert {
    condition     = google_firebaserules_release.firestore.name == "cloud.firestore"
    error_message = "the rules are released for Firestore"
  }
  assert {
    condition     = strcontains(one(one(google_firebaserules_ruleset.firestore.source).files).content, "allow read, write: if false;") && !strcontains(one(one(google_firebaserules_ruleset.firestore.source).files).content, "if true")
    error_message = "client security rules deny everything (API-only writes)"
  }
  assert {
    condition     = google_bigquery_dataset.app_raw.dataset_id == "app_raw" && google_bigquery_dataset.app_raw.location == "australia-southeast1" && google_bigquery_dataset.app_raw.delete_contents_on_destroy == false
    error_message = "the Firestore copy lands in app_raw, never dropped on destroy"
  }
  assert {
    condition     = google_firestore_database.app.delete_protection_state == "DELETE_PROTECTION_DISABLED"
    error_message = "dev's database can be recreated"
  }
}

run "prod_firestore_is_delete_protected" {
  command = plan
  variables {
    env = "prod"
  }
  assert {
    condition     = google_firestore_database.app.delete_protection_state == "DELETE_PROTECTION_ENABLED" && google_firestore_database.app.deletion_policy == "ABANDON"
    error_message = "prod user data can't be deleted by Terraform"
  }
}

run "watchdog_checks_daily_and_uptime" {
  command = plan
  variables {
    env = "dev"
  }
  assert {
    condition     = google_cloud_run_v2_job.watchdog.template[0].template[0].containers[0].args == tolist(["fantasy", "watchdog", "--mode", "daily"])
    error_message = "the job runs the daily checks by default"
  }
  assert {
    condition     = google_cloud_scheduler_job.watchdog_daily.schedule == "0 9 * * *" && google_cloud_scheduler_job.watchdog_uptime.schedule == "*/15 * * * *"
    error_message = "09:00 Sydney daily checks; uptime every 15 minutes"
  }
  assert {
    condition     = google_cloud_run_v2_job.watchdog.template[0].template[0].max_retries == 0
    error_message = "no retries: a retry would double-alert"
  }
}
