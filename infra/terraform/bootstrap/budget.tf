# G-08 ceiling: US$10/month (expressed in the billing account's currency).
# Scoped to this system's three projects. Alerts email the billing account
# admins; the Telegram route (Pub/Sub) is added in INFRA-005.
resource "google_billing_budget" "monthly" {
  provider = google.billing

  billing_account = var.billing_account
  display_name    = "${var.prefix} monthly ceiling (G-08)"

  budget_filter {
    projects               = [for p in google_project.this : "projects/${p.number}"]
    calendar_period        = "MONTH"
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  amount {
    specified_amount {
      currency_code = var.budget_currency
      units         = tostring(var.budget_amount)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
      spend_basis       = "CURRENT_SPEND"
    }
  }

  depends_on = [google_project_service.this["admin/billingbudgets.googleapis.com"]]
}
