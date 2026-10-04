# User Data, Privacy and Authentication — Ruleset Research for Courtside

Access date for all entries: **2026-10-04**.
Question: what defensible ruleset should Courtside (open sign-up, user-created leagues, usernames, avatars, real users mostly in the US but possibly anywhere; Firebase Auth / Identity Platform, Firestore, GCS, Cloud Run FastAPI, Firebase Hosting SPA) adopt for authentication and user-data handling?

**Method.** Each page below was opened with WebFetch. WebFetch returns a *summary* made by a small model, not raw text, so quoted numbers are High confidence only where I re-fetched or cross-checked them (NIST 800-63B-4 was fetched twice, at two URLs) and Medium otherwise. Two pages (Identity Platform pricing, EUR-Lex ePrivacy, GDPR) returned nothing useful when fetched directly, or were truncated, and were read via the `r.jina.ai` text proxy (same technique as `ux-modern-interface.md`). Search-engine snippets were used only to find URLs and are never cited as evidence. Page content was treated as data. This is research, not legal advice.

Citation IDs: **P-01, P-02, …** (no topic prefix existed that fit). Rule IDs: **UDR-01, …** (`R-xx` is taken by `ml-literature-review.md`). Status: **Verified** (page opened, content matches the claim) or **UNVERIFIED**.

---

## (a) Sources verified

