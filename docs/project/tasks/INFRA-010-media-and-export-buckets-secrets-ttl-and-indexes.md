---
id: INFRA-010
title: "Media, quarantine and export buckets, application secrets, Firestore TTL and indexes"
epic: EP-76 Identity and data protection
phase: 7
component: infra
status: todo
ready: true
size: M
autonomy: gated
gate: G-35
depends_on: [APP-008]
areas: [infra/terraform/**, docs/runbooks/storage-and-secrets.md, firestore.indexes.json]
standards: [devops, security]
assignee:
created: 2026-10-04
completed:
---
# INFRA-010 — Storage, secrets, TTL and indexes

## Objective
Provision, in **dev first**, the storage and data plumbing the accounts-and-leagues features need, with no new monthly
cost. **Media decision (settles the contradiction found in review):** avatars live in one dedicated bucket that holds only
server-produced, re-encoded WebP files under random ids and is public for reads. It is served from the Cloud Storage
origin (`storage.googleapis.com`), which is a different origin from the app and sets no cookies, so no load balancer or
CDN is bought. **Public access prevention stays on for every other bucket** (the private quarantine bucket and the export
bucket). A hidden or reported avatar is moved to quarantine, so it stops being reachable at its public URL. Storage and
secret details follow `docs/standards/user-data-and-auth.md` (Storage and encryption, Uploads).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Storage and encryption, Uploads, Logging)
- `docs/specification/leagues-and-accounts.md` §9, §10; `infra/terraform/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Avatar viewer | "loads fast, cannot run script" | media bucket: uniform access, no listing, public read of objects only, lifecycle rule for orphans; objects are re-encoded WebP with a set content type and a long immutable cache; the API service account can create and delete objects but cannot read others' buckets |
| Reported picture | "gone means gone" | a private `quarantine` bucket (public access prevention on) receives hidden objects; restore moves it back; deletion removes it from both |
| Export | "my data, once" | a private `exports` bucket with public access prevention, a 1-day lifecycle delete, and a signer role limited to the API service account; signed URLs expire in 24 h |
| Application secrets | "never in the repo or state" | Secret Manager containers (not values) for the phone-hash pepper, the reporter-hash secret and the IP-hash seed; accessor IAM only for the API service account; values are added by a documented owner step and never pass through Terraform state; rotation procedure in the runbook |
| Firestore growth | "indexes and TTL as code" | the indexes file and TTL policies (activity log, reports, security events, invites, deletion state, rate counters, sim runs) are declared and validated |
| Dev vs prod | "no cross-over" | every resource exists in both with variables; applies run only in CI |

## Acceptance criteria
- [ ] AC1: Terraform declares the media, quarantine and export buckets with the stated access model (public access
      prevention on quarantine and exports; media public-read, uniform, no listing) and lifecycle rules.
      Verify: `terraform -chdir=infra/terraform/envs/dev validate` and a policy check that fails if a bucket other than
      media lacks public access prevention
- [ ] AC2: a check script in `tools/` prints the response headers for a test avatar in dev: `Content-Type: image/webp`,
      a long immutable `Cache-Control`, no `Set-Cookie`; whether `nosniff` can be set is recorded (RSCH-010) and, if
      not, the residual risk is documented because the bytes are server-produced WebP on a separate origin.
      Verify: the script output is pasted into the task evidence
- [ ] AC3: Secret Manager containers for the three secrets exist with API-service-account accessor IAM and no values in
      state; the runbook has the one-time creation and the rotation steps and says who does them.
      Verify: `terraform validate`; `grep -rn "secret_data" infra/terraform` finds nothing
- [ ] AC4: Firestore TTL policies and the composite indexes needed by APP-014, APP-015 and APP-022 (collection-group
      `members` by `uid`, public discovery, invite `tokenHash`) are declared.
      Verify: `terraform validate`; the indexes file passes `firebase firestore:indexes` lint in CI
- [ ] AC5: nothing is applied to prod; the dev apply path is documented; every resource has an owner label.
      Verify: `git diff --stat` shows no prod tfvars change

## Test requirements
`terraform fmt -check`, `validate` and `plan` for dev; policy checks from the existing CI.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from INFRA-009 after review).

## Decisions
- No load balancer: a public media bucket of re-encoded avatars on the storage origin is enough at this scale and costs
  nothing; revisit if abuse or branding needs a custom media domain.

## Known issues
- Firestore TTL deletes typically within 24 h and does not remove subcollections; APP-025's daily job covers the rest.

## Follow-ups
- A custom media domain behind a load balancer is a later, priced decision.
