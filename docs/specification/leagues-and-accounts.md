# Courtside: leagues and accounts specification

Version 0.2 · 2026-10-04 · **PROPOSAL until gates G-34 (D-72) and G-35 (D-74) are answered.** Courtside is the product name (D-73). Written from the owner's request of
2026-10-04: *create your own fantasy league and invite others by URL; commissioners and co-commissioners; private or
public leagues with a leagues panel; league and team names, default team name = user name + a keyword; profile pictures,
username and team picture; a proper sign-up and user settings section.*

Authentication, privacy and data handling follow `docs/standards/user-data-and-auth.md` (rules UDR-xx; research in
`docs/research/user-data-privacy-and-auth.md`). This is the shared design the tasks below implement. The tasks hold the acceptance criteria; this file holds the
vocabulary, permissions, data model, flows and limits they all agree on.

## 1. Scope

**In this slice (L1)**: accounts you can register for; a public profile (username, picture); leagues you create and
configure; teams with names and pictures; invite links; public discovery; commissioner and co-commissioner powers;
the league's settings (the same league shape as the draft settings, DRAFT-017) used by that league's practice drafts and
valuations.

**Not in L1** (named so nobody assumes them): a live multi-user draft room, in-app weekly scoring from real NBA games,
lineups/waivers/trades between members, chat, email or push notifications to members. Each is a separate later slice
(`LEAGUE-LIVE`, `LEAGUE-SEASON`; owner decision, D-72 Q4). A league in L1 is a **group with a rule set**; it does not
run a season. A league row carries `source: native` so a later link to a Yahoo league (DATA-032) is an addition, not a
rewrite.

**Order of work**: nothing here starts before the owner's real draft (Sun 18 Oct 2026). Build order after the draft
tasks, in dependency order:
1. Spikes and records: RSCH-010 (identity platform facts), SEC-003 (data inventory, threat model, breach runbook), BRAND-001, BRAND-003, HYG-001, HYG-002.
2. Foundations and identity: APP-026 (registry) → APP-020 (events) → APP-024 (rate limiter) → INFRA-009 and INFRA-010 → APP-018 → APP-027 (step-up, MFA, revocation) → APP-012 → APP-013 → APP-021.
3. Leagues: APP-014 → APP-015 → APP-022 → APP-023 → APP-016 → APP-017.
4. Data rights: APP-019 → APP-025.
5. Screens: WEB-030 → WEB-031 → WEB-037 → WEB-032 → WEB-033 → WEB-034 → WEB-035 → WEB-036 → WEB-038.
6. SEC-002 (review and abuse drill) must pass before the `OPEN_SIGNUP` flag (default off) is turned on. BRAND-002 (repository
   rename) is an owner action.

Ownership, so nothing is built twice: APP-012 owns the username rules, the one `is_blocked` text blocklist and the
team-name generator with its word list (APP-014 and APP-015 call it; APP-015 serves `GET /team-names/suggest`); APP-024
owns the one rate limiter, its table and the 16 KB body cap (every other task only adds rows); APP-026 owns the
`USER_DATA_OWNERS` registry and its coverage test (every task that stores personal data registers its own entry);
APP-019 owns the export, APP-025 owns deletion and retention jobs, both built from the registry; APP-020 owns security
events and log redaction; APP-027 owns step-up, MFA level and session revocation; INFRA-009 owns identity configuration
and INFRA-010 owns buckets, secrets, TTL and indexes. HYG-001 fails CI on a task with no files, a file with no task and an
unlinked doc; HYG-002 on dead code and duplicates.

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **Account** | A sign-in identity (Firebase uid). Has a platform role: `owner` (the project owner) or `member` (everyone else). |
| **Profile** | What others may see about an account: **username**, **avatar**. Nothing else. The real name and the email are never shown to other users. |
| **League** | A named group with settings, a visibility and 2..30 team slots. |
| **Team** | One slot in a league. Belongs to one account, has a name and a picture. A team is created when a person joins. |
| **League role** | `commissioner` (the creator; exactly one), `co_commissioner` (0..3), `manager` (everyone else). |
| **Visibility** | `private` (not listed; join only through an invite link) or `public` (listed in the Leagues panel). |
| **Join mode** (public only) | `open` (one click until full) or `approval` (a request a commissioner accepts). |
| **Invite link** | `https://<site>/join#<token>`: an unguessable bearer token in the URL fragment (never sent to a server by the browser) that lets its holder join that league. |

Platform roles and league roles are separate. Being `member` on the platform says nothing about any league; being
commissioner of one league gives no rights in another. The platform `owner` can hide or delete any league and remove
any picture (moderation), and still sees the live Yahoo data that no other account sees (D-64, privacy rule).

## 3. Permissions

`✓` allowed, `—` not allowed. "Own" = the actor's own team.

