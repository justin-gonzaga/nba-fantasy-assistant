output "project_ids" {
  description = "Project IDs by role (admin, dev, prod)."
  value       = { for k, p in google_project.this : k => p.project_id }
}

output "project_numbers" {
  description = "Project numbers by role."
  value       = { for k, p in google_project.this : k => p.number }
}

output "region" {
  description = "Default region."
  value       = var.region
}

output "state_bucket" {
  description = "GCS bucket for Terraform state (backend \"gcs\" bucket)."
  value       = google_storage_bucket.tfstate.name
}

output "workload_identity_provider" {
  description = "Full provider resource name for google-github-actions/auth (workload_identity_provider)."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "deploy_service_accounts" {
  description = "Deploy service account emails by environment (google-github-actions/auth service_account)."
  value       = { for k, sa in google_service_account.deploy : k => sa.email }
}

output "claude_service_account" {
  description = "Service account Claude's local gcloud impersonates (dev only)."
  value       = google_service_account.claude.email
}

output "budget_id" {
  description = "Billing budget resource name."
  value       = google_billing_budget.monthly.name
}
