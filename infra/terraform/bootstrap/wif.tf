# Keyless CI -> GCP auth (I4 A). GitHub Actions presents its OIDC token;
# only tokens from this exact repository pass the provider condition.
resource "google_iam_workload_identity_pool" "github" {
  project                   = google_project.this["admin"].project_id
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "OIDC identities from ${var.github_repository}"

  # A deleted pool ID stays reserved (soft-deleted) for 30 days.
  lifecycle {
    prevent_destroy = true
  }

  depends_on = [
    google_project_service.this["admin/iam.googleapis.com"],
    google_project_service.this["admin/sts.googleapis.com"],
  ]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = google_project.this["admin"].project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-oidc"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"          = "assertion.sub"
    "attribute.repository"    = "assertion.repository"
    "attribute.repository_id" = "assertion.repository_id"
    "attribute.ref"           = "assertion.ref"
    "attribute.actor"         = "assertion.actor"
    "attribute.event_name"    = "assertion.event_name"
    # "prod" only for the main branch and v* tags; everything else is "dev".
    "attribute.deploy_tier" = "(assertion.ref == 'refs/heads/main' || assertion.ref.startsWith('refs/tags/v')) ? 'prod' : 'dev'"
  }

  # Reject every token not minted for this repository (immutable numeric IDs
  # plus the name).
  attribute_condition = join(" && ", [
    "assertion.repository_id == '${var.github_repository_id}'",
    "assertion.repository_owner_id == '${var.github_repository_owner_id}'",
    "assertion.repository == '${var.github_repository}'",
  ])

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

locals {
  wif_pool = google_iam_workload_identity_pool.github.name
}

# One deploy service account per environment (roles on the env projects are
# granted by the env stacks, INFRA-002+).
resource "google_service_account" "deploy" {
  for_each = toset(["dev", "prod"])

  project      = google_project.this[each.key].project_id
  account_id   = "deploy"
  display_name = "CI deploy (${each.key})"
  description  = "Used only by GitHub Actions via Workload Identity Federation."

  depends_on = [google_project_service.this]
}

# dev: any ref of the repository (branches, PRs, tags).
resource "google_service_account_iam_member" "deploy_dev_wif" {
  service_account_id = google_service_account.deploy["dev"].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${local.wif_pool}/attribute.repository_id/${var.github_repository_id}"
}

# prod: only refs/heads/main and refs/tags/v* (deploy_tier == "prod").
resource "google_service_account_iam_member" "deploy_prod_wif" {
  service_account_id = google_service_account.deploy["prod"].name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${local.wif_pool}/attribute.deploy_tier/prod"
}
