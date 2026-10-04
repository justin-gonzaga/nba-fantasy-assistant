variable "billing_account" {
  description = "Cloud Billing account ID (XXXXXX-XXXXXX-XXXXXX). Set in the gitignored terraform.tfvars; it must stay out of the public repo."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^[0-9A-F]{6}-[0-9A-F]{6}-[0-9A-F]{6}$", var.billing_account))
    error_message = "billing_account must look like XXXXXX-XXXXXX-XXXXXX (upper-case hex)."
  }
}

variable "prefix" {
  description = "Globally unique prefix for project IDs and the state bucket. Project IDs can never be reused once taken, so change it only before the first apply."
  type        = string
  default     = "nbafa-hdfo"

  validation {
    # Longest derived ID is "<prefix>-admin" and must be <= 30 chars.
    condition     = can(regex("^[a-z][a-z0-9-]{3,22}[a-z0-9]$", var.prefix)) && length(var.prefix) <= 24
    error_message = "prefix: 5-24 chars, lower-case letters/digits/hyphens, starting with a letter."
  }
}

variable "org_id" {
  description = "Organisation ID to create the projects under. null = no parent (personal projects). Projects can be moved INTO an organisation later, not easily out of one."
  type        = string
  default     = null
}

variable "region" {
  description = "Default region for regional resources (GCS, BigQuery, Cloud Run)."
  type        = string
  default     = "australia-southeast1"
}

variable "github_repository" {
  description = "GitHub repository (owner/name) allowed to use Workload Identity Federation."
  type        = string
  default     = "justin-gonzaga/nba-fantasy-assistant"
}

variable "github_repository_id" {
  description = "Numeric GitHub repository ID (gh api repos/OWNER/NAME --jq .id). Matching on the immutable ID prevents a deleted-and-recreated repo with the same name from inheriting access."
  type        = string
  default     = "1403819022"
}

variable "github_repository_owner_id" {
  description = "Numeric GitHub owner (user) ID (gh api repos/OWNER/NAME --jq .owner.id)."
  type        = string
  default     = "68487711"
}

variable "budget_amount" {
  description = "Monthly budget in the billing account's currency. G-08 ceiling is US$10/month; the billing account is in AUD, so the default is A$15 (about US$10)."
  type        = number
  default     = 15
}

variable "budget_currency" {
  description = "Currency code of the billing account. The Budgets API rejects a currency that differs from the account's."
  type        = string
  default     = "AUD"
}

variable "owner_email" {
  description = "Owner's Google account email, allowed to impersonate the Claude dev service account. null = the email of the credentials running the apply (ADC)."
  type        = string
  default     = null
}
