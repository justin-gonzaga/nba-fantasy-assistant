# The watchdog (INFRA-005, G-27 A): notices what the daily job can't report about itself (a run that
# never started, stale NBA data from the PC, the site or API down) and tells the owner on Telegram.
# Same image as the daily job; CI deploys its image by digest. Two schedules: the daily checks at
# 09:00 Sydney (after the 07:45 run) and the uptime checks every 15 minutes.

resource "google_cloud_run_v2_job" "watchdog" {
  project             = local.project_id
  name                = "watchdog"
  location            = var.region
  deletion_protection = local.is_prod
  labels              = local.labels

  template {
    task_count = 1
    template {
      service_account = "transform-sa@${local.project_id}.iam.gserviceaccount.com"
      max_retries     = 0 # a retry would double-alert; the next schedule is the retry
      timeout         = "300s"
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/job" # placeholder until CI's first deploy
        args  = ["fantasy", "watchdog", "--mode", "daily"]
        env {
          name  = "APP_ENV"
          value = var.env
        }
        env {
          name  = "WORK_ROOT" # the run log, the week table and the watchdog's own state
          value = "gs://${google_storage_bucket.serve.name}"
        }
        env {
          name  = "SITE_URL"
          value = "https://${local.project_id}.web.app"
        }
        env {
          name  = "API_URL"
          value = google_cloud_run_v2_service.api.uri
        }
        env {
          name  = "WATCHDOG_MUTED" # off-season switch (runbook: monitoring.md)
          value = tostring(var.watchdog_muted)
        }
        env {
          name  = "TELEGRAM_CHAT_ID"
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
            memory = "512Mi"
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

resource "google_cloud_run_v2_job_iam_member" "ci_deploy_watchdog" {
  project  = local.project_id
  location = google_cloud_run_v2_job.watchdog.location
  name     = google_cloud_run_v2_job.watchdog.name
  role     = "roles/run.developer"
  member   = local.deploy_member
}

locals {
  watchdog_run_uri = "https://run.googleapis.com/v2/projects/${local.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.watchdog.name}:run"
}

# 09:00 Sydney: was there a 07:45 run today, and is the NBA data fresh?
resource "google_cloud_scheduler_job" "watchdog_daily" {
  project   = local.project_id
  region    = var.region
  name      = "watchdog-daily"
  schedule  = "0 9 * * *"
  time_zone = "Australia/Sydney"
  paused    = !var.daily_schedule_enabled

  http_target {
    http_method = "POST"
    uri         = local.watchdog_run_uri
    oauth_token {
      service_account_email = "scheduler-sa@${local.project_id}.iam.gserviceaccount.com"
    }
  }
  depends_on = [google_project_service.scheduler]
}

# Every 15 minutes: are the site and the API up? (overrides the container args per run)
resource "google_cloud_scheduler_job" "watchdog_uptime" {
  project   = local.project_id
  region    = var.region
  name      = "watchdog-uptime"
  schedule  = "*/15 * * * *"
  time_zone = "Australia/Sydney"
  paused    = !var.daily_schedule_enabled

  http_target {
    http_method = "POST"
    uri         = local.watchdog_run_uri
    body = base64encode(jsonencode({
      overrides = { containerOverrides = [{ args = ["fantasy", "watchdog", "--mode", "uptime"] }] }
    }))
    headers = { "Content-Type" = "application/json" }
    oauth_token {
      service_account_email = "scheduler-sa@${local.project_id}.iam.gserviceaccount.com"
    }
  }
  depends_on = [google_project_service.scheduler]
}