| Action | Commissioner | Co-commissioner | Manager | Signed-in non-member |
|---|---|---|---|---|
| See a public league's overview, teams, settings | ✓ | ✓ | ✓ | ✓ (public only) |
| See a private league | ✓ | ✓ | ✓ | — (only the invite preview) |
| Edit name, description, visibility, join mode, settings | ✓ | ✓ | — | — |
| Create and revoke invite links | ✓ | ✓ | — | — |
| Accept or decline join requests | ✓ | ✓ | — | — |
| Remove or block a manager | ✓ | ✓ | — | — |
| Remove or block a co-commissioner | ✓ | — | — | — |
| Appoint or demote co-commissioners | ✓ | — | — | — |
| Transfer the commissioner role | ✓ (to a co-commissioner) | — | — | — |
| Delete the league | ✓ | — | — | — |
| Reset another team's name or picture to the default | ✓ | ✓ | — | — |
| Rename own team, change own picture | ✓ | ✓ | ✓ | — |
| Leave the league | after transferring (or delete) | ✓ | ✓ | — |
| Join | n/a | n/a | n/a | public+open, public+approval (request), or any league with a valid link |

Co-commissioners can change settings, as the owner asked ("commissioners have access to change league settings"). Only
the commissioner can appoint, transfer and delete, so power cannot be taken from them. The owner may change this table
at G-34.

**One enforcement point**: a single function `can(actor, action, league, target)` in the league service reads this table
(it is the table, as data). No route checks roles by itself. A test walks the whole table against every endpoint.

## 4. Data model (Firestore, written only by the API, client rules deny all - D-64)

```
users/{uid}                      (exists: APP-008) + username, usernameLower, avatar{id,url}, usernameChangedAt, termsVersion, privacyVersion, acceptedAt
usernames/{usernameLower}        {uid, reservedUntil?}   -- uniqueness by a transaction that creates this doc
leagues/{leagueId}               {name, nameLower, description, visibility, joinMode, status: setup|archived,
                                  source: "native", settings: LeagueShape, season, capacity, memberCount,
                                  commissionerUid, createdAt, updatedAt, rev, hidden?: bool}
leagues/{leagueId}/members/{teamId}   {uid, role, teamId, joinedAt}
leagues/{leagueId}/teams/{teamId}     {name, nameLower, avatar?, ownerUid, updatedAt, rev}
invites/{tokenHash}              {leagueId, createdBy, createdAt, expiresAt, maxUses|null, uses, revokedAt|null, label}
                                 -- top level so a token is looked up by one read; league delete removes them by leagueId
leagues/{leagueId}/requests/{uid}     {at, teamName, message}
leagues/{leagueId}/blocked/{uid}      {at, by}
leagues/{leagueId}/log/{autoId}       {at, actorTeamId, kind, summary}         -- Firestore TTL 180 days
reports/{autoId}                      {at, reporterHash, kind: league|avatar|team|username, targetId, reason, status}
                                      -- reporterHash = HMAC with the reporter-hash secret; TTL 180 days
```
- `teamId` is a random 12-character id. **Every API response and URL addresses people by `teamId` or `username`, never by
  uid or email.** Another user's uid is not returned anywhere.
- `LeagueShape` is the `league` object of APP-011's `Preset` (scoring, drafting, teams, budget, spots, categories,
  weights), validated by the same code. `capacity` equals `settings.teams`.
- `memberCount` changes only in the same transaction as the member document.
- "My leagues" = collection-group query on `members` where `uid == me` (index in `firestore.indexes.json`).
- Discovery = `visibility == public, hidden == false, status == setup`, ordered by `createdAt` desc, cursor-paged; name
  search is a prefix range on `nameLower`.
- Invite tokens: 16 random bytes, base64url (22 characters), shown once; only the SHA-256 is stored.

## 5. Naming and pictures

| Thing | Rules |
|---|---|
| Username | 3-20 characters `A-Za-z0-9_`; unique case-insensitively; a reserved list (`admin`, `owner`, `support`, `commissioner`, `nba`, `yahoo`, `system`, `moderator`, ...) and a blocklist (offensive terms; a file in the repo) are refused. Changeable once every 30 days; the old name stays reserved to the same account for 30 days. Suggested at sign-up from the Google given name or the email prefix. |
| League name | 3-40 characters, no control characters or angle brackets, blocklist applies, unique case-insensitively **among public leagues** (private leagues may repeat). Description 0-280. |
| Team name | 2-30 characters, same character rules, unique case-insensitively **within the league**. |
| Default team name | `<username> <Keyword>`: the keyword is chosen deterministically from the list below by a hash of (account, league) so a refresh shows the same suggestion; a "shuffle" button steps to the next; a clash inside the league steps on; after the list, a roman numeral is appended. Longest result is 20 + 1 + 9 = 30 characters. |
| Keywords | Ballers, Hoopers, Dunkers, Shooters, Hustlers, Slashers, Snipers, Crushers, Ringers, Bombers, Buckets, Legends, Dynasty, Titans, Flyers, Rollers, Rebels, Wolfpack, Squad, Crew (no NBA team names). |
| Pictures | An upload of JPEG, PNG or WebP up to 2 MB and 4096 px a side, no animation; the server decodes it, centre-crops to a square, re-encodes to 256 px WebP, discards all metadata, and stores it under a random id. Without a picture: an initials avatar in a colour derived from the username, or one of 12 preset icons. Two reports from verified accounts at least 7 days old hide a picture (object moved to quarantine) pending review; a `severe` report hides at once. |

