# User Data and Authentication Standard

Status: **Accepted** (D-74 and S-40, approved by the owner 2026-10-04). Rules are enforced by the named tasks as they ship; until a
task ships, the rule guides review.

Scope: every Courtside account, sign-in method, stored personal field, upload, log line and export. It supersedes the
"invited users only" wording in `security.md` §2 once D-74 is approved (live Yahoo data stays owner-only either way).
Evidence base: `docs/research/user-data-privacy-and-auth.md` (sources `P-xx`; not legal advice). Rule ids `UDR-xx` are the
research ids, so a rule can be traced to its source.

How to read a rule: each is one testable sentence. **Enforced by** names the task that builds the check. A value marked
(design) is a choice, not a sourced number. Rules marked **UNVERIFIED** depend on a fact that spike RSCH-010 settles; do
not build on them until that note is closed.

## 1. Principles
1. **Collect less.** A personal field with no entry in the data inventory (UDR-21) is not collected.
2. **One door.** Clients never read user data directly; everything goes through the API (UDR-26), which calls `can()`.
3. **One registry.** Anything that stores user data is listed in `USER_DATA_OWNERS`; export and deletion are built from it.
4. **Identifiers, not people, in logs.** Logs carry the UID only (UDR-29).
5. **Fail closed.** An unknown provider, a missing counter or a stale token is refused or limited more, never less.
6. **Spend is a security control.** SMS, billing and storage have caps and alerts (UDR-19).

## 2. Authentication
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-01 | An account needs a verified contact (provider-verified email, verified Firebase email, or verified phone) before it may create a league, set a public username or upload an image. | APP-018, APP-021 |
| UDR-02 | Passwords: at least 15 characters, at least 64 allowed, no composition rules, no periodic expiry. | APP-018, INFRA-009, WEB-030 |
| UDR-03 | Breached or common passwords are rejected. Firebase cannot enforce this server-side, so the client checks against a k-anonymity breach list (a third-party call that is listed in the processors register) and the default sign-in offers a passwordless method. (Q1 of D-74.) | WEB-030, SEC-003 |
| UDR-04 | Email-enumeration protection is on; a test shows sign-in, reset and sign-up responses are the same for known and unknown emails. | INFRA-009, APP-018 |
| UDR-05 | Optional TOTP for everyone; mandatory for the owner and for admin routes; enrolment needs a verified email. Firebase TOTP has no recovery codes, so recovery is owner-assisted after a verified-email check (RSCH-010). | APP-027, WEB-036 |
| UDR-06 | Linking providers needs a fresh sign-in with the existing method; an identity with `email_verified = false` is treated as unverified in every authorisation decision. **UNVERIFIED** takeover behaviour (SPK-2). | APP-018, RSCH-010 |
| UDR-07 | Email change, MFA change, provider link or unlink and account deletion need a sign-in no older than 5 minutes (design) and notify the old address. | APP-027 |

## 3. Sessions
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-08 | The API verifies signature, `aud`, `iss`, `exp`, `iat`, `sub` and an allow-list of sign-in providers on every request. | APP-018 |
| UDR-09 | Writes and account-level routes verify with revocation checking. Latency cost is measured first. **UNVERIFIED** (SPK-4). | APP-027, RSCH-010 |
| UDR-10 | Absolute session lifetime at most 30 days (design). A server session cookie, if used, is `httpOnly`, `secure`, `SameSite`, named `__session`, 5 minutes to 14 days. | APP-018 |
| UDR-11 | Refresh tokens are revoked on password reset, account disable, suspected compromise and "sign out everywhere". | APP-027 |
| UDR-12 | An ADR records where the browser keeps tokens and the XSS mitigations (strict CSP, `Referrer-Policy: no-referrer` on invite and auth pages). **UNVERIFIED** (SPK-3). | RSCH-010, WEB-030, INFRA-010 |

## 4. Account recovery
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-13 | Reset, email-link and verification flows give the same message and similar timing whether or not the account exists. | APP-018 |
| UDR-14 | Recovery and email-link tokens are single use, HTTPS only and rate limited; a reset does not sign the user in and invalidates sessions. | APP-018, APP-027, APP-024 |
| UDR-15 | No security questions; recovery never bypasses an enrolled MFA factor. | APP-018 |

## 5. Phone and SMS (off at launch unless G-35 Q2 says otherwise)
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-16 | The SMS region policy is an allow-list of served countries (initially US); a test refuses other country codes; Firebase test numbers exist only in dev. | INFRA-009, APP-018 |
| UDR-17 | reCAPTCHA SMS defence runs in AUDIT, then ENFORCE (threshold about 0.8), before phone sign-in is enabled in prod. | INFRA-009 |
| UDR-18 | Phone is never the only recovery factor; a non-SMS alternative is offered; changing the number needs a fresh sign-in and notifies the account email. | APP-018, APP-027 |
| UDR-19 | SMS spend is bounded by controls that really sit in the send path: the region allow-list, reCAPTCHA SMS defence, the provider's own per-number and per-IP throttles, a billing budget with a usage alert, and the `AUTH_METHODS` kill switch. The API cannot cap SMS or verification emails, because the client SDK sends them directly; a drill measures the real cap (SEC-002). | INFRA-009, APP-018, SEC-002 |
| UDR-20 | Phone numbers are stored only if needed, shown masked, looked up by keyed hash (HMAC, pepper in Secret Manager), never returned to others and never logged. | APP-018, APP-020 |

