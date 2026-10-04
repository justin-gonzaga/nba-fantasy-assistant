# Per-environment storage and identities (INFRA-002).
# Naming: buckets  <prefix>-<env>-<purpose>        e.g. nbafa-hdfo-prod-raw
#         datasets <layer>                          (one project per env, so no env suffix)
#         SAs      <workload>-sa@<prefix>-<env>.iam e.g. ingest-sa@nbafa-hdfo-dev.iam.gserviceaccount.com (IDs need 6+ chars)

locals {
  project_id = "${var.prefix}-${var.env}"
  is_prod    = var.env == "prod"

  labels = {
    app        = "nba-fantasy-assistant"
    env        = var.env
    managed_by = "terraform"
    stack      = "env"
  }

  # dbt-native layer names (S-10 B) plus the ML/decision artefact datasets.
  datasets = {
    raw          = "Bronze: BigQuery external tables over the raw GCS files (immutable)"
    staging      = "Typed, deduplicated models, one per source"
    intermediate = "Business logic joins and aggregates"
    marts        = "Serving tables for decisions and the UI"
    features     = "Point-in-time feature tables"
    predictions  = "Model outputs (projections, distributions)"
    recs         = "Recommendations, explanations and their outcomes"
  }

  # transform (the pipeline/dbt identity) owns every layer except raw, which it only reads.
  transform_datasets = [for d in keys(local.datasets) : d if d != "raw"]
  api_datasets       = ["marts", "predictions", "recs"]

  workloads = {
    ingest    = "Writes raw source payloads (create only, never delete)"
    transform = "Runs dbt and model jobs: edits its datasets, reads raw"
    api       = "Serves the API: reads marts/predictions/recs, runs queries"
    scheduler = "Cloud Scheduler: invokes Cloud Run jobs"
  }
}

resource "google_project_service" "extra" {
  for_each           = toset(["policytroubleshooter.googleapis.com"])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

# ---------- Buckets ----------
resource "google_storage_bucket" "raw" {
  project                     = local.project_id
  name                        = "${var.prefix}-${var.env}-raw"
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = local.labels

  versioning {
    enabled = local.is_prod
  }

  dynamic "retention_policy" {
    for_each = local.is_prod && var.raw_retention_days > 0 ? [1] : []
    content {
      retention_period = var.raw_retention_days * 86400
      is_locked        = false
    }
  }

  dynamic "lifecycle_rule" {
    for_each = local.is_prod ? [] : [1]
    content {
      condition {
        age = var.dev_lifecycle_days
      }
      action {
        type = "Delete"
      }
    }
  }
}

resource "google_storage_bucket" "exports" {
  project                     = local.project_id
  name                        = "${var.prefix}-${var.env}-exports"
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = !local.is_prod
  labels                      = local.labels

  lifecycle_rule {
    condition {
      age = local.is_prod ? var.exports_lifecycle_days : var.dev_lifecycle_days
    }
    action {
      type = "Delete"
    }
  }
}

# ---------- BigQuery datasets ----------
resource "google_bigquery_dataset" "this" {
  for_each                   = local.datasets
  project                    = local.project_id
  dataset_id                 = each.key
  location                   = var.region
  description                = each.value
  labels                     = local.labels
  delete_contents_on_destroy = false
}

# ---------- Service accounts ----------
resource "google_service_account" "workload" {
  for_each     = local.workloads
  project      = local.project_id
  account_id   = "${each.key}-sa"
  display_name = "${each.key} (${var.env})"
  description  = each.value
}

locals {
  sa = { for k, s in google_service_account.workload : k => s.member }
}

# ingest: create + read raw objects. objectCreator cannot delete or overwrite (immutable bronze).
resource "google_storage_bucket_iam_member" "ingest_raw" {
  for_each = toset(["roles/storage.objectCreator", "roles/storage.objectViewer"])
  bucket   = google_storage_bucket.raw.name
  role     = each.value
  member   = local.sa.ingest
}

# transform: read raw files (external tables), edit its datasets, read the raw dataset, run jobs.
resource "google_storage_bucket_iam_member" "transform_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = local.sa.transform
}

resource "google_storage_bucket_iam_member" "transform_exports" {
  bucket = google_storage_bucket.exports.name
  role   = "roles/storage.objectAdmin"
  member = local.sa.transform
}

resource "google_bigquery_dataset_iam_member" "transform_edit" {
  for_each   = toset(local.transform_datasets)
  project    = local.project_id
  dataset_id = google_bigquery_dataset.this[each.value].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = local.sa.transform
}

resource "google_bigquery_dataset_iam_member" "transform_raw_view" {
  project    = local.project_id
  dataset_id = google_bigquery_dataset.this["raw"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = local.sa.transform
}

# api: read serving datasets, run query jobs. No write anywhere.
resource "google_bigquery_dataset_iam_member" "api_view" {
  for_each   = toset(local.api_datasets)
  project    = local.project_id
  dataset_id = google_bigquery_dataset.this[each.value].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = local.sa.api
}

resource "google_project_iam_member" "job_user" {
  for_each = toset(["transform", "api"])
  project  = local.project_id
  role     = "roles/bigquery.jobUser"
  member   = local.sa[each.value]
}

# scheduler: invoke Cloud Run jobs/services (the jobs themselves come in INFRA-004).
resource "google_project_iam_member" "scheduler_invoker" {
  project = local.project_id
  role    = "roles/run.invoker"
  member  = local.sa.scheduler
}

# Cross-env read of this env's raw bucket (prod → dev SAs, I3 A).
resource "google_storage_bucket_iam_member" "raw_readers" {
  for_each = toset(var.raw_readers)
  bucket   = google_storage_bucket.raw.name
  role     = "roles/storage.objectViewer"
  member   = each.value
}

# CI (dev only): the deploy SA creates per-PR ephemeral datasets (ci_pr<N>_*) and owns what it creates.
resource "google_project_iam_member" "ci_bigquery" {
  for_each = local.is_prod ? toset([]) : toset(["roles/bigquery.user", "roles/bigquery.jobUser"])
  project  = local.project_id
  role     = each.value
  member   = "serviceAccount:deploy@${local.project_id}.iam.gserviceaccount.com"
}

# CI (dev only): dbt in CI reads the raw layer: the files behind the external tables and the
# raw dataset's table definitions. Read-only; prod raw is never readable from CI (FND-017).
resource "google_storage_bucket_iam_member" "ci_raw_read" {
  count  = local.is_prod ? 0 : 1
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:deploy@${local.project_id}.iam.gserviceaccount.com"
}

resource "google_bigquery_dataset_iam_member" "ci_raw_view" {
  count      = local.is_prod ? 0 : 1
  project    = local.project_id
  dataset_id = google_bigquery_dataset.this["raw"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:deploy@${local.project_id}.iam.gserviceaccount.com"
}