## 6. Flows

**Sign up** (WEB-030 on APP-012): choose Google, email and password, or email link (phone is built behind the `AUTH_METHODS` flag and off at launch, D-74) →
verification code or link where the method needs it (the app is unusable until the contact is verified, UDR-01) → onboarding: pick a username (live availability), optional picture, accept terms and
privacy notice (age 16+) → land on Leagues. An account that has signed in but not onboarded can call only `/me`,
`/me/onboarding`, `/usernames/{name}/available` and the public landing data.

**Create a league** (WEB-033): name, visibility (default private), join mode if public, the league settings (the DRAFT-017
form with a "same as my default preset" shortcut), season; then your team (default name, picture). You are the commissioner.
The last step shows the invite link with Copy and, on phones, the Share sheet.

**Join by link** (WEB-035): `/join#<token>` shows the league name, the commissioner's username, the filled/total slots and
the settings summary, **to anyone, signed in or not**. "Join" asks for sign-in/sign-up if needed, remembers the link
through the sign-up, then a one-step form: team name (default filled), optional picture → joined. Bad cases have their own
messages: expired, revoked, full, already a member (goes to the league), blocked, league deleted/hidden.

**Discover** (WEB-032): Leagues → Discover lists public leagues (name, commissioner, `filled/capacity`, format chips,
created), search by name, filters for format and "has open spots". Open → the read-only overview with Join or Request.

**Request to join** (approval mode): the requester sends a team name and a message (≤ 140); a commissioner or
co-commissioner accepts (the team is created) or declines (the requester may ask again after 24 h); pending requests
are capped at 50 per league and one per person.

**Manage** (WEB-034): commissioners get Settings, Members (roles, remove/block, reset a team), Invites and an Activity log
(who changed what). Settings use the ETag/If-Match pattern, so two commissioners cannot silently overwrite one another.
Lowering capacity below the member count, or changing the format to one the server doesn't support yet, is refused with a
clear message. Members see a "settings changed" entry in Activity.

**Leave, remove, transfer, delete**: a manager leaves; the team is deleted. A commissioner with other members must
transfer first (to a co-commissioner) or delete the league. Deleting needs the league name typed; it removes the league
and everything under it in the API's batched writes. A removed member is blocked from re-joining until unblocked.

**Delete my account** (extends D-64): memberships end (teams deleted); leagues where you are commissioner with other
members block the deletion with `409 transfer-or-delete-leagues`; leagues where you are alone are deleted; the username is
released after 30 days; the avatar is deleted; the export includes your leagues and teams.

## 7. API surface (all under the existing bearer-token auth; names are final in APP-012..025)

| Endpoint | Who |
|---|---|
| `GET /usernames/{name}/available`, `POST /me/onboarding`, `PATCH /me/profile`, `PUT /me/avatar`, `DELETE /me/avatar` | the account |
| `POST /leagues`, `GET /leagues/mine`, `GET /leagues/public?q=&cursor=` | any onboarded account |
| `GET /leagues/{id}`, `PATCH /leagues/{id}` (If-Match), `DELETE /leagues/{id}` | members (read) / commissioners (edit) / commissioner (delete) |
| `POST /leagues/{id}/invites`, `GET /leagues/{id}/invites`, `DELETE /leagues/{id}/invites/{inviteId}` | commissioners |
| `POST /invites/preview {token}` (no auth), `POST /invites/accept {token, teamName?}` | anyone / onboarded account |
| `POST /leagues/{id}/join` (public+open), `POST /leagues/{id}/requests`, `POST .../requests/{teamId}:accept|:decline` | account / account / commissioners |
| `PATCH /leagues/{id}` with `{status: archived|setup}`; `PATCH /leagues/{id}/teams/{teamId}`, `PUT/DELETE .../teams/{teamId}/avatar`, `POST .../teams/{teamId}:reset` | the team's owner / commissioners |
| `PUT /leagues/{id}/members/{teamId}/role`, `POST .../members/{teamId}:remove|:block|:unblock`, `POST /leagues/{id}:transfer` | per the table |
| `POST /reports` | any onboarded account |
| `GET /leagues/{id}/log` | commissioners |
| `GET /team-names/suggest` | any onboarded account |
| `GET /auth/config`, `POST /me/sessions:revoke`, `POST /me/export`, `POST /me/consent`, `DELETE /me`, `GET /admin/reports`, `POST /admin/users/{id}:purge` | public / account / account / account / account / owner / owner (MFA) |

