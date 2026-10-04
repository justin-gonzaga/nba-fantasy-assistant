# Serving (INFRA-003): the image registry, the bucket the API reads (D-62) and the app's secrets.
# Secrets are created as names only: the owner adds their values; Terraform never holds them.

resource "google_project_service" "serving" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

locals {
  deploy_member = "serviceAccount:deploy@${local.project_id}.iam.gserviceaccount.com"
  app_secrets = toset([
    "telegram-bot-token",
    "yahoo-client-id",
    "yahoo-client-secret",
    "yahoo-refresh-token",
    "anthropic-api-key",
  ])
  secret_readers = { for pair in setproduct(tolist(local.app_secrets), ["transform", "api"]) : "${pair[0]}/${pair[1]}" => pair }
}

# ---------- Images ----------
resource "google_artifact_registry_repository" "images" {
  project       = local.project_id
  location      = var.region
  repository_id = "images"
  format        = "DOCKER"
  description   = "The api/job image (FND-015); deploys pin a digest"
  labels        = local.labels

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 3 # ~0.35 GB each, ~1 GB kept: about US$0.05/month over the 0.5 GB free tier
    }
  }
  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"
    condition {
      tag_state  = "UNTAGGED"
      older_than = "1209600s" # 14 days
    }
  }
  depends_on = [google_project_service.serving]
}

resource "google_artifact_registry_repository_iam_member" "ci_push" {
  project    = local.project_id
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = local.deploy_member
}

# ---------- The serve bucket: what the pipeline publishes and the API reads ----------
resource "google_storage_bucket" "serve" {
  project                     = local.project_id
  name                        = "${var.prefix}-${var.env}-serve"
  location                    = upper(var.region)
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = !local.is_prod
  labels                      = local.labels
}

resource "google_storage_bucket_iam_member" "api_serve_read" {
  bucket = google_storage_bucket.serve.name
  role   = "roles/storage.objectViewer"
  member = local.sa["api"]
}

resource "google_storage_bucket_iam_member" "transform_serve_write" {
  bucket = google_storage_bucket.serve.name
  role   = "roles/storage.objectUser" # create and replace the day's brief
  member = local.sa["transform"]
}

# ---------- Secrets (names only) ----------
resource "google_secret_manager_secret" "app" {
  for_each  = local.app_secrets
  project   = local.project_id
  secret_id = each.value
  labels    = local.labels
  replication {
    auto {}
  }
  depends_on = [google_project_service.serving]
}

resource "google_secret_manager_secret_iam_member" "readers" {
  for_each  = local.secret_readers
  project   = local.project_id
  secret_id = google_secret_manager_secret.app[each.value[0]].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.sa[each.value[1]]
}
