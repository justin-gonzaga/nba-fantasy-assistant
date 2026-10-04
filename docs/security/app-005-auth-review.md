# Security review: API sign-in (APP-005, D-27)

Scope: `apps/api/src/fantasy_api/auth.py`, its use in the routers, `main.require_auth_config`, and the Cloud Run
environment in `infra/terraform/modules/env/run.tf`. Reviewed 2026-09-28.

| # | Threat | Mitigation | Test / evidence |
|---|---|---|---|
| 1 | Anyone on the internet reads league data | Every data route (`/today`, `/matchup`, `/waivers`, `/system/freshness`) depends on `current_user`; only `/system/health` is public | test_auth.py `test_data_routes_need_a_token` |
| 2 | Forged or expired token | Google's `verify_firebase_token` checks the signature against Google's rotating keys, expiry, issuer and audience (= this env's Firebase project) | `firebase_verifier`; invalid tokens -> 401 (`test_invalid_tokens_are_401_and_strangers_403`) |
| 3 | A valid Google account that isn't the owner | Verified email must be on the allowlist; unverified emails are refused | 403 for stranger and unverified (same test) |
| 4 | Deployed "open" by mistake | Outside `APP_ENV=local` the API refuses to start without an allowlist and a project; Cloud Run's default allowlist is empty | `test_outside_local_an_allowlist_is_required`; terraform run `api_fails_closed_without_an_allowlist` |
| 5 | The owner's email published in a public repo | The allowlist is a sensitive Terraform variable set in a git-ignored `owner.auto.tfvars` | `.gitignore` `*.tfvars`; `owner.auto.tfvars.example` has a placeholder |
| 6 | Brute force / scraping with a stolen token | Per-user rate limit (60 requests/minute, sliding window) -> 429 | `test_rate_limit_per_user_with_a_window` |
| 7 | Error details leak internals | RFC 9457 problem+json; no stack traces; unhandled errors logged by type only | test_errors.py |
| 8 | Token logged | Tokens are never logged; the logger redacts secret-like keys (dikit.logging) | code inspection |

Residual risks and follow-ups
- The rate limit is per instance (in memory); with at most 2 instances the effective limit is up to 2x. Acceptable
  for one user; revisit if the demo chat (D-38) opens.
- The Cloud Run service has no public invoker yet. WEB-013 adds the SPA's Google sign-in and then the
  `allUsers` invoker; the app-level checks above are what protect data from that point on.
- Google sign-in must be enabled in the Firebase console (Authentication -> Sign-in method -> Google): an owner
  step, listed in docs/runbooks/api-hosting.md.