Every league response carries `viewer.permissions` (the result of `can()` for that viewer) so the web app never recomputes roles.

Errors use the existing problem format; the permission failures are `403 forbidden-role` (never reveal that a private
league exists: a non-member asking for a private league gets `404`).

## 8. Limits and abuse controls

| Control | Value |
|---|---|
| Leagues created per account | 5 active, 3 per day (the platform owner: 20) |
| Memberships per account | 20 |
| Active invite links per league | 10; lifetime 1 day, 7 days (default) or 30 days; max uses 1..30 or unlimited |
| Co-commissioners per league | 3 |
| Join/request attempts | 30 per hour per account; 10 bad tokens per hour per account |
| Avatar uploads | 10 per day per account |
| Reports | 10 per day per account |
| Request bodies | 16 KB JSON; 2 MB image |
| New accounts | Firebase Auth rate limits; the API creates a profile only after onboarding; SEC-002 decides whether App Check is needed before the flag is on |

## 9. Privacy and security rules (checked by SEC-002)

The numbered rules are in `docs/standards/user-data-and-auth.md`; this list is what the leagues feature adds.

- Strangers see only: username, avatar, team name, team avatar, league role, league name/description/settings. Never email,
  real name, uid, time zone or notification settings.
- Private leagues are invisible to non-members, including in search and counts; the invite preview shows only name,
  commissioner username, slots and a settings summary.
- Every object is authorised on the server from the verified token. No endpoint takes a uid. Object ids are random.
- User-entered text is stored as plain text and rendered as text; the API escapes nothing and the web never uses
  `dangerouslySetInnerHTML`.
- Invite tokens: stored hashed, compared in constant time, never logged (the fragment never reaches a server; the token travels only in POST bodies, which are never logged).
- The live Yahoo data and the owner's private pipeline outputs stay `owner`-only. Self-registered `member` accounts see demo
  data and the league features only (D-64).
- Pictures are server-produced WebP files in one public-read bucket, served from `storage.googleapis.com` (a separate
  origin, so an upload can never run as script on the app's origin; INFRA-010 checks the headers). The quarantine and exports
  buckets stay private.

## 10. Performance and cost

League page = 1 league document + at most 30 team documents (31 reads). Discovery = 20 reads per page, cached 30 s in
process. Targets are D-71's (p95 ≤ 300 ms published reads, ≤ 500 ms `/me/*`), and PERF-001 adds the league endpoints to
the load script. Firestore's free tier is 50 000 reads a day: about 1 500 league-page views a day, enough for the 25
concurrent users D-71 targets. Image storage is cents per month and there is no load balancer. Firebase Auth email/password is free to 50 000 monthly
active users. **No new monthly cost is expected**; the first billing step stays the one already planned before 25 Dec.

## 11. Traceability

| Owner's request | Where |
|---|---|
| Create a league, name it, invite by URL | APP-014, APP-015, WEB-033, WEB-035 |
| Commissioner by default; co-commissioners; commissioners change settings | APP-016, §3, WEB-034 |
| Private or public; a leagues panel to view and join public leagues | APP-014 (discovery), APP-015, WEB-032 |
| Name leagues and teams; default team name = user name + keyword | §5, APP-015, WEB-033, WEB-035 |
| Profile pictures, username, team picture | APP-012, APP-013, WEB-031, WEB-034 |
| Proper registration, sign-up, user settings | APP-012, WEB-030, WEB-031 (extends WEB-014) |
| Safety of strangers using it | APP-017, APP-022, SEC-002 |
| Rename to Courtside; no stale references | D-73, BRAND-001, BRAND-003, BRAND-002 |
| Sign up with Google, email, phone, with verification codes | D-74, INFRA-009, APP-018, APP-021, WEB-030, WEB-037 |
| Do not duplicate or orphan anything; keep using the harness | HYG-001, HYG-002, APP-026, APP-024, §1 ownership text |
| Best-practice privacy and a ruleset for auth and data | `docs/standards/user-data-and-auth.md`, SEC-003, SEC-002, APP-019, APP-020, APP-024, APP-025, APP-026, APP-027, INFRA-010, WEB-036 |
| No duplicated or orphaned code | HYG-001, the ownership list in §1, `USER_DATA_OWNERS` |
