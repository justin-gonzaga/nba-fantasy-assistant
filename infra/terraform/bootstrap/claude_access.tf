# I5 A (+ G-00 amendment): Claude Code works in dev only; in prod it can
# read logs and metrics, nothing else. Claude's local gcloud impersonates
# this service account, so the owner's own login is never used by Claude.
data "google_client_openid_userinfo" "me" {}

locals {
  owner_member = "user:${coalesce(var.owner_email, data.google_client_openid_userinfo.me.email)}"
}

resource "google_service_account" "claude" {
  project      = google_project.this["dev"].project_id
  account_id   = "claude-agent"
  display_name = "Claude Code (dev only)"
  description  = "Impersonated by the owner's local gcloud for Claude sessions. No prod data or write access."

  depends_on = [google_project_service.this["dev/iam.googleapis.com"]]
}

resource "google_project_iam_member" "claude_dev" {
  project = google_project.this["dev"].project_id
  role    = "roles/editor"
  member  = google_service_account.claude.member
}

resource "google_project_iam_member" "claude_prod_readonly" {
  for_each = toset(["roles/logging.viewer", "roles/monitoring.viewer"])

  project = google_project.this["prod"].project_id
  role    = each.value
  member  = google_service_account.claude.member
}

resource "google_service_account_iam_member" "owner_impersonates_claude" {
  service_account_id = google_service_account.claude.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = local.owner_member
}