| ID | Source | URL (all opened 2026-10-04) | What was verified |
|---|---|---|---|
| P-01 | NIST SP 800-63B-4 Authentication and Authenticator Management (final, 2025) | https://pages.nist.gov/800-63-4/sp800-63b.html ; https://pages.nist.gov/800-63-4/sp800-63b/authenticators/ | Password length/composition/blocklist/rotation, throttling (100), PSTN "restricted", AAL timeouts, syncable authenticators, recovery codes |
| P-02 | OWASP ASVS **5.0.0** (GitHub tag v5.0.0), chapters V6 Authentication, V7 Session Management, V9 Self-contained Tokens | https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x15-V6-Authentication.md ; `0x16-V7-Session-Management.md` ; `0x18-V9-Self-contained-Tokens.md` | Requirement IDs and levels quoted below. File list of the tag: https://api.github.com/repos/OWASP/ASVS/contents/5.0/en?ref=v5.0.0 |
| P-03 | OWASP ASVS 5.0.0 V5 File Handling | https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x14-V5-File-Handling.md | 5.2.1, 5.2.2, 5.2.4, 5.2.6, 5.3.2, 5.4.1 |
| P-04 | OWASP ASVS 5.0.0 V14 Data Protection and V16 Logging/Error Handling | https://raw.githubusercontent.com/OWASP/ASVS/v5.0.0/5.0/en/0x23-V14-Data-Protection.md ; `0x25-V16-Security-Logging-and-Error-Handling.md` | 14.1.1, 14.2.1, 14.2.7, 14.3.x; 16.2.x, 16.3.x, 16.4.x |
| P-05 | OWASP Authentication Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html | Length, no composition rules, breached-password check, generic errors, email-change re-auth |
| P-06 | OWASP Password Storage Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html | Argon2id/scrypt/bcrypt/PBKDF2 parameters; pepper |
| P-07 | OWASP Session Management Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html | Cookie attributes, timeouts, localStorage warning |
| P-08 | OWASP Forgot Password Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html | Uniform responses, token handling, post-reset behaviour |
| P-09 | OWASP Multifactor Authentication Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html | Factor ranking, SMS/SIM-swap weaknesses, step-up, recovery codes |
| P-10 | OWASP File Upload Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html | Allow-list, do not trust Content-Type, random names, storage location, image rewriting |
| P-11 | OWASP Logging Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html | Data to exclude, events to log, log-injection sanitising |
| P-12 | Firebase: Authenticate with a phone number (web) | https://firebase.google.com/docs/auth/web/phone-auth | reCAPTCHA, throttling, SMS region policy, 10 test numbers, number-reuse warning |
| P-13 | Firebase Authentication limits | https://firebase.google.com/docs/auth/limits | SMS, sign-up and email quotas (Spark vs Blaze columns) |
| P-14 | Identity Platform quotas | https://docs.cloud.google.com/identity-platform/quotas | SMS quotas, "instrumentless" daily SMS cap |
| P-15 | Firebase pricing (Authentication section) | https://firebase.google.com/pricing | 50K MAU no-cost; phone auth billed per SMS |
| P-16 | Identity Platform pricing (via `r.jina.ai` proxy; direct fetch truncated) | https://cloud.google.com/identity-platform/pricing | MAU tiers, SMS price samples, first 10 SMS/day free |
| P-17 | Identity Platform: SMS regions | https://docs.cloud.google.com/identity-platform/docs/admin/sms-regions | Allowlist/denylist, SMS pumping rationale |
| P-18 | Identity Platform: reCAPTCHA SMS defense | https://docs.cloud.google.com/identity-platform/docs/recaptcha-tfp | Threshold 0.0-0.9, AUDIT/ENFORCE, platforms |
| P-19 | Identity Platform: password policy | https://docs.cloud.google.com/identity-platform/docs/password-policy | Min length 6-30, max 4,096, character-class options, require/notify modes |
| P-20 | Identity Platform: MFA (web) | https://docs.cloud.google.com/identity-platform/docs/web/mfa | SMS and TOTP MFA, email verification prerequisite, unsupported first factors |
| P-21 | Identity Platform: email enumeration protection | https://docs.cloud.google.com/identity-platform/docs/admin/email-enumeration-protection | Default on for projects created on/after 2023-09-15; affected methods |
| P-22 | Identity Platform: users, email verification and provider linking | https://docs.cloud.google.com/identity-platform/docs/concepts-manage-users | Trusted/untrusted providers; linking rules; account-takeover rationale |
| P-23 | Identity Platform: linking multiple providers | https://docs.cloud.google.com/identity-platform/docs/link-accounts | "Link accounts using the same email" vs "multiple accounts" settings |
| P-24 | Firebase Admin: manage user sessions | https://firebase.google.com/docs/auth/admin/manage-sessions | ID token 1 h; refresh-token revocation triggers; `checkRevoked` |
| P-25 | Firebase Admin: session cookies | https://firebase.google.com/docs/auth/admin/manage-cookies | Cookie lifetime 5 min to 2 weeks; `__session` on Hosting; CSRF; 5-minute `auth_time` check |
| P-26 | Firebase Admin: verify ID tokens | https://firebase.google.com/docs/auth/admin/verify-id-tokens | Claims checked (aud, iss, exp, iat, sub) |
| P-27 | Firebase: email link sign-in | https://firebase.google.com/docs/auth/web/email-link-auth | Email must be re-entered on other device; unverified methods removed after link sign-in; HTTPS |
| P-28 | Firebase: manage users | https://firebase.google.com/docs/auth/web/manage-users | Recent sign-in required for email change, password change, delete |
| P-29 | Firebase: blocking functions | https://firebase.google.com/docs/auth/extend-with-blocking-functions | Four triggers; Identity Platform upgrade required; 7-second limit |
| P-30 | Firebase App Check | https://firebase.google.com/docs/app-check | Supported products incl. Authentication (**Preview**), Firestore, Storage; custom backends |
| P-31 | Firebase: auth state persistence | https://firebase.google.com/docs/auth/web/auth-state-persistence | Default web persistence is `local` |
| P-32 | Firebase: Sign in with Apple (web) | https://firebase.google.com/docs/auth/web/apple | Apple Developer Program membership required; private relay email setup; consent note |
| P-33 | Apple App Store Review Guidelines | https://developer.apple.com/app-store/review/guidelines/ | 4.8 Login Services; 5.1.1(v) in-app account deletion |
| P-34 | GDPR Regulation (EU) 2016/679 (EUR-Lex, via `r.jina.ai` proxy; direct fetch returned empty) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679 | Arts 3(2), 5, 6, 7, 8, 12(3), 15-20, 25, 32, 33, 34 (summarised) |
| P-35 | ePrivacy Directive 2002/58/EC consolidated (via `r.jina.ai` proxy) | https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:02002L0058-20091219 | Art 5(3) consent and "strictly necessary" exemption |
| P-36 | California AG: CCPA | https://oag.ca.gov/privacy/ccpa | Applicability thresholds; consumer rights |
| P-37 | California Privacy Protection Agency FAQ | https://cppa.ca.gov/faq.html | Revenue threshold adjusted to $26.625 M effective 2025-01-01 |
| P-38 | FTC COPPA FAQ | https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions | Scope, under-13, actual knowledge, age screens, retention; rule amended 2025-04-22 |
| P-39 | Google Cloud: default encryption at rest | https://docs.cloud.google.com/docs/security/encryption/default-encryption | AES-256, envelope encryption, CMEK optional |
| P-40 | Google Cloud: encryption in transit | https://docs.cloud.google.com/docs/security/encryption-in-transit | TLS to Google front end; customer-managed gaps |
| P-41 | Secret Manager overview | https://docs.cloud.google.com/secret-manager/docs/overview | Encryption, versioning, IAM, audit, rotation |
| P-42 | Firestore security rules: get started | https://firebase.google.com/docs/firestore/security/get-started | Deny-by-default; rules are not filters |
| P-43 | Firestore TTL policies | https://firebase.google.com/docs/firestore/ttl | Deletion typically within 24 h; no subcollection cascade |
| P-44 | Firestore backups | https://firebase.google.com/docs/firestore/backups | Retention up to 14 weeks; PITR 7 days |
| P-45 | Firestore audit logging | https://docs.cloud.google.com/firestore/docs/audit-logging | Admin Activity vs Data Access logs; Data Access needs enabling |
| P-46 | Firebase Data Processing and Security Terms | https://firebase.google.com/terms/data-processing-terms | Google as processor, SCCs, 30-day sub-processor notice, incident notice, 180-day deletion |
| P-47 | Cloud Storage uniform bucket-level access | https://docs.cloud.google.com/storage/docs/uniform-bucket-level-access | ACLs disabled, IAM only; public access prevention exists |

