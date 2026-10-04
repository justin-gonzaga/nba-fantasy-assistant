---
id: APP-025
title: "Account deletion cascade, retention jobs, username release and admin purge"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-019, APP-026, APP-027, APP-014, APP-023]
areas: [apps/api/src/fantasy_api/lifecycle/delete*.py, apps/api/src/fantasy_api/lifecycle/purge*.py, apps/pipeline/src/fantasy_pipeline/retention*.py, apps/api/tests/test_lifecycle_delete.py, apps/pipeline/tests/test_retention.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-025 — Delete, retain, purge

## Objective
A person can delete their account and everything goes, in a way that survives failures; nothing is kept longer than it
is needed; the owner can purge an account immediately (for example an under-13). It uses the APP-019 registry and
replaces the partial `DELETE /me`. Rules: `docs/standards/user-data-and-auth.md` (User rights, Retention).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (User rights, Data minimisation and retention)
- APP-019 registry; `docs/specification/leagues-and-accounts.md` §6 (delete my account)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member | "delete my account" | needs a recent sign-in and typing the username; a 14-day grace period (signing in again cancels), then the cascade runs and finishes within 7 days (inside one month of the request, UDR-30); the response states what is deleted and what is kept and why |
| Commissioner | "my league has members" | refused with 409 `transfer-or-delete-leagues` listing the leagues; sole-member leagues are deleted automatically |
| Footprint in other leagues | "gone, but history stays sane" | activity logs show "former manager"; the username is released after 30 days; reports they filed are anonymised |
| Failure halfway | "not half-deleted" | a resumable job with a state document (`pending -> done`), each step idempotent, a failure alerts the owner, the auth account is deleted last |
| Backups | honest | Firestore backups and point-in-time recovery hold deleted data until they expire (documented, within the configured window); a restore replays the pending-deletions list |
| Retention | nothing kept forever | TTLs: league activity 180 d, reports 180 d, security events 180 d, expired invites 30 d after expiry, export bundles 24 h, deletion state 90 d; a daily job proves it ran |
| Under-13 discovered | "remove it now" | `POST /admin/users/{id}:purge` skips the grace period, needs owner role plus MFA (APP-027), is logged; the route is in the step-up table and in spec §7 |
| Owner account | protected | cannot be deleted through the self-service path |

## Acceptance criteria
- [ ] AC1: deletion: grace period, cancel on sign-in, typed confirmation, the 409 rule for commissioners, then a
      resumable cascade over every registered owner with the auth account last; re-running is a no-op.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_delete.py` (fault injected after each step)
- [ ] AC2: after deletion a scan of every registered store for the uid and username finds nothing, and public
      references show "former manager".
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_delete.py -k "scan or anonymised"`
- [ ] AC3: username release after 30 days; the old ad-hoc `DELETE /me` is removed (one delete path).
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_delete.py -k "release"`;
      `grep -rn "def delete_me" apps --include=*.py` lists only `lifecycle/`
- [ ] AC4: a retention table lists each TTL collection and its period (the Terraform TTL policies are INFRA-010; a test
      checks the two lists match) and a daily job deletes what TTL cannot (exports, expired invites, orphaned
      subcollections); it reports counts and fails loudly when it deleted nothing for 7 days while expired data exists.
      Verify: `uv run pytest -q apps/pipeline/tests/test_retention.py`
- [ ] AC5: admin purge works only for the owner role with MFA, skips the grace period and writes a security event.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_delete.py -k "purge"`
- [ ] AC6: the client is regenerated with no diff on a second run.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Fault-injection tests for the cascade; contract tests on both stores; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original APP-019).

## Decisions
_None yet._

## Known issues
- Firestore TTL deletes typically within 24 h and does not remove subcollections, so the daily job is required.

## Follow-ups
- SEC-003 documents the backup window in the privacy notice.
