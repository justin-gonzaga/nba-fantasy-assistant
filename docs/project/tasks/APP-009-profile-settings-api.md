---
id: APP-009
title: "Profile and settings API with validation and safe concurrent edits"
epic: EP-70 Dashboard
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: G-25
depends_on: []
areas: [apps/api/**, apps/pipeline/src/fantasy_pipeline/daily_brief.py, apps/web/src/api/schema.gen.ts, packages/core/src/fantasy_core/settings.py]
standards: [backend, security, testing]
assignee: claude
created: 2026-10-02
completed: 2026-10-03
---
# APP-009 — Profile and settings API

## Objective
Each user reads and edits their own profile and settings (D-64 settings list), and the daily chain reads them in
place of `.env` values for notifications, so behaviour is per user (D-31).

## Context to read (only these)
- `docs/project/architecture-decisions.md` D-64 (settings in scope)
- APP-008's `UserStore`; `apps/pipeline/src/fantasy_pipeline/daily_brief.py` (where notification settings are read)

## User stories and edge cases
| Persona | Story | Edge cases |
|---|---|---|
| Owner, phone | "Move my brief to 08:30 and mute injury alerts" | invalid time / time zone → 422 with the field named; partial update leaves the other fields alone |
| Owner, two tabs | Edits in both | the stale tab's save → 412 `stale-settings` with the current values (ETag/If-Match), never a silent overwrite |
| Member | "Link my Telegram" | the bot's `/start <code>` (via the webhook) links the chat; codes are single-use and expire in 10 minutes; relinking replaces the old chat |
| Any | Export / delete | export returns the profile + settings JSON; delete removes them (the last owner can't, 409) |
| New user | No settings yet | defaults returned (time zone Australia/Sydney, brief on, theme system), not 404 |
| Attacker | Reads another user's settings | impossible by construction: only `/me/...` routes, uid from the token |

## Acceptance criteria
- [x] AC1: `GET /me/settings` returns stored values or documented defaults with an `ETag`.
      Verify: `apps/api/tests/test_settings.py::test_defaults`, `::test_etag`
- [x] AC2: `PATCH /me/settings` validates each field (IANA zone, HH:MM window, enum alerts/strategy/theme) and
      requires `If-Match`; a mismatch → 412 with the current document; a missing header → 428.
      Verify: `test_settings.py` (valid, each invalid field, 412, 428)
- [x] AC3: Telegram linking: `POST /me/telegram/link` issues a code; `POST /telegram/webhook` (verified by Telegram's
      secret-token header; G-30 A) binds the chat on `/start <code>`; reuse, expiry, a bad secret and unrelated
      messages fail cleanly.
      Verify: `test_settings.py::test_telegram_link_*`, `::test_webhook_*`
- [x] AC4: `GET /me/export` and `DELETE /me` behave per the table.
      Verify: `test_settings.py::test_export`, `::test_delete`, `::test_last_owner_cannot_delete`

## Plan
1. `Settings` model (defaults per D-64), validation (IANA zone via `zoneinfo`, HH:MM, enums), version for ETags.
2. `UserStore` gains settings (compare-and-set on the version), Telegram link codes (single use, 10 min) and the
   chat binding; in-memory + Firestore adapters, both under the store contract tests (emulator in CI).
3. Routes: `GET/PATCH /me/settings` (ETag / If-Match → 412 with the current document, 428 without),
   `POST /me/telegram/link`, `GET /me/export`, `DELETE /me`; OpenAPI + TS types regenerated.
4. G-30 (A, A): `/start <code>` arrives by webhook (`POST /telegram/webhook`, secret-token header, rate limited);
   the daily brief's use of the settings (old AC5) moves to APP-010 with the shared users package.

## Test requirements
In-memory store adapter; frozen clock for code expiry; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | API | `apps/api/tests/test_settings.py::test_defaults`, `::test_etag` (+ `::test_settings_are_per_user`) | pass: documented defaults at version 0, `ETag: "settings-v<n>"`, `no-store` |
| AC2 | API + store contract | `test_settings.py` › valid partial update, each of 8 invalid fields named (`field` member, nothing saved), unknown field 422, stale → 412 `stale-settings` with `current` + fresh ETag, garbage tag → 412, missing → 428; `test_users_store.py::test_settings_compare_and_set` (memory; Firestore on the CI emulator) | pass |
| AC3 | API + store contract | `test_settings.py::test_telegram_link_*` (binds; relink replaces; single use; 10-min expiry; keeps other settings via CAS; case-insensitive), `::test_webhook_*` (bad/missing secret 401, unrelated updates 200 `{}`, bare `/start` and bad code answered inline, off (404) without a secret, not in the public schema); `test_users_store.py::test_link_codes_are_single_use_and_expire` | pass |
| AC4 | API | `test_settings.py::test_export`, `::test_delete` (user and settings gone), `::test_last_owner_cannot_delete` (409), `::test_routes_need_sign_in` | pass |

## Implementation history
- 2026-10-02 — Specified; waits on G-25 and APP-008.
- 2026-10-04 — Built: `users/settings.py` (model, validation table), `users/settings_service.py` (CAS update,
  link codes, link, delete-me), `users/settings_routes.py`; `UserStore` gained `get_settings`,
  `save_settings_if` (compare-and-set), `save_link_code`, `use_link_code` (atomic single use), in memory and
  in Firestore (`settings/{uid}`, `link_codes/{code}`; deleting a user deletes their settings in the same
  transaction). Problem details gained extension members (`field` on a 422, `current` on a 412). The webhook
  answers inline (a `sendMessage` in the response), so no outbound Telegram call; it is excluded from the
  OpenAPI document. CORS allows PATCH and If-Match and exposes ETag. Also `fantasy_core.settings.telegram_webhook_secret` (unset = webhook off) and the regenerated TS types
  (both added to `areas:` after review). Review (PASS): a link that loses the settings race 3 times now says
  so ("busy") instead of "invalid code".
  `api` tests: 121 passed, 7 skipped (Firestore emulator; CI runs them).

## Decisions
- Depends on APP-008's merged `UserStore` code; APP-008 stays open only for its AC7 (the owner's `terraform apply`
  for Firestore). Until `users_backend = "firestore"`, settings live in memory and reset on a restart.
- G-30 APPROVED (A, A), 2026-10-03: webhook; a shared users package. AC5 (the daily brief reads the settings)
  moved to APP-010, which does the package move.

## Known issues
- The webhook is off in the cloud until its secret exists (see Follow-ups); linking works only after that.

## Follow-ups
- Infra (Tier B, owner review): a `telegram-webhook-secret` in Secret Manager, `TELEGRAM_WEBHOOK_SECRET` on the
  API service, and a one-off `setWebhook` (url `<api>/telegram/webhook`, `secret_token`) once the bot's polling
  is off (a bot can't poll and use a webhook at once).
- APP-010: the shared users package; the daily brief reads these settings (time zone, awake window, alerts).
- The Settings page in the web app (not in this task's scope).