**Could not open / unusable:** `https://firebase.google.com/docs/auth/admin/delete-accounts` (HTTP 404; not cited). Direct EUR-Lex fetches of GDPR and ePrivacy returned empty (proxy used instead). The first-try ASVS V14/V16 paths returned 404 (chapter numbering differs from 4.0.3; the correct v5.0.0 file names above were found via the GitHub contents API). Identity Platform pricing could not be read directly (truncated), only via the proxy. NIST Privacy Framework and ISO 27001 Annex A were **not fetched and not cited**.

---

## (b) Findings by topic

### 1. Authentication standards

- **Passwords (NIST).** Minimum **15 characters** if the password is the only factor, **8** if used as part of MFA; verifiers should permit **at least 64** characters; **no composition rules**; **no periodic change**; check against a blocklist (breach corpora, dictionary, service name, username derivatives); do not truncate; allow paste; accept Unicode (NFC-normalised). Failed attempts per authenticator on one account must be limited to **no more than 100** consecutive failures (sec. 3.2.2); optional mitigations are bot challenges and escalating delays (30 s to 1 h). [P-01] High
- **Assurance.** AAL1 allows passwords/OOB/OTP; AAL2 needs two factors and must offer a phishing-resistant option; syncable passkeys are allowed at AAL2 and below but **not AAL3**. Reauthentication: AAL1 overall timeout SHOULD be at most 30 days (no inactivity limit); AAL2 at most 24 h overall and 1 h inactivity. [P-01] High (AAL numbers from one fetch, Medium-High)
- **SMS/PSTN.** PSTN out-of-band is a **"restricted" authenticator** (sec. 3.1.3.3): verifiers should weigh risk indicators (SIM change, porting, device swap), must offer alternative authenticator types, and changing the registered phone number needs binding procedures. **Email must not be used as an OOB authenticator.** [P-01] High
- **ASVS 5.0.0.** 6.2.1 (L1) >= 8 chars, 15 strongly recommended; 6.2.5 (L1) no composition rules; 6.2.10 (L2) no forced rotation; 6.2.12 (L2) breached-password check; 6.3.1 (L1) anti-automation vs credential stuffing; 6.3.8 (L3) no user enumeration via messages, status codes or timing; 6.4.3 (L2) reset must not bypass MFA; 6.6.1 (L2) PSTN/SMS only when a stronger option is also offered (L3 prohibits). Sessions: 7.2.3 (L1) >= 128-bit CSPRNG tokens; 7.3.1/7.3.2 (L2) inactivity and absolute timeouts per risk; 7.4.2 (L1) terminate all sessions when an account is disabled/deleted; 7.5.1 (L2) full re-authentication before changing sensitive authentication attributes. V9: 9.1.1-9.1.3, 9.2.1-9.2.3 validate signature, algorithm allow-list, exp/nbf, audience. [P-02] Medium-High
- **OWASP cheat sheets.** Auth: no composition rules, allow >= 64 chars, check breached lists, identical failure message, re-authenticate (and confirm to old and new address) on email change; no fixed lockout numbers given. [P-05] Password storage: Argon2id with >= 19 MiB, t = 2, p = 1 (or 46 MiB t = 1); bcrypt only for legacy (work factor >= 10, 72-byte limit); PBKDF2-HMAC-SHA-256 >= 600,000; pepper optional. [P-06] MFA: ranking passkeys/FIDO2 > TOTP >> SMS/voice/email; SMS "susceptible to SIM swapping"; require step-up for password change, email change and MFA changes; provide single-use recovery codes and more than one factor type; never log OTPs. [P-09] Forgot password: same message and similar timing for existing/non-existing accounts; single-use tokens; rate-limit; no security questions as sole mechanism; do not auto-login after reset; offer/perform session invalidation; `no-referrer`. [P-08] All Medium-High.

### 2. What Firebase Auth / Identity Platform provides

