---
id: WEB-035
title: "Join by invite link: preview, sign-up detour, team name, joined"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-015, WEB-030]
areas: [apps/web/src/leagues/join/**, apps/web/e2e/league-join*.spec.ts]
standards: [frontend, security, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-035 — The join page (`/join#<token>`)

## Objective
The page a friend lands on from a shared link. It shows the league (name, commissioner, slots, format) to anyone,
signed in or not; "Join" sends them through sign-up/sign-in if needed and brings them back to a one-step form (team
name with a default, optional picture); then they are in. The token is a credential and lives in the URL fragment (`/join#<token>`), which
browsers never send to a server: the page reads it, strips it, and sends it only in the body of
`POST /invites/preview` and `POST /invites/accept` (APP-015).

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §6 (join by link), §9
- `docs/standards/user-data-and-auth.md` (capability URLs, referrer policy)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Friend, not signed in | "what is this?" | preview with league name, commissioner username, `filled/total`, format summary; one primary button "Join this league" |
| Friend without an account | "sign up then land back" | the token survives the sign-up and onboarding (kept in memory/sessionStorage, not the URL query), including the email-verification detour on another device (falls back to "open the link again") |
| Signed-in member | "join" | team name field prefilled (default + Shuffle), optional picture, then success screen with a link to the league |
| Bad links | "tell me why" | expired, revoked, used up, league full, league deleted/hidden, blocked: each its own message and the next step (ask the commissioner); unknown token looks identical to expired |
| Already a member | friendly | goes straight to the league |
| Token hygiene | credential | the route has `Referrer-Policy: no-referrer` (WEB-030 AC8); after first load the fragment is removed (history.replaceState) while the token stays in memory; never sent to analytics or error reports |
| Link opened in an in-app browser | works | no popups needed for sign-in (redirect fallback) |
| Brute force | throttled | 429 handled with a calm message |
| Sign-up closed | explains | shows the invite-only message but still lets already registered users join |

## Acceptance criteria
- [ ] AC1: signed-out visitors see the preview (and nothing else) for a valid link and the correct message for each
      bad state; unknown and expired look the same.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "league-join-preview"`
- [ ] AC2: the sign-up detour returns to the join form with the token intact for Google and for email sign-up.
      Verify: `test:e2e --grep "league-join-signup"`
- [ ] AC3: joining creates the team with the chosen or default name and ends on the league page; double click joins
      once.
      Verify: `test:e2e --grep "league-join-success"`
- [ ] AC4: token hygiene: after load the URL no longer contains the token, requests send it only in a POST body
      (never a URL path or query), and nothing is written to storage except `sessionStorage` for the detour (cleared
      after joining); the `Referrer-Policy` header is asserted in WEB-030 AC8.
      Verify: `test:e2e --grep "league-join-token"` (asserts URL, storage, outgoing requests)
- [ ] AC5: axe clean, 320 px, keyboard-only join path.
      Verify: `test:e2e --grep "a11y|keyboard|phone"` extended

## Test requirements
Playwright with the API stubbed for each token state; component tests for the message mapping.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- The preview endpoint stays unauthenticated by design; its output is limited to what a link holder needs (APP-015).

## Known issues
_None._

## Follow-ups
_None._
