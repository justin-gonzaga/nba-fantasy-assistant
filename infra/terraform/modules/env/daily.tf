# The daily chain in the cloud (INFRA-008, D-63). The NBA's hosts block cloud IPs, so the owner's
# PC runs only the NBA fetch at 07:30 (writing raw snapshots to the raw bucket); this job runs the
# rest at 07:45 Sydney: injury report, week projection, brief, Telegram. Its workspace is the serve
# bucket, which is also what the API reads, so nothing needs publishing.
# CI deploys the job's image by digest (like the API); the image here is a placeholder.

resource "google_project_service" "scheduler" {
  project            = local.project_id
  service            = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_run_v2_job" "daily" {
  project             = local.project_id
  name                = "daily"
  location            = var.region
  deletion_protection = local.is_prod
  labels              = local.labels

  template {
    task_count = 1
    template {
      service_account = "transform-sa@${local.project_id}.iam.gserviceaccount.com"
      max_retries     = 1
      timeout         = "900s"
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/job" # placeholder until CI's first deploy
        args  = ["job", "cloud"]
        env {
          name  = "APP_ENV"
          value = var.env
        }
        env {
          name  = "DATA_ROOT" # raw snapshots: the PC's fetch writes, this job reads (+ the injury report)
          value = "gs://${google_storage_bucket.raw.name}"
        }
        env {
          name  = "WORK_ROOT" # predictions, league, briefs, run log: the bucket the API reads
          value = "gs://${google_storage_bucket.serve.name}"
        }
        env {
          name  = "SERVE_ROOT"
          value = "gs://${google_storage_bucket.serve.name}"
        }
        env {
          name  = "GCP_PROJECT" # BigQuery for the draft-values step (DATA-035); CI sets the same value
          value = local.project_id
        }
        env {
          name  = "TELEGRAM_CHAT_ID" # from the git-ignored owner.auto.tfvars; empty: no message
          value = var.telegram_chat_id
        }
        env {
          name = "TELEGRAM_BOT_TOKEN"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.app["telegram-bot-token"].secret_id
              version = "latest"
            }
          }
        }
        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }
  depends_on = [google_project_service.serving, google_service_account.workload]
}

# The chain adds the injury report to raw: create-only, so it can never overwrite or delete bronze.
resource "google_storage_bucket_iam_member" "transform_raw_create" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectCreator"
  member = local.sa["transform"]
}

# CI updates the job's image on deploy, like the API's.
resource "google_cloud_run_v2_job_iam_member" "ci_deploy_daily" {
  project  = local.project_id
  location = google_cloud_run_v2_job.daily.location
  name     = google_cloud_run_v2_job.daily.name
  role     = "roles/run.developer"
  member   = local.deploy_member
}

resource "google_service_account_iam_member" "ci_acts_as_transform" {
  service_account_id = google_service_account.workload["transform"].name
  role               = "roles/iam.serviceAccountUser"
  member             = local.deploy_member
}

# Cloud Scheduler starts the job (the scheduler identity already has run.invoker, main.tf).
resource "google_cloud_scheduler_job" "daily" {
  project   = local.project_id
  region    = var.region
  name      = "daily-brief"
  schedule  = "45 7 * * *"
  time_zone = "Australia/Sydney"
  paused    = !var.daily_schedule_enabled

  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${local.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.daily.name}:run"
    oauth_token {
      service_account_email = "scheduler-sa@${local.project_id}.iam.gserviceaccount.com"
    }
  }
  depends_on = [google_project_service.scheduler]
}
