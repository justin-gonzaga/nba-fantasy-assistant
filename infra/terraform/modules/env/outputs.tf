output "project_id" {
  description = "The environment's project ID."
  value       = local.project_id
}

output "buckets" {
  description = "Bucket names by purpose."
  value = {
    raw     = google_storage_bucket.raw.name
    exports = google_storage_bucket.exports.name
  }
}

output "datasets" {
  description = "BigQuery dataset IDs."
  value       = sort(keys(google_bigquery_dataset.this))
}

output "service_accounts" {
  description = "Workload service account emails."
  value       = { for k, s in google_service_account.workload : k => s.email }
}

output "serving" {
  description = "Where images and published outputs live (INFRA-003)."
  value = {
    image_repo   = "${google_artifact_registry_repository.images.location}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.images.repository_id}"
    serve_bucket = "gs://${google_storage_bucket.serve.name}"
    api_url      = google_cloud_run_v2_service.api.uri
  }
}

output "web_build_env" {
  description = "The website's live-mode build variables (public values; WEB-013)."
  value = {
    VITE_API_URL          = google_cloud_run_v2_service.api.uri
    VITE_FIREBASE_API_KEY = data.google_firebase_web_app_config.web.api_key
    # The site's own domain, not <project>.firebaseapp.com: a same-site sign-in handler works in
    # browsers that block third-party storage (a cross-site popup failed with auth/internal-error).
    # Its /__/auth/handler must be an authorised redirect URI on the Google OAuth web client.
    VITE_FIREBASE_AUTH_DOMAIN = "${google_firebase_hosting_site.web.site_id}.web.app"
    VITE_FIREBASE_PROJECT_ID  = local.project_id
    VITE_FIREBASE_APP_ID      = google_firebase_web_app.web.app_id
  }
}