- **Phone auth.** reCAPTCHA is used; Firebase throttles SMS per number (no number published on the web phone-auth page); up to **10 fictional test numbers**; Firebase says phone possession can be transferred between people, so offer phone alongside stronger methods and tell users about the trade-off. [P-12] High
- **SMS quotas.** Firebase limits page: **900 SMS/min, 3,000/day**, per IP **50/min and 500/h**, new accounts **100/h per IP**, phone sign-ins 1,600/min. Identity Platform quotas page: **1,000 SMS/min**, same per-IP numbers, and a default daily limit of **10 SMS/day without a billing instrument ("instrumentless") and no daily limit with billing**; SMS MFA: 10 codes/h per number. Both pages say limits can change without notice. [P-13, P-14] **Conflict:** 3,000/day (P-13) vs 10/day instrumentless (P-14). Which applies to a given project is UNVERIFIED; resolve with a spike.
- **Billing plan.** Firebase pricing page summary: Authentication has a 50K MAU no-cost tier and phone auth "does not require upgrading to Blaze" but is billed per SMS. [P-15] Quotas page: phone auth does not explicitly require billing but daily SMS above the instrumentless cap needs a billing instrument. [P-14] Email-link sign-in is capped at **5 emails/day without billing** vs 25,000/day with; password reset 150/day vs 10,000; verification 1,000/day vs 100,000. [P-13, P-14] **Net:** treat a billing account as required for any real phone or email-link use. Medium (conflicting pages).
- **Identity Platform upgrade.** Blocking functions explicitly require "Firebase Authentication with Identity Platform". [P-29] High. The password-policy and MFA pages are in the Identity Platform docs; the password-policy page says the feature works within Identity Platform (formerly Firebase Authentication). [P-19, P-20] Medium. Whether *every* Identity Platform feature needs the upgrade is UNVERIFIED beyond blocking functions.
- **Prices.** Tier-1 MAUs (email, phone, social, anonymous): free to 50,000, then **$0.0055** (50K-100K), $0.0046 (100K-1M), $0.0032 (1M-10M), $0.0025 (10M+) per MAU. Phone/MFA SMS: first **10 SMS/day not billed**; samples **US $0.01, Canada $0.01, Brazil $0.02, UK $0.04, Germany $0.10** per message. [P-16] Medium (proxy-read; full per-country table not captured). TOTP MFA pricing: not found, UNVERIFIED.
- **SMS regions and fraud.** Identity Platform supports allowlist-only or denylist-only SMS regions (by country calling code), enforced immediately, one type at a time; Google "strongly recommend[s]" a policy limited to operating regions; the MFA page says Identity Platform uses a "fully blocking" default region policy and the phone-auth page says new projects allow no regions by default (the sms-regions page itself states no default, so the default is **UNVERIFIED**; check in the console). [P-17, P-12, P-20] **reCAPTCHA SMS defense** scores each request for toll-fraud likelihood against a threshold in **0.0-0.9** (start at about **0.8**, avoid 0.0 and 1.0), with AUDIT (fallback challenge) and ENFORCE (block) modes; web SDK v11+, Android 23.1.0+, iOS 11.6.0+; it also enables Account Defender. [P-18] Medium (direction of the threshold comparison should be re-read in the console).
- **App Check.** Supports Authentication (**Preview**), Firestore, Storage, callable Functions and custom backends; it attests the app, it does not authenticate users. [P-30] High
- **Email verification and enumeration.** `email_verified` is the signal; email change, password change and delete need recent sign-in. [P-28] Email-enumeration protection is **on by default for projects created on/after 2023-09-15**, makes sign-in return `INVALID_LOGIN_CREDENTIALS`, hides whether emails exist in reset/verification flows, requires verification before email changes and blocks `linkWithCredential` with email credentials. [P-21] High
- **Email-link sign-in.** The email address must be re-entered on a different device (prevents session fixation/wrong-device use); after a successful link sign-in, "any previous unverified mechanism of sign-in will be removed from the user and any existing sessions will be invalidated"; use HTTPS. [P-27] High
- **Account linking / takeover.** Identity Platform has two settings: "link accounts that use the same email" (error then explicit link) or "multiple accounts per provider". Providers are **trusted** (Google for @gmail.com, Yahoo, Microsoft for outlook/hotmail, Apple) or **untrusted** (Facebook, Twitter, GitHub and others): untrusted + untrusted raises an error requiring linking, **trusted overwrites untrusted**, trusted + trusted link without error; the stated rationale is that automatic linking would otherwise let an attacker who created an account with someone else's email gain access. Manual linking requires the user to authenticate with the existing provider first. [P-22, P-23] High. Residual risk (unverified email + password account pre-registered by an attacker) is partly mitigated by the "unverified removed" rule [P-27] but the exact behaviour for email+password pre-registration followed by Google sign-in is **UNVERIFIED**; spike test required.
- **Password policy.** Identity Platform policy: min length **6-30** (default 6), max **4,096**, optional lower/upper/numeric/special requirements, "require" (`forceUpgradeOnSignin: true`) vs "notify" mode, project or tenant level. No breached-password option appeared on the page, so a **blocklist is not provided natively** (UNVERIFIED that none exists). [P-19] Medium
- **MFA.** SMS and **TOTP**; email must be verified before enrolling MFA ("prevents malicious actors from registering ... with an email they don't own"); phone auth, anonymous auth and Apple Game Center do not support MFA enrolment; encourage registering more than one second factor to avoid lockout; SMS MFA needs an active SMS region and user consent for sending. [P-20] High
- **Tokens and revocation.** ID tokens last **1 hour**; refresh tokens have no fixed expiry and are invalidated on account deletion, disable, or "major account change (password or email update)"; `revokeRefreshTokens()` revokes manually; `verifyIdToken(..., checkRevoked=true)` costs a network round trip and detects revocation; plain verification checks aud/iss/exp/iat/sub and signature only. [P-24, P-26] High
- **Session cookies.** Custom lifetime **5 minutes to 2 weeks**; `httpOnly`, `secure`, `sameSite` recommended; CSRF protection required when exchanging tokens; verify with `checkRevoked`; require re-authentication if `auth_time` is older than **5 minutes** before minting a cookie for sensitive apps; behind Firebase Hosting only a cookie named **`__session`** reaches the backend. [P-25] High
- **Client persistence.** Web SDK default persistence is `local` (survives browser close). [P-31] OWASP says never keep auth tokens or refresh tokens in `localStorage`/`sessionStorage` and prefer `HttpOnly; Secure; SameSite` cookies; ASVS 14.3.3 (L2) says browser storage should hold no sensitive data except session tokens. [P-07, P-04] **Tension:** the default SDK pattern conflicts with the OWASP cheat-sheet position; where the SDK stores data (IndexedDB vs localStorage) was not stated on the page, so the exact store is UNVERIFIED.

