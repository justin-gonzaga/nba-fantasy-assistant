# Users, roles and invites (D-64, G-25, APP-008): Firestore (Native) written only by the API through
# the server SDK as the api identity. Security rules deny every client (web/mobile SDK) request.
# A copy streams to BigQuery `app_raw` through the "Stream Firestore to BigQuery" Firebase extension,
# installed once by the owner (docs/runbooks/api-hosting.md, "Users and invites").

resource "google_project_service" "firestore" {
  for_each = toset([
    "firestore.googleapis.com",
    "firebaserules.googleapis.com",
  ])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_firestore_database" "app" {
  project                 = local.project_id
  name                    = "(default)" # the extension and the server SDK default to it
  location_id             = var.region
  type                    = "FIRESTORE_NATIVE"
  concurrency_mode        = "OPTIMISTIC"
  delete_protection_state = local.is_prod ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"
  deletion_policy         = local.is_prod ? "ABANDON" : "DELETE"
  depends_on              = [google_project_service.firestore]
}

resource "google_firebaserules_ruleset" "firestore" {
  project = local.project_id
  source {
    files {
      name    = "firestore.rules"
      content = file("${path.module}/firestore.rules")
    }
  }
  depends_on = [google_firestore_database.app]
}

resource "google_firebaserules_release" "firestore" {
  project      = local.project_id
  name         = "cloud.firestore" # the release Firestore enforces for the (default) database
  ruleset_name = google_firebaserules_ruleset.firestore.name
  lifecycle {
    replace_triggered_by = [google_firebaserules_ruleset.firestore]
  }
}

# The API reads and writes documents (no admin: it cannot change indexes, rules or the database).
resource "google_project_iam_member" "api_datastore" {
  project = local.project_id
  role    = "roles/datastore.user"
  member  = local.sa.api
}

# The analytical copy (G-25 Q1 "A + BQ copy"): the extension writes a changelog table and a latest
# view here. It is user state, kept apart from the data-product datasets.
resource "google_bigquery_dataset" "app_raw" {
  project                    = local.project_id
  dataset_id                 = "app_raw"
  location                   = var.region
  description                = "Firestore users/invites changelog, streamed by the Firebase extension (APP-008)"
  labels                     = local.labels
  delete_contents_on_destroy = false
}
