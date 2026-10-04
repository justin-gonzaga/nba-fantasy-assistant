# Prod environment storage and identities (INFRA-002).
variable "raw_retention_days" {
  description = "Retention policy on the prod raw bucket, in days (unlocked; see docs/runbooks/gcp-environments.md)."
  type        = number
  default     = 30
}

module "env" {
  source             = "../../modules/env"
  env                = "prod"
  raw_retention_days = var.raw_retention_days
  watchdog_muted     = var.watchdog_muted

  # I3 A: dev pipelines read prod raw, read-only.
  raw_readers = [
    "serviceAccount:ingest-sa@nbafa-hdfo-dev.iam.gserviceaccount.com",
    "serviceAccount:transform-sa@nbafa-hdfo-dev.iam.gserviceaccount.com",
  ]
}

output "env" {
  description = "Prod buckets, datasets and service accounts."
  value = {
    buckets          = module.env.buckets
    datasets         = module.env.datasets
    service_accounts = module.env.service_accounts
  }
}

variable "watchdog_muted" {
  description = "Silence the watchdog's alerts (off-season); set in owner.auto.tfvars (INFRA-005)."
  type        = bool
  default     = false
}
