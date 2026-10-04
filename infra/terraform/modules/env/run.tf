# The API on Cloud Run (INFRA-004). Terraform owns the service's shape; CI deploys each revision's
# image by digest, so the image here is a placeholder that Terraform then ignores.
# No public invoker: the service stays private until app-level sign-in exists (APP-005).

resource "google_cloud_run_v2_service" "api" {
  project             = local.project_id
  name                = "api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL" # reachable, but IAM keeps it private: no public invoker
  deletion_protection = local.is_prod
  labels              = local.labels

  template {
    service_account = "api-sa@${local.project_id}.iam.gserviceaccount.com" # known at plan time
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # placeholder until CI's first deploy
      env {
        name  = "DATA_ROOT"
        value = "gs://${google_storage_bucket.serve.name}"
      }
      env {
        name  = "APP_ENV"
        value = var.env
      }
      env {
        name  = "FIREBASE_PROJECT" # sign-in tokens must be issued for this project
        value = local.project_id
      }
      env {
        name  = "ALLOWED_EMAILS" # empty: the API refuses to start (fails closed)
        value = var.api_allowed_emails
      }
      env {
        name  = "USERS_BACKEND" # APP-008: "firestore" after the apply that creates the database
        value = var.users_backend
      }
      env {
        name  = "CORS_ORIGINS" # the website (Firebase Hosting) may call the API from browsers
        value = "https://${local.project_id}.web.app,https://${local.project_id}.firebaseapp.com"
      }
      env {
        name  = "CORS_ORIGIN_REGEX" # PR preview channels: <site>--<channel>-<hash>.web.app
        value = "https://${local.project_id}--[a-z0-9-]+\\.web\\.app"
      }
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }
  depends_on = [google_project_service.serving, google_service_account.workload]
}

resource "google_cloud_run_v2_service_iam_member" "ci_deploy" {
  project  = local.project_id
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.developer"
  member   = local.deploy_member
}

resource "google_service_account_iam_member" "ci_acts_as_api" {
  service_account_id = google_service_account.workload["api"].name
  role               = "roles/iam.serviceAccountUser"
  member             = local.deploy_member
}

# The website calls the API from the browser, so Cloud Run must accept unauthenticated requests;
# the API itself then requires a verified, allowlisted Google sign-in on every data route and
# refuses to start without an allowlist (APP-005). Off unless the env opts in (WEB-013).
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.api_public ? 1 : 0
  project  = local.project_id
  location = google_cloud_run_v2_service.api.location
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
