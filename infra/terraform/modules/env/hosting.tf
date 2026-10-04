# Website hosting (D-59, WEB-012): Firebase Hosting in each env project, deployed only by CI.
# The site id is the project id, so the free address is <project>.web.app.

resource "google_project_service" "firebase" {
  for_each = toset([
    "firebase.googleapis.com",
    "firebasehosting.googleapis.com",
    "identitytoolkit.googleapis.com", # Firebase Auth: Google sign-in (D-27, WEB-013)
  ])
  project            = local.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_firebase_project" "this" {
  provider   = google-beta
  project    = local.project_id
  depends_on = [google_project_service.firebase]
}

resource "google_firebase_hosting_site" "web" {
  provider   = google-beta
  project    = local.project_id
  site_id    = local.project_id
  depends_on = [google_firebase_project.this]
}

# The web app registration: its config (API key, auth domain, app id) is public by design and is
# baked into the website at build time; it is not a secret. Google sign-in itself is enabled once
# in the Firebase console (owner step, docs/runbooks/api-hosting.md).
resource "google_firebase_web_app" "web" {
  provider     = google-beta
  project      = local.project_id
  display_name = "web (${var.env})"
  depends_on   = [google_firebase_project.this]
}

data "google_firebase_web_app_config" "web" {
  provider   = google-beta
  project    = local.project_id
  web_app_id = google_firebase_web_app.web.app_id
}

# Only the CI deploy identity can publish releases (prod: from CalVer tags, via WIF).
resource "google_project_iam_member" "deploy_hosting" {
  project = local.project_id
  role    = "roles/firebasehosting.admin"
  member  = "serviceAccount:deploy@${local.project_id}.iam.gserviceaccount.com"
}