## 6. Data minimisation and retention
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-21 | A data inventory lists every stored personal field with purpose, lawful basis and retention. | SEC-003 |
| UDR-22 | A neutral age screen blocks under 13; the date of birth is not stored; the Terms state the minimum age. EU age is the owner's decision (Q5). | WEB-037, APP-021 |
| UDR-23 | Ephemeral data (invites, sim runs, rate counters, reports) carries a Firestore TTL field; jobs tolerate up to 24 h delay. | INFRA-010, APP-025 |
| UDR-24 | No non-essential cookies or third-party trackers; analytics, if any, is cookieless or consent-gated. | WEB-037 |
| UDR-25 | Optional processing is opt-in, records time and version, and is withdrawable in one step. | APP-019, APP-021 |

Retention values (owner confirms in G-35): security events 180 days (design), reports 180 days, activity logs 180 days, invite tokens until expiry,
inactive accounts: no automatic deletion at launch, backups: the platform maximum is disclosed in the privacy notice.

## 7. Storage and encryption
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-26 | Firestore client rules are deny-all; user data is reached only through the API; CI fails on a permissive rule (a test over the rules file, run in `just check`). | APP-008, APP-026 |
| UDR-27 | Secrets live only in Secret Manager with version history; the repo holds none. | existing gitleaks |
| UDR-28 | User-data buckets use uniform bucket-level access and public access prevention; only the dedicated avatar bucket is public-read, and it holds only server-produced re-encoded files; the quarantine and exports buckets keep public access prevention. | INFRA-010, APP-013 |

## 8. Logging
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-29 | Logs record authentication and authorisation outcomes keyed by a pseudonymous account id (HMAC of the UID) only, never the raw UID; never passwords, tokens, OTP codes, full emails or full phone numbers; user text is sanitised against CR/LF; timestamps are UTC. | APP-020 |

## 9. User rights
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-30 | "Delete my account" removes the Auth user, owned documents (with subcollections), the avatar and provider links within one month of the request: a 14-day grace period in which signing in cancels, then a cascade that finishes within 7 days. | APP-025 |
| UDR-31 | A test creates a user across every registered collection, deletes the account and asserts nothing remains (backups excepted). | APP-025 |
| UDR-32 | The privacy notice states that deleted data can remain in backups for a bounded period. | SEC-003, WEB-037 |
| UDR-33 | Users can download a JSON export and correct their username, avatar and email in the app. | APP-019, WEB-036 |

## 10. Uploads
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-34 | Only JPEG, PNG and WebP, decided by file signature, never by client `Content-Type`; SVG and everything else is rejected. | APP-013 |
| UDR-35 | Every image is decoded and re-encoded to a fixed maximum size (strips EXIF and GPS); 2 MB and a pixel cap (design). | APP-013 |
| UDR-36 | Objects get random server-generated names, are re-encoded to WebP and served from the storage origin (`storage.googleapis.com`, separate from the site) with the headers checked in INFRA-010, and uploads need authentication and a per-user quota. | APP-013, INFRA-010 |
| UDR-40 | Usernames are unique case-insensitively, normalised against look-alikes, with a reserved list and a report-and-reset flow (`kind: username`, owner action `reset`). | APP-012, APP-017 |

## 11. Third parties and incidents
| Rule | Statement | Enforced by |
|---|---|---|
| UDR-37 | A processors register lists every third party with the data shared, region and contract basis. | SEC-003 |
| UDR-38 | A breach runbook names who decides, the 72-hour clock where GDPR applies and when users are told. | SEC-003 |
| UDR-39 | The runbook includes a tested kill switch (revoke all tokens, disable a provider, rotate secrets) and a drill before open sign-up and then quarterly (design). | SEC-002, SEC-003 |

## 12. Change control
- A new feature that stores personal data adds its collection to `USER_DATA_OWNERS` and a row to the data inventory in the
  same PR; the coverage test fails otherwise (APP-026, which owns the registry; HYG-001 checks the data inventory row).
- A new rule, or a relaxed one, is a Tier B change with an entry in `standards-decisions.md`.
- Legal items (GDPR scope, minimum age in the EU, fantasy-sports law by state, US breach-notification law, Yahoo and NBA
  data terms) are outside this standard and listed in G-35 for a lawyer or the owner.
