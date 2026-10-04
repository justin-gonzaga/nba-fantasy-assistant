---
id: APP-019
title: "Account data export and consent re-acceptance"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-021, APP-026, APP-027, APP-014, APP-023]
areas: [apps/api/src/fantasy_api/lifecycle/export*.py, apps/api/src/fantasy_api/lifecycle/consent*.py, apps/api/tests/test_lifecycle_export.py, apps/api/tests/test_lifecycle_consent.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-019 — Export and consent

## Objective
People must be able to get all their data. This task builds the complete export from the `USER_DATA_OWNERS`
registry (the registry and its coverage test are APP-026) and the re-acceptance flow when the terms or privacy notice
change. The first acceptance is recorded at onboarding (APP-021). Deletion, retention and purge are APP-025 and read the
same registry, so a new feature cannot forget to join either. Rules: `docs/standards/user-data-and-auth.md` (User rights, Data minimisation).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (User rights, Data minimisation and retention)
- `docs/specification/leagues-and-accounts.md` §4, §6
- `apps/api/src/fantasy_api/users/*` (current delete/export from APP-008/APP-011 — replaced here, not kept beside)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member | "give me my data" | `POST /me/export` builds a JSON bundle (profile, settings, presets, leagues, teams, memberships, requests, consents, security events about me) delivered as a signed download that expires in 24 h; requires a recent sign-in; one export a day; excludes other people's data except their public names inside my records |
| Developer adds a collection | "cannot forget" | the registry coverage test (APP-026) fails first; the export test then proves the new category appears in the bundle |
| Consent | "what did I agree to" | the consent fields on the user document (`termsVersion`, `privacyVersion`, `acceptedAt`, written by APP-021) are compared with the current versions; a new version forces re-acceptance through `POST /me/consent` before further use |
| Old export/delete code | no duplicates | the partial `GET /me/export` and `DELETE /me` from APP-008/APP-011 are removed here (export) and in APP-025 (delete); no second path remains |
| Large account | bounded | export streams in pages, capped at 20 MB; avatars are listed by URL, not inlined |
| Secrets | never | no tokens, hashed invite tokens or provider secrets in the bundle |

## Acceptance criteria
- [ ] AC1: the export bundle is built by iterating `USER_DATA_OWNERS` (APP-026) and nothing else; a test registers a
      fake owner and sees it in the bundle.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_export.py -k "registry"`
- [ ] AC2: the export contains every registered category, excludes secrets and others' non-public data, is delivered by
      a signed URL to the private exports bucket (INFRA-010; a fake in tests) that expires after 24 h, needs a recent
      sign-in (APP-027 step-up table) and is limited to one a day (a row in APP-024's table).
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_export.py`
- [ ] AC3: a new `termsVersion` or `privacyVersion` makes `/me` return `consentRequired` and write routes return 403
      `consent-required` until `POST /me/consent` records the new versions.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_consent.py`
- [ ] AC4: the old ad-hoc export route and function are gone (one export path).
      Verify: `grep -rn "def export_me\|/me/export" apps --include=*.py` lists only `lifecycle/`
- [ ] AC5: the client is regenerated with no diff on a second run.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Contract tests on both stores; registry-completeness test; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified; deletion, retention and purge split to APP-025.

## Decisions
- One registry of user-data owners, checked by a test, is the guard against orphaned personal data.

## Known issues
_None._

## Follow-ups
- DSAR handling procedure and the breach plan live in SEC-003.