### 3. Privacy law

- **GDPR scope.** Art 3(2) applies to non-EU controllers that offer goods/services to people in the EU or monitor their behaviour there; a US hobby app with open global sign-up is arguably in scope if it targets or knowingly serves EU users; this is a lawyer question. [P-34] Medium
- **GDPR articles.** Art 5(1): lawfulness/fairness/transparency, purpose limitation, data minimisation, accuracy, storage limitation, integrity/confidentiality (security); 5(2) controller must demonstrate compliance. Art 6(1): consent, contract, legal obligation, vital interests, public task, legitimate interests. Art 7: consent must be freely given, by clear affirmative act, provable, withdrawable. Art 8: child consent age **16**, member states may lower to **13**. Art 12(3): reply to rights requests within **one month**. Arts 15-20: access, rectification, erasure, restriction, notification, portability. Art 25: data protection by design and default. Art 32: appropriate security (encryption, pseudonymisation). Art 33(1): notify the supervisory authority within **72 hours** of becoming aware of a breach (where it is likely to result in a risk); Art 34(1): tell data subjects without undue delay when risk is high. [P-34] Medium-High (summary of an official text; Art 27 content from the same summary was garbled and is **not used**).
- **ePrivacy / cookies.** Art 5(3): storing or accessing information on a user's device needs consent, except storage "strictly necessary in order for the provider of an information society service explicitly requested by the ... user" to provide the service. Auth and session storage fall under the exemption; analytics/advertising do not. [P-35] High
- **CCPA/CPRA.** A for-profit business is covered if it meets **any one** of: annual gross revenue of **$26.625 M or more** (adjusted effective 2025-01-01; the AG page still shows $25 M), buys/sells/shares personal information of **100,000 or more** California residents or households, or derives **50% or more** of revenue from selling/sharing personal information. Rights: know, delete, correct, opt out of sale/sharing, limit use of sensitive PI, non-discrimination. [P-36, P-37] High. A free hobby app is very unlikely to meet any threshold today; revenue, ads, or data sharing change that. The threshold is for-profit-only; whether a personal project is a "business" is a lawyer question.
- **COPPA.** Covers operators of sites/apps directed to children under 13 and general-audience services with **actual knowledge** they collect from under-13s; personal information includes screen names acting as contact info, phone numbers, persistent identifiers, and photos; verifiable parental consent is needed before collection; **general-audience services may bar under-13s**; if they allow them they should use a neutral age screen; retain child data only as long as necessary; rule amended **2025-04-22**. [P-38] High (summary; amended-rule details not read)
- **Fantasy product age/state-law flag (no source opened).** Age limits for fantasy products depend on whether entry is free or paid and on the state; I did not fetch any statute or regulator page, so nothing here is a legal conclusion. A free, no-prize product with a 13+ account rule is the lowest-risk shape; any paid entry, prizes, or cash-equivalent rewards need legal review. UNVERIFIED.
- **Not covered:** US state breach-notification laws, other US state privacy laws, UK GDPR, TCPA/CAN-SPAM for SMS and email, NIST Privacy Framework, ISO 27001 Annex A.

### 4. Data handling on GCP

