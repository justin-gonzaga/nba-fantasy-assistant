# Credentials: the owner's gcloud Application Default Credentials (ADC).
# The bootstrap is the only stack applied with owner credentials; everything
# after it runs as a service account (CI via WIF, Claude via impersonation).
provider "google" {
  region = var.region
}

# The Billing Budgets API refuses end-user credentials without a quota
# project. This alias bills those calls to the admin project (whose
# billingbudgets API this stack enables) instead of the ADC default.
provider "google" {
  alias                 = "billing"
  region                = var.region
  user_project_override = true
  billing_project       = local.project_ids.admin
}
