---
id: APP-018
title: "Identity from a verified token, sign-in method policy, linking and auth config"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-008, APP-020]
areas: [apps/api/src/fantasy_api/auth/**, apps/api/tests/test_auth_identity.py, apps/api/tests/test_auth_policy.py, apps/api/tests/test_auth_tokens.py, apps/api/tests/test_auth_config.py, packages/core/**]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-018 — How an identity is verified and trusted

## Objective
The owner wants sign-up with Google, email, phone and other providers, each with verification codes where they apply.
Firebase Auth / Identity Platform performs the sign-in; **the API decides what is trusted**. This task adds one
function that turns a verified ID token into an `Identity` (uid, method, `emailVerified`, `phoneVerified`, auth time,
MFA level) and applies the project's rules to it: which methods are accepted, when an unverified email is refused, how
provider linking is allowed. It also publishes `GET /auth/config` (public), the single source the web app uses to show
methods and the password policy. Rate limits are APP-024; step-up, MFA and session revocation are APP-027. Security events go through APP-020
(`record_event`). Rules:
`docs/standards/user-data-and-auth.md` (Authentication, Account recovery, Phone).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Authentication, Account recovery, Phone/SMS), `docs/standards/security.md` §2
- `apps/api/src/fantasy_api/auth/*` (APP-005), `users/*` (APP-008)
- `docs/research/user-data-privacy-and-auth.md` (sources, only if a rule needs checking)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Google user | "sign in with Google" | Google email is verified by Google; accepted; the profile is created at onboarding (APP-021), not at first token |
| Email/password user | "I verify my email" | until `email_verified` the identity is `unverified`: only `/me`, `/auth/*`; no profile, no leagues; verification expiry and resend throttling are the provider's (the client SDK sends the email, so this API cannot cap it: APP-024 note; SEC-002 measures it) |
| Phone user | "text me a code" | accepted only when the provider is `phone` and the country is on the allow-list; the number is never returned by any API (a masked form only for the account page) |
| Takeover by linking | "attacker pre-registers my email" | an unverified email/password account is never merged with a later Google sign-in on the same email; linking needs a recent sign-in with the existing method and the old unverified account is deleted, not adopted |
| Token replay / forged token | rejected | wrong audience/issuer, expired, unsigned, other project, disabled user: 401 with no detail, tested with crafted tokens |
| Disposable email domains | "no throwaway farms" | a maintained deny-list refuses sign-up with a neutral message; not applied to existing accounts |
| Provider outage | degrade | verification keys cached; existing sessions work until expiry; sign-up shows a retry |
| Enumeration | no oracle | the API never confirms whether an email or phone exists; `auth/config` is identical for all callers |
| Method disabled by the owner | config change | disabled method: new sign-ups 403 `method-disabled`; existing accounts using it keep working unless the owner says otherwise |

## Acceptance criteria
- [ ] AC1: `identity_from_token()` is the only code that reads provider claims; every route uses `Identity`, and a grep
      test fails on `firebase_admin.auth` use outside `auth/`.
      Verify: `uv run pytest -q apps/api/tests/test_auth_identity.py`; `grep -rn "firebase_admin" apps --include=*.py`
      lists only `auth/`
- [ ] AC2: method policy: accepted methods come from configuration (`AUTH_METHODS`), default `google,password`;
      unverified email accounts are refused everywhere but `/me` and `/auth/*`; phone is accepted only for allowed
      countries.
      Verify: `uv run pytest -q apps/api/tests/test_auth_policy.py -k "methods or unverified or country"`
- [ ] AC3: linking never merges an unverified account with a verified one; adoption attempts are rejected and logged as
      a security event (APP-020).
      Verify: `uv run pytest -q apps/api/tests/test_auth_policy.py -k "linking or takeover"`
- [ ] AC4: crafted-token tests (wrong audience, issuer, expired, `none` algorithm, other project, disabled user) all
      return the same 401 body.
      Verify: `uv run pytest -q apps/api/tests/test_auth_tokens.py`
- [ ] AC5: `GET /auth/config` (public, cacheable 60 s) returns `{methods[], password:{minLength, breachCheck},
      phoneCountries[], signupOpen, mfa}` and nothing that varies by caller; no secrets.
      Verify: `uv run pytest -q apps/api/tests/test_auth_config.py`
- [ ] AC6: the disposable-email deny-list and the country allow-list are data files with tests; existing invited and
      owner accounts are unaffected.
      Verify: `uv run pytest -q apps/api/tests/test_auth_policy.py -k "disposable or existing"`
- [ ] AC7: a policy outcome that matters (linking refused, method disabled, unverified access, forged token) calls
      `record_event`; an unauthenticated 401 does not (no flood).
      Verify: `uv run pytest -q apps/api/tests/test_auth_policy.py -k "events"`
- [ ] AC8: a phone number, if stored, is stored only as a keyed hash (HMAC with the pepper from Secret Manager, INFRA-010)
      plus a masked display form, and is registered in `USER_DATA_OWNERS`; phone is off unless `AUTH_METHODS` says so.
      Verify: `uv run pytest -q apps/api/tests/test_auth_policy.py -k "phone_hash or phone_off"`

## Test requirements
Token factories signing with a test key; Firebase Auth emulator for the linking flows in CI; no real SMS.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified from the owner's request for multi-method sign-up with verification codes; step-up, MFA,
  revocation and limits split to APP-024.

## Decisions
- Trust decisions live in the API, not in client SDK behaviour or console toggles alone: the configuration is code,
  tested and reviewable (one policy module).

## Known issues
- Phone sign-in needs the Identity Platform upgrade and costs per SMS; it stays off until G-35 and INFRA-009. The code
  and tests need only the emulator, so this task does not wait for INFRA-009.

## Follow-ups
- Passkeys (WebAuthn) when the provider supports them in a way we can enforce server-side.