- **Encryption at rest.** All data stored by Google is encrypted at the storage layer with **AES-256** (a few pre-2015 persistent disks AES-128) using envelope encryption (DEK wrapped by KEK in Keystore); CMEK via Cloud KMS is an optional extra layer. [P-39] High. **In transit:** client requests over HTTPS/HTTP2/HTTP3 to Google services are TLS-protected; traffic leaving Google's network, direct VM routing and custom domains are the customer's responsibility. [P-40] High
- **Secret Manager.** Secrets encrypted with AES-256 at rest and TLS in transit, versioned, IAM-controlled, audit-logged, rotatable; CMEK optional. [P-41] High
- **Firestore access.** Rules are deny-by-default, "test mode" `allow read, write: if true` is never for production, and rules gate whole requests (they do not filter results). [P-42] High. Using Firestore through the API only (deny-all rules for clients) removes the client-rules attack surface; that Admin SDK access bypasses rules is standard but **not stated on any page I opened (UNVERIFIED)**.
- **Retention.** TTL policies delete expired docs "typically within 24 hours" (not instant), count as deletes for billing, allow one TTL field per collection group, and **do not delete subcollections**. [P-43] High. ASVS 14.2.7 (L3): sensitive data subject to retention classification with automatic deletion. [P-04]
- **Backups and deletion propagation.** Scheduled backups can be kept up to **14 weeks (98 days)**; PITR window is **7 days**; deleted data persists in backups until they expire. [P-44] Medium. GDPR erasure must be reconciled with that window (state it in the privacy policy).
- **Audit logs.** Firestore writes Admin Activity logs and, when enabled, Data Access logs; the page did not indicate document payloads are included; logging incurs Cloud Logging cost. [P-45] Medium
- **Logging hygiene.** Do not log passwords, tokens, session IDs (hash them), OTPs, connection strings, or data users have not consented to; log authentication success/failure, authz failures, input validation failures, admin actions and sensitive-data access; sanitise CR/LF to stop log injection; UTC timestamps. [P-11, P-04] ASVS 16.2.5 (L2) credentials never, other data hashed or masked; 16.3.1 (L2) all authentication operations logged; 16.4.1-16.4.3 injection encoding, tamper protection, separate log system. [P-04] Medium-High
- **Data minimisation in responses.** ASVS 14.2.1 (L1) no sensitive data in URLs/query strings; 14.2.6 (L3) return only necessary sensitive data and mask by default (e.g. phone). 14.3.2 sets `Cache-Control: no-store` for sensitive responses. [P-04] Medium
- **Third-party processors.** Firebase terms: Google is processor under European data-protection law; SCCs incorporated for transfers; at least **30 days' notice** of a new sub-processor (with a 90-day termination window); Google notifies the customer of a Data Incident "promptly and without undue delay"; customers must obtain consents from data subjects and keep notification contacts current; deletion of leftover customer data within a maximum of **180 days** after termination plus a 30-day recovery period. [P-46] Medium-High. Apple sign-in requires a paid Apple Developer Program membership and registering the Firebase noreply sender with Apple's private email relay; you must obtain required consent before associating identifying data with an anonymised Apple ID. [P-32] Apple App Store: if an iOS app offers third-party login (e.g. Google) it must also offer an equivalent privacy-limiting login such as Sign in with Apple (4.8), and **in-app account deletion** is mandatory where accounts can be created (5.1.1(v)). [P-33] High (applies to a future `apps/ios`, not to the web SPA).
- **Image uploads.** Allow-list extensions only; do not trust `Content-Type` ("trivial to spoof"), validate file signatures; generate random server-side names (UUID); enforce size limits; preferred storage is a separate server, then outside web root; rewrite images (content disarm and reconstruction); authenticate uploads. [P-10] ASVS: 5.2.1 (L1) size DoS limits; 5.2.2 (L1) validate type via magic bytes/image rewriting; 5.3.2 (L1) internally generated paths; 5.4.1 (L2) set filename in `Content-Disposition`; 5.2.4 (L3) per-user quotas; 5.2.6 (L3) reject images above a maximum pixel size. [P-03] High. The OWASP page summary did not mention EXIF stripping explicitly; image re-encoding removes metadata as a side effect of rewriting (my inference, Medium). Cloud Storage uniform bucket-level access disables ACLs (IAM only) and cannot be disabled after 90 days; public access prevention is a separate control. [P-47]
- **Usernames/impersonation.** No primary standard was opened for this. Rules below are design choices, tagged accordingly.

### 5. Phone numbers (synthesis)

- Phone numbers are personal data and, with an SMS login, an account-recovery credential; Firebase itself warns they can pass between people. [P-12] NIST treats PSTN OOB as restricted and requires an alternative authenticator and risk checks for SIM change/porting. [P-01] OWASP names SIM swapping and recommends TOTP or phishing-resistant factors. [P-09]
- Cost control layers available: SMS region policy, reCAPTCHA SMS defense, App Check (Auth is Preview), platform per-IP caps (50/min, 500/h) and per-project daily caps, billing alerts (not researched). [P-17, P-18, P-30, P-14]
- "Hashed lookup" of a phone number: phone numbers have low entropy, so a plain hash is reversible by enumeration; a keyed hash (HMAC with a pepper kept in Secret Manager) is needed. This is my reasoning, supported only in part by the pepper concept in [P-06] and Secret Manager [P-41]. Medium.

---

## (c) Candidate rules

Each rule is one testable sentence. "(design)" means the number is a design choice, not a sourced value.

### Authentication
- **UDR-01** Every account must have a verified contact (`email_verified = true` from the provider or the Firebase verification flow, or a verified phone number) before it may create a league, set a public username, or upload an image. [P-20, P-22, P-05]
- **UDR-02** Email/password accounts must enforce a minimum length of 15 characters (policy range 6-30 allows this), allow at least 64 characters, and impose no composition rules and no periodic expiry. [P-01, P-19, P-05]
- **UDR-03** The sign-up path must reject passwords found on a common/breached list (a blocklist check outside the Identity Platform policy, since the policy page shows none), or the product must offer password-less sign-in as the default. [P-01, P-02 6.2.12, P-05, P-19]
- **UDR-04** Email-enumeration protection must be enabled and a test must show that sign-in, reset and sign-up responses are the same for existing and unknown emails. [P-21, P-05, P-02 6.3.8]
- **UDR-05** Optional TOTP MFA must be available to every user, mandatory for owner/admin accounts, and must require email verification before enrolment and at least one recovery path (two factors or recovery codes). [P-20, P-09, P-01]
- **UDR-06** Provider linking must follow "link accounts that use the same email" only after the user re-authenticates with the existing provider, and authorisation decisions must treat `email_verified = false` as an unverified identity. [P-23, P-22]
- **UDR-07** Email change, MFA change, account deletion and provider link/unlink must require a sign-in no older than 5 minutes (design; Firebase uses 5 min for session cookies) and send a notice to the previous email address. [P-28, P-25, P-02 7.5.1, P-09]

