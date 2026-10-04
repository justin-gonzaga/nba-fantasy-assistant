---
id: APP-008
title: "Users, roles and invites: a user store keyed by uid, /me, owner invites"
epic: EP-70 Dashboard
phase: 7
component: api
status: in_progress
ready: true
size: M
autonomy: review
gate: G-25
depends_on: [APP-005]
areas: [apps/api/**, infra/terraform/**, docs/runbooks/api-hosting.md]
standards: [backend, security, testing]
assignee: claude
created: 2026-10-02
completed:
---
# APP-008 — Users, roles and invites

## Objective
Replace the single env allowlist with a user store (D-64, store per G-25 Q1) so several invited people can sign in
(D-31): users keyed by the sign-in uid, roles `owner`/`member`, and owner-issued invites. The env allowlist only
bootstraps the first owner.

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-31, D-64
- `apps/api/src/fantasy_api/auth.py`, `apps/api/tests/test_auth.py`

## User stories and edge cases
| Persona | Story | Edge cases |
|---|---|---|
| Owner (first sign-in) | "I sign in and I'm the owner" | bootstrap from `ALLOWED_EMAILS` exactly once; the email compare is case-insensitive |
| Owner | "Invite my friend by email; remove them later" | duplicate invite → the existing one; inviting an existing member → 409; invites expire (14 days); removing yourself as the last owner → 409 |
| Invited member | "I sign in with the invited Google account and I'm in" | the invite is claimed on first sign-in and bound to the uid; a different email → 403 with a clear problem; an expired invite → 403 `invite-expired` |
| Removed member | Still holds a valid Google token | the next request → 403 (no token caching beyond the request) |
| Any user | Changes their Google email | the uid still identifies them; the email updates on next sign-in |
| Attacker | Calls owner endpoints as a member, or forges a uid | 403; the uid comes only from the verified token |

## Acceptance criteria
- [x] AC1: a `UserStore` port with an in-memory adapter (tests) and a Firestore adapter (G-25: API-only writes via the
      Admin SDK, security rules deny all client access); users are keyed by uid and hold
      email, display name, role, created/last-seen times.
      Verify: `uv run pytest -q apps/api/tests/test_users_store.py` (contract tests run against both adapters; the
      Firestore adapter against the Firestore emulator in CI)
- [x] AC2: first sign-in by a bootstrap email creates the owner; later sign-ins don't duplicate or demote.
      Verify: `apps/api/tests/test_users.py::test_bootstrap_owner_once`
- [x] AC3: `GET /me` returns uid, email, display name, role; an unknown, uninvited account gets 403 `not-invited`.
      Verify: `test_users.py::test_me`, `::test_uninvited_is_403`
- [x] AC4: owner-only `POST /invites {email}`, `GET /invites`, `DELETE /invites/{id}`, `GET /members`,
      `DELETE /members/{uid}`; members get 403; every edge case in the table has a test.
      Verify: `test_users.py` (one test per row above) → all pass
- [x] AC5: a claimed invite binds the uid; a removed member's next request is 403.
      Verify: `test_users.py::test_invite_claim`, `::test_removed_member_is_locked_out`
- [x] AC6: the existing views keep working for the owner, and the OpenAPI contract and TS types are regenerated.
      Verify: `uv run pytest -q apps/api` all pass; `just api-client` → no diff
- [ ] AC7: Terraform adds the Firestore (Native) database in australia-southeast1, deny-all security rules, the API's
      `datastore.user` role, and the Firestore→BigQuery stream (extension or equivalent) into an `app_raw` dataset; plan shown.
      Verify: `terraform -chdir=infra/terraform plan` shows only those resources; after apply, a test write appears in
      `app_raw` within 5 minutes

## Test requirements
Contract tests shared by both adapters; the API tests use the in-memory adapter and a fake token verifier (as
test_auth does). No real Google accounts in tests.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | `FIRESTORE_EMULATOR_HOST=127.0.0.1:8681 uv run pytest -q apps/api/tests/test_users_store.py` (5 contract tests × memory + Firestore emulator) | 10 passed (without the emulator: 5 passed, 5 skipped with a reason); CI `test-py` starts the emulator container and sets `REQUIRE_FIRESTORE_EMULATOR=1` (fails instead of skipping) |
| AC2 | test | `apps/api/tests/test_users.py::test_bootstrap_owner_once` (mixed-case email; no duplicate/demotion; a 2nd allowlisted email after the first owner → 403 `not-invited`) | pass |
| AC3 | test | `test_users.py::test_me`, `::test_uninvited_is_403`, `::test_unverified_or_uidless_tokens_are_forbidden` | pass |
| AC4 | test | `test_users.py`: `test_owner_invites_lists_and_revokes`, `test_duplicate_invite_returns_the_existing_one`, `test_inviting_an_existing_member_is_409`, `test_invites_expire_after_14_days`, `test_last_owner_cannot_remove_themself`, `test_a_second_owner_can_be_invited_and_one_owner_removed`, `test_invite_needs_a_valid_email`, `test_a_different_email_is_403_with_a_clear_problem`, `test_email_change_keeps_the_account`, `test_members_get_403_on_owner_endpoints` (×5 endpoints), `test_the_uid_comes_only_from_the_verified_token` | `uv run pytest -q apps/api/tests/test_users.py` → 23 passed |
| AC5 | test | `test_users.py::test_invite_claim`, `::test_removed_member_is_locked_out` | pass |
| AC6 | command | `uv run pytest -q apps/api` → 98 passed (emulator on); `just api-client` then `git diff` → no diff; `corepack pnpm --dir apps/web typecheck` → exit 0 | pass |
| AC7 | command | `terraform -chdir=infra/terraform/modules/env test` → 17 passed (2 new runs: Firestore Native `(default)` in australia-southeast1, deny-all rules released as `cloud.firestore`, api `roles/datastore.user`, `app_raw` dataset, prod delete-protected); `terraform validate` envs/dev + envs/prod (init `-backend=false`) → valid; `terraform fmt -check -recursive` → clean | Partial: plan/apply and the "write appears in `app_raw` within 5 min" check are owner steps (runbook "Users and invites") |
| all | command | `FIRESTORE_EMULATOR_HOST=127.0.0.1:8681 just ci-local` | 544 passed, 0 skipped; coverage 93.49 % (≥ 85); ruff, mypy strict, import-linter, tasks validate, manifest check clean |

## Implementation history
- 2026-10-02 — Specified (owner request: "capability for different users, managing profile, settings"). Waits on G-25.
- 2026-10-03 — Built (Claude, worktree `nbafa-users`, branch `task/APP-008-users`). `fantasy_api/users/`: `model`
  (User, Invite, 14-day TTL), `store` (`UserStore` protocol + in-memory adapter), `firestore` (Admin-SDK adapter;
  `users/{uid}`, `invites/{id}`; claim in a transaction), `service` (bootstrap-once, invite claim/expiry via the
  injected `Clock`, last-owner rule, last-seen writes throttled to 15 min; no access caching), `routes` (`/me`,
  owner-only `/invites`, `/members`). `auth.current_user` now returns the `User` (uid from the token's `sub`;
  `AuthConfig.allowed_emails` → `bootstrap_owners`; rate limit keyed by uid); `require_owner`. `serve()` uses
  Firestore whenever auth is on. CORS: GET/POST/DELETE + `Content-Type`, no credentials. OpenAPI + TS types
  regenerated. Terraform `modules/env/firestore.tf` + `firestore.rules` + 2 test runs. CI: a Firestore emulator
  container in `test-py`. Runbook section "Users and invites". Dev tooling: `gcloud components install
  cloud-firestore-emulator`; Java 21 as a portable zip in `~/tools/jdk-21.0.12.1+1` (winget's machine install
  waited on a UAC prompt and was cancelled). Attempts: 1 TF-test fix (an unknown-at-plan SA member in an assert).
  Next: owner review (Tier B: CI + infra), then the owner's `terraform apply` + extension install.

## Decisions
- Review (Medium, fixed): first-owner bootstrap and last-owner removal are atomic (`create_first_owner`,
  `delete_user_keeping_an_owner`: Firestore transactions / an in-memory lock); a two-thread race test passes on both
  adapters (Firestore emulator: 14/14). CI's emulator image is pinned by digest.
- Deploy safety (2026-10-03): `USERS_BACKEND` (Terraform `users_backend`, default `memory`) keeps the old allowlist
  behaviour until the owner's apply creates Firestore; `firestore` after that. Tested (`test_the_store_stays_in_memory_until_the_owner_switches_to_firestore`).
- Bootstrap = "the store has no owner yet": the allowlist grants nothing once an owner exists (no separate flag).
- Invites take an optional `role` (default `member`), so a co-owner is possible; the last owner can't be removed.
- `POST /invites` answers 201 when created, 200 with the existing open invite for a duplicate; an expired one is replaced.
- `GET /invites` lists all invites with a computed `status` (open/expired/claimed) for WEB-015.
- Removing a member leaves their invite claimed, so re-admitting them needs a new invite.

## Known issues
- AC7's plan/apply and the BigQuery-stream check need the owner (credentials + a Firebase extension install that
  deploys Cloud Functions). The CI emulator step (`google-cloud-cli:emulators` image) is unproven until the PR's
  first CI run.
- Touches `.github/workflows/ci.yml` (outside `areas:`) for the emulator step: Tier B review.

## Follow-ups
- APP-009 settings, WEB-014 profile page, WEB-015 member admin, DATA-032 per-user league.
