# Terraform state for every stack (bootstrap, envs/dev, envs/prod), one
# prefix per stack. Lives in the admin project so that nothing done inside
# dev or prod (including deleting one) can touch the state.
resource "google_storage_bucket" "tfstate" {
  project  = google_project.this["admin"].project_id
  name     = "${var.prefix}-tfstate"
  location = upper(var.region)

  storage_class               = "STANDARD"
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  versioning {
    enabled = true
  }

  # Keep deleted objects recoverable for 7 days (GCS default).
  soft_delete_policy {
    retention_duration_seconds = 604800
  }

  # Bound storage growth: keep the 20 most recent non-current versions.
  lifecycle_rule {
    condition {
      num_newer_versions = 20
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  labels = merge(local.common_labels, { env = "admin" })

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.this["admin/storage.googleapis.com"]]
}