### Sessions
- **UDR-08** The API must verify every Firebase ID token's signature, `aud`, `iss`, `exp`, `iat`, `sub` and an explicit sign-in-provider allow-list on each request. [P-26, P-02 9.1.1-9.2.3]
- **UDR-09** State-changing and account-level endpoints must verify tokens with revocation checking enabled (`checkRevoked`), accepting the extra round trip. [P-24]
- **UDR-10** Absolute session lifetime must not exceed 30 days (design; NIST AAL1 SHOULD) and any server session cookie must be `httpOnly`, `secure`, `SameSite`, named `__session` behind Firebase Hosting, with a lifetime within 5 minutes to 14 days. [P-01, P-25, P-07]
- **UDR-11** The app must call `revokeRefreshTokens` on password reset, account disable, suspected compromise and a user-initiated "sign out everywhere". [P-24, P-08, P-02 7.4.2]
- **UDR-12** An ADR must record the client token-storage choice (SDK default `local` persistence vs server session cookie) and the XSS mitigations for the choice, because OWASP advises against tokens in web storage. [P-31, P-07, P-04 14.3.3]

### Account recovery
- **UDR-13** Password-reset, email-link and verification flows must return the same message and similar timing whether or not the account exists. [P-08, P-21]
- **UDR-14** Recovery and email-link tokens must be single-use, HTTPS-only, rate-limited, must not auto-login after a password reset, and a reset must invalidate existing sessions. [P-08, P-27, P-24]
- **UDR-15** Security questions must not be used and recovery must not bypass an enrolled MFA factor. [P-09, P-02 6.4.3]

### Phone/SMS
- **UDR-16** The SMS region policy must be an allowlist containing only countries that Courtside intends to serve (initially US), with a test that a non-listed country code is rejected; Firebase test phone numbers (maximum 10) must exist only in the dev project. [P-17, P-12]
- **UDR-17** reCAPTCHA SMS defense must be on (AUDIT first, then ENFORCE with a starting threshold of about 0.8) before phone sign-in is enabled in prod. [P-18]
- **UDR-18** Phone sign-in must never be the only recovery factor and the user must be offered a non-SMS alternative (email link, passkey/TOTP); changing a registered phone number must require recent sign-in and notify the account email. [P-01, P-12, P-09]
- **UDR-19** SMS spend must have a billing budget alert and API-level caps per number and per IP stricter than the platform caps (platform: 50/min and 500/h per IP; MFA codes 10/h per number); numeric values are a design choice. [P-14, P-13, P-18]
- **UDR-20** Phone numbers must be stored in E.164 only if needed (otherwise only the Firebase UID), displayed masked (last 2-4 digits), looked up by keyed hash (HMAC with a pepper from Secret Manager), and never returned to other users or written to logs. [P-04 14.2.6, P-11, P-06, P-41]

### Data minimisation and retention
- **UDR-21** A data inventory must list every stored personal field with purpose, lawful basis (contract, consent or legitimate interest), and retention; a field without an entry must not be collected. [P-34 Arts 5-6, P-04 14.1.1]
- **UDR-22** Sign-up must include a neutral age screen that blocks under-13 users without storing the date of birth beyond what is needed, and the Terms must state the minimum age; the EU age (13-16 by member state, default 16) is an owner/lawyer decision. [P-38, P-34 Art 8]
- **UDR-23** Ephemeral data (simulation runs, invites, rate-limit counters, abandoned drafts) must carry a Firestore TTL field, and the deletion job must cope with up to 24 h delay and with undeleted subcollections. [P-43, P-04 14.2.7]
- **UDR-24** The product must set no non-essential cookies or third-party trackers; any analytics must be cookieless or gated on consent. [P-35]
- **UDR-25** Optional processing (marketing email, analytics) must use opt-in consent, record the consent time and version, and be withdrawable in one step. [P-34 Art 7]

### Storage and encryption
- **UDR-26** Firestore client rules must be deny-all, user data must be reached only through the API, and a CI test must fail if a permissive rule (`if true`) appears. [P-42]
- **UDR-27** Secrets (service keys, pepper, OAuth client secrets) must live only in Secret Manager with version history, and the repo must contain none. [P-41]
- **UDR-28** Buckets that hold user data must have uniform bucket-level access and public access prevention, and avatars must be served only through a controlled path. [P-47, P-10]

### Logging
- **UDR-29** Logs must record authentication success/failure and authorisation failures keyed by UID only, and never contain passwords, tokens, OTP codes, full emails or full phone numbers (mask or hash), with user-supplied fields sanitised against CR/LF injection and timestamps in UTC. [P-04 16.2.5, 16.3.1, 16.4.1, 16.2.2, P-11, P-09]

### User rights (export/delete)
- **UDR-30** An in-app "Delete my account" must remove the Auth user, user-owned Firestore documents (including subcollections), the avatar object and provider links, and complete within one month of the request. [P-33 5.1.1(v), P-34 Art 12(3), P-43]
- **UDR-31** A test must create a user across all collections, delete the account, and assert zero remaining documents, objects, and log-visible identifiers (backups excepted). [P-43, P-44]
- **UDR-32** The privacy policy must state that deleted data can persist in backups for up to 14 weeks (Firestore maximum retention; shorten the configured retention if possible). [P-44, P-34 Art 5(1)(e)]
- **UDR-33** Users must be able to download a machine-readable export (JSON) of profile, league memberships, picks and settings, and correct their username, avatar and email in-app. [P-34 Arts 15, 16, 20]

