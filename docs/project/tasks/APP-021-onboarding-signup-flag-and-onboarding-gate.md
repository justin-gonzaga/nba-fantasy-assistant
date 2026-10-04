---
id: APP-021
title: "Onboarding, the OPEN_SIGNUP flag and the onboarding gate"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-012, APP-018, APP-026]
areas: [apps/api/src/fantasy_api/onboarding/**, apps/api/tests/test_onboarding.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-021 — Onboarding and the sign-up flag

## Objective
Today APP-005/APP-008 answer `403 not-invited` to anyone not on the owner's list. Courtside needs anyone to be able to
register (D-72 Q1, D-74) without widening what a new account can see. This task adds the profile creation at
onboarding (username from APP-012, terms and age confirmation), the `OPEN_SIGNUP` flag (default **off**), and the
gate that keeps a not-yet-onboarded identity away from everything else. How an identity is verified is APP-018; this
task consumes its `Identity`.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §2, §6 (sign up), §8
- `docs/standards/user-data-and-auth.md` (consent, minimisation)
- `apps/api/src/fantasy_api/users/*`, `auth/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Stranger, flag on | "I sign up and pick a name" | verified identity but no profile: only `/me`, `/me/onboarding`, `/usernames/*`, `/auth/*` work; others 403 `onboarding-required` |
| Stranger, flag off | "sign-ups are closed" | `POST /me/onboarding` returns 403 `signup-closed`; invited users and the owner still pass (APP-008 invites keep working) |
| Under-age or no consent | "I must confirm" | requires `ageConfirmed13: true` and the current `termsVersion` and `privacyVersion`; stores timestamp and versions on the user document (re-acceptance after a version change is APP-019), never a birthdate |
| Double submit / retry | idempotent | the same body returns 200 with the same profile, not 409 |
| Unverified identity | refused | 403 `identity-unverified` from APP-018's `Identity` |
| Existing owner or invited member | unchanged | their role and settings are untouched; they are onboarded on first call with a suggested username |
| Flag flipped during traffic | immediate | read from config per request (cached ≤ 30 s); change is a security event |
| New role | least privilege | new accounts are `member`: demo data and leagues only, never the live Yahoo data (D-64) |

## Acceptance criteria
- [ ] AC1: `POST /me/onboarding` creates the profile (`username`, `usernameLower`, consents, role `member`) for a
      verified identity, once and idempotently.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "create or idempotent or unverified"`
- [ ] AC2: `OPEN_SIGNUP` off: strangers get 403 `signup-closed`; an invited or owner identity still onboards;
      turning it on needs no deploy and is logged as a security event.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "flag"`
- [ ] AC3: until onboarded, every route other than the allow-list returns 403 `onboarding-required`; the gate is one
      default dependency and the allow-list is explicit.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "gate"` (walks the OpenAPI routes)
- [ ] AC4: terms/privacy confirmation is required and recorded with versions; no birthdate or exact age is stored.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "consent or no_birthdate"`
- [ ] AC5: a `member` can never read owner-only data: a route-walk test calls every owner-only route as a member and
      expects 403.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "member_cannot"`
- [ ] AC6: privacy: only `/me` returns email/consent fields; the client is regenerated with no diff.
      Verify: `uv run pytest -q apps/api/tests/test_onboarding.py -k "privacy"`; `just api-client` twice, no diff

## Test requirements
Route-walk tests; contract tests on both stores; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (split from the original APP-012 because tasks are S or M).

## Decisions
- No birthdate is stored: the only age record is the 16+ confirmation (data minimisation).

## Known issues
_None._

## Follow-ups
- APP-019 exports and APP-025 deletes these fields.
