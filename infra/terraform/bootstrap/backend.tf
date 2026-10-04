# Bootstrap state starts LOCAL (terraform.tfstate, gitignored): the bucket
# that will hold it does not exist until the first apply.
#
# After the first successful apply, migrate (runbook: docs/runbooks/gcp-bootstrap.md, Part C):
#   1. Uncomment the block below and set `bucket` to the `state_bucket` output.
#   2. terraform init -migrate-state      (answer "yes" to copy the state)
#   3. terraform plan                     (expect: No changes)
#   4. Delete the local terraform.tfstate and terraform.tfstate.backup.
#
# The GCS backend provides state locking natively (a lock object per state).
#
terraform {
  backend "gcs" {
    bucket = "nbafa-hdfo-tfstate"
    prefix = "bootstrap"
  }
}
