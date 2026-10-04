# ADR-0019: GCP serverless runtime (Cloud Run + Cloud Scheduler), Terraform, dev/prod projects

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: D-01 B (provider GCP), D-28, I1–I5 · **Supersedes**: ADR-0003
- **Related**: ADR-0020, ADR-0017, system-architecture §7–8

## Context
The owner wants production use with phone alerts and an eventual move to GCP. stats.nba.com is only needed for a one-off history download.

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
- Run the pipeline as **Cloud Run jobs** triggered by **Cloud Scheduler** (awake-window aware), and the API as a **Cloud Run service**.
- Manage everything with **Terraform** (state in a locked GCS bucket) across two projects, **dev** and **prod**.
- CI authenticates via **Workload Identity Federation**.
- Each workload gets a least-privilege service account.
- Claude has dev access only; prod changes go through CI.

## Consequences
- Near-$0 serverless operation; strong GCP/IaC skills.
- No persistent disk, so the warehouse must be BigQuery (ADR-0020).
- Cloud reachability of the NBA CDN and injury PDFs must be verified (DISC-004/005).

## Revisit triggers
The cost ceiling is breached, the sources block GCP IPs, or a long-running process becomes necessary.