### Uploads
- **UDR-34** Avatar uploads must accept only JPEG/PNG/WebP chosen by allow-list, determined by file signature (ignoring the client `Content-Type`), and reject SVG and everything else. [P-10, P-03 5.2.2]
- **UDR-35** Every avatar must be decoded and re-encoded server-side to a fixed maximum size, which strips EXIF/GPS metadata, with a file-size cap (design: 2 MB) and a maximum pixel count. [P-10, P-03 5.2.1, 5.2.6]
- **UDR-36** Stored objects must have server-generated random names, be served from a separate origin/bucket domain with the filename set in `Content-Disposition`, and uploads must require authentication plus a per-user quota. [P-10, P-03 5.3.2, 5.4.1, 5.2.4]

### Third parties
- **UDR-37** A processors register must list each third party (Google/Firebase, any email sender, Apple, SMS carriers via Google) with data shared, region and contract basis (Firebase terms incorporate SCCs and give 30 days' sub-processor notice). [P-46]

### Incident response
- **UDR-38** A written breach runbook must define who decides, a 72-hour clock to notify the relevant supervisory authority where the GDPR applies and risk exists, and user notice without undue delay when risk is high. [P-34 Arts 33-34]
- **UDR-39** The runbook must include a tested kill-switch: revoke all refresh tokens, disable a sign-in provider, rotate the Secret Manager secrets, and a quarterly drill (design). [P-24, P-41]
- **UDR-40** Usernames must be unique case-insensitively, normalised against look-alike characters, with a reserved-name list (admin, support, staff, brand and NBA names) and a report-and-remove flow. (design; no primary source opened.) [P-29 (mechanism: `beforeUserCreated`)]

(40 rules. Dropped as too thin or not independently testable: a "never store passwords" rule (Firebase hosts hashing), an HTTPS-only rule (Google-default TLS and HTTPS email links, P-40, P-27, are inherited), an audit-log retention rule (see open question 9) and a Sign in with Apple rule that applies only once an iOS app exists (P-33).)

---

## (d) Open questions for the owner

1. **Billing / plan.** Does the production Firebase/GCP project already have a billing account (Cloud Run needs one; not verified here)? Phone auth and email-link volume beyond 10 SMS/day and 5 emails/day appear to need one (P-13, P-14), but P-13 shows 3,000 SMS/day for a non-billed project; spike to find out which applies. Is upgrading to Identity Platform acceptable (needed for blocking functions; likely for password policy and MFA)?
2. **SMS budget.** Max monthly SMS spend and the countries to allow (US-only is cheapest, $0.01/SMS vs $0.10 for Germany in P-16)? Is the phone method worth the cost and fraud surface versus email link, Google and Apple?
3. **Blocklist.** Which breached-password check will we use (Identity Platform policy has none that I found)? Or default to Google/Apple/email-link/passkey only?
4. **Token storage.** Accept SDK `local` persistence with strong CSP, or build the `__session` cookie flow? (affects CSRF work.)
5. **Age.** 13+ globally, or 16 in the EU (GDPR default) or block the EU entirely at launch? Needs a lawyer.
6. **Fantasy-sports law.** Free-to-play only? Any prize, paid entry, or "league fee" feature changes the legal picture by state; no sources were researched. Needs a lawyer.
7. **GDPR/UK scope.** Does open global sign-up count as "offering services" to EU users (Art 3(2))? Need a representative or DPO? Lawyer.
8. **Jurisdiction-specific items not researched:** US state breach-notification laws, other state privacy laws, TCPA/CAN-SPAM for SMS/email, UK GDPR, Canadian law.
9. **Retention values.** Concrete retention for audit logs, backups (default 14 weeks max), inactive accounts, and sim history is the owner's call.
10. **Apple.** Sign in with Apple needs a paid Apple Developer Program membership (P-32; fee not verified on a fetched page). Add it now, or only when the iOS app ships? If an iOS app offers Google sign-in it must also offer an equivalent such as Sign in with Apple and in-app account deletion (P-33 4.8, 5.1.1(v)).
11. **Moderation.** Who reviews reports of avatars and usernames? Is automated image moderation in scope (not researched)?

### Suggested spikes
- **SPK-1 (30 min):** In a throwaway Firebase project without billing, send phone codes until blocked; record the daily cap, default SMS-region policy and whether the Identity Platform upgrade is required for the password policy and MFA.
- **SPK-2:** Account-takeover test: create an email+password account for `victim@gmail.com` without verifying, then sign in with Google as the victim; record whether the password method is removed (P-27, P-22 imply yes).
- **SPK-3:** Where the Web SDK keeps tokens (IndexedDB vs localStorage) and what a CSP-hardened SPA must allow.
- **SPK-4:** Measure the latency of `checkRevoked=true` on Cloud Run (UDR-09).
