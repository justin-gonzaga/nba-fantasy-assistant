# Dev environment storage and identities (INFRA-002). Apply dev before prod:
# prod grants these dev SAs read-only access to the prod raw bucket (I3 A).
module "env" {
  source = "../../modules/env"
  env    = "dev"

  api_allowed_emails     = var.api_allowed_emails
  telegram_chat_id       = var.telegram_chat_id
  daily_schedule_enabled = var.daily_schedule_enabled
  watchdog_muted         = var.watchdog_muted
  api_public             = true # the website calls it; the API enforces Google sign-in (APP-005)
}

variable "api_allowed_emails" {
  description = "Who may sign in to the API; set in owner.auto.tfvars (git-ignored)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_chat_id" {
  description = "The owner's Telegram chat for the cloud brief; set in owner.auto.tfvars (git-ignored)."
  type        = string
  default     = ""
  sensitive   = true
}

variable "daily_schedule_enabled" {
  description = "Run the cloud daily chain at 07:45 Sydney (INFRA-008); set true at the switch-over."
  type        = bool
  default     = false
}

output "env" {
  description = "Dev buckets, datasets and service accounts."
  value = {
    buckets          = module.env.buckets
    datasets         = module.env.datasets
    service_accounts = module.env.service_accounts
    serving          = module.env.serving
  }
}

output "web_build_env" {
  description = "Public build variables for the live website (copied into GitHub repo variables)."
  value       = module.env.web_build_env
}

variable "watchdog_muted" {
  description = "Silence the watchdog's alerts (off-season); set in owner.auto.tfvars (INFRA-005)."
  type        = bool
  default     = false
}
