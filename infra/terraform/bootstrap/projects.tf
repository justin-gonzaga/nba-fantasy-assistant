locals {
  # admin: Terraform state + Workload Identity Federation + budget quota project.
  # dev / prod: the two environments (I2 A).
  project_ids = {
    admin = "${var.prefix}-admin"
    dev   = "${var.prefix}-dev"
    prod  = "${var.prefix}-prod"
  }

  common_labels = {
    app        = "nba-fantasy-assistant"
    managed_by = "terraform"
    stack      = "bootstrap"
  }

  admin_apis = [
    "cloudbilling.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "sts.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]

  env_apis = [
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "cloudbilling.googleapis.com",
    "billingbudgets.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
  ]

  project_apis = merge(
    { for api in local.admin_apis : "admin/${api}" => { env = "admin", api = api } },
    { for pair in setproduct(["dev", "prod"], local.env_apis) : "${pair[0]}/${pair[1]}" => { env = pair[0], api = pair[1] } },
  )
}

resource "google_project" "this" {
  for_each = local.project_ids

  project_id      = each.value
  name            = "nbafa ${each.key}"
  org_id          = var.org_id
  billing_account = var.billing_account
  labels          = merge(local.common_labels, { env = each.key })

  # No default VPC: nothing here needs Compute Engine networking.
  auto_create_network = false

  # A deleted project ID can never be reused; refuse `terraform destroy`.
  deletion_policy = "PREVENT"
}

resource "google_project_service" "this" {
  for_each = local.project_apis

  project = google_project.this[each.value.env].project_id
  service = each.value.api

  # Never switch an API off as a side effect of a Terraform change.
  disable_on_destroy         = false
  disable_dependent_services = false
}
