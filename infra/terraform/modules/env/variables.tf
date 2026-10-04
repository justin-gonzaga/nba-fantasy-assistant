variable "env" {
  description = "Environment name: dev or prod."
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.env)
    error_message = "env must be dev or prod."
  }
}

variable "prefix" {
  description = "Shared naming prefix (same as the bootstrap stack)."
  type        = string
  default     = "nbafa-hdfo"
}

variable "region" {
  description = "Region for buckets and BigQuery datasets."
  type        = string
  default     = "australia-southeast1"
}

variable "raw_retention_days" {
  description = "Prod raw bucket retention policy (objects can't be deleted or replaced before this age). 0 = none. The policy is NOT locked: locking is irreversible and needs a separate owner decision."
  type        = number
  default     = 0
}

variable "dev_lifecycle_days" {
  description = "Dev buckets delete objects after this many days (I3)."
  type        = number
  default     = 30
}

variable "exports_lifecycle_days" {
  description = "Exports bucket deletes objects after this many days."
  type        = number
  default     = 90
}

variable "raw_readers" {
  description = "Extra members given read-only access to this env's raw bucket (prod: the dev ingest/transform SAs, I3 A)."
  type        = list(string)
  default     = []
}

variable "api_allowed_emails" {
  description = "Comma-separated emails that bootstrap the first owner (D-27, D-64): used only while Firestore has no owner; invites decide access after. Set in a git-ignored owner.auto.tfvars; empty means the API refuses to start."
  type        = string
  default     = ""
  sensitive   = true
}

variable "api_public" {
  description = "Let browsers reach the API (Cloud Run allUsers invoker). Safe only because the API enforces sign-in itself (APP-005)."
  type        = bool
  default     = false
}

variable "telegram_chat_id" {
  description = "The owner's Telegram chat for the cloud brief; set in owner.auto.tfvars (git-ignored). Empty: no message."
  type        = string
  default     = ""
  sensitive   = true
}

variable "daily_schedule_enabled" {
  description = "Run the cloud daily chain at 07:45 Sydney (INFRA-008). Off until the owner's switch-over."
  type        = bool
  default     = false
}

variable "watchdog_muted" {
  description = "Silence the watchdog (off-season) without deleting it (INFRA-005)."
  type        = bool
  default     = false
}

variable "users_backend" {
  description = "API user store: \"memory\" (allowlist bootstraps the owner) until Firestore exists, then \"firestore\" (APP-008)."
  type        = string
  default     = "memory"
  validation {
    condition     = contains(["memory", "firestore"], var.users_backend)
    error_message = "users_backend must be memory or firestore"
  }
}
