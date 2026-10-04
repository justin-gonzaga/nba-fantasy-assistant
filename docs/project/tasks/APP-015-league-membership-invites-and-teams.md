---
id: APP-015
title: "Invite links, link preview, join by link and default team names"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-014, APP-012, APP-024, APP-026]
areas: [apps/api/src/fantasy_api/leagues/invites*.py, apps/api/src/fantasy_api/leagues/join*.py, apps/api/tests/test_invites*.py, apps/api/tests/test_join*.py, apps/api/tests/test_team_suggest.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-015 — Invite links and joining by link

## Objective
People get into a league by a link the commissioner shares. This task adds invite links (unguessable, hashed,
expiring, revocable), the unauthenticated preview, joining by link (which creates the member and a team with a good
default name from APP-012's generator), and the `GET /team-names/suggest` endpoint over that generator.

**Token handling (settles a review finding).** The link is `https://<site>/join#<token>`: the token is in the URL
**fragment**, which browsers never send to servers or in `Referer`, so it cannot reach an access log. The web page reads
it, removes it from the address bar and sends it in a **POST body** to `POST /invites/preview` and
`POST /invites/accept`. Invites are stored in a top-level collection `invites/{tokenHash}` that carries `leagueId`, so a
token resolves to its league by one document read with no league id in the request. Requests, public joining, renaming, pictures,
leaving and blocking are APP-023. Spec: `docs/specification/leagues-and-accounts.md` §3, §5, §6, §8, §9.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5, §6, §8, §9
- APP-014's league service and `can()`; APP-012's `is_blocked`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Commissioner | "I send a link to my friends" | create a link with a lifetime (1/7/30 days) and optional max uses; the full URL is returned **once**; max 10 active links; revoke any time; deleting the league deletes its invites (query on `leagueId`) |
| Friend opens the link, not signed in | "I see what I am joining before I sign up" | `POST /invites/preview {token}` (no auth) returns league name, commissioner username, filled/total and a settings summary; nothing else; unknown, expired, revoked and used-up tokens return the same 404 shape and are limited by a row in APP-024's table |
| Friend joins | "my team has a good default name" | `POST /invites/accept {token, teamName?}`; the default comes from APP-012's `default_name` with the league's taken names; unique in the league; full league 409 `league-full`; the slot count is checked in the same transaction |
| Two people take the last slot | "only one gets it" | transaction on `memberCount`; the loser gets `league-full`, not a half-created team |
| Already a member / blocked | clear messages | already a member returns 200 with the league id; blocked returns 403 `blocked` (no hint who blocked) |
| Not onboarded | gate | joining needs an onboarded account (APP-021); the preview does not |
| Token leakage | defence | token stored as SHA-256, compared in constant time, never in a URL path or query (fragment and POST body only), request bodies never logged; a link at max uses stops working |

## Acceptance criteria
- [ ] AC1: invite links: 128-bit token, SHA-256 stored, returned once, lifetime and max uses enforced, at most 10
      active, revocable; the list shows label, created, expires and uses (never the token).
      Verify: `uv run pytest -q apps/api/tests/test_invites.py`
- [ ] AC2: `POST /invites/preview` works unauthenticated, returns only the preview fields, and returns an identical
      404 for unknown, expired, revoked and used-up tokens; the 10-bad-tokens-an-hour limit per IP and per account is a
      row in APP-024's table.
      Verify: `uv run pytest -q apps/api/tests/test_invites.py -k "preview or same_404 or limit_row"`
- [ ] AC3: `POST /invites/accept` creates the member and team in one transaction that increments `memberCount`; 30
      concurrent joins on a 10-slot league create exactly 10 teams; 30 joins an hour per account is an APP-024 row.
      Verify: `uv run pytest -q apps/api/tests/test_join.py -k "join or concurrent"` and the CI emulator job
- [ ] AC4: `GET /team-names/suggest?league=<id|new>&shuffle=<n>` calls APP-012's `default_name` with the league's taken
      names (`new` means none) and holds no word list of its own; a member of a private league only gets suggestions for
      leagues they belong to.
      Verify: `uv run pytest -q apps/api/tests/test_team_suggest.py`; `grep -rln "Ballers" apps packages` lists only
      `textrules/team_names.py`
- [ ] AC5: names pass APP-012's `is_blocked` (reused, not copied); logs and the activity log never contain a token,
      email or uid; invite documents are registered in `USER_DATA_OWNERS` (APP-026) and a token never appears in a
      URL (an OpenAPI walk asserts no `{token}` path parameter).
      Verify: `uv run pytest -q apps/api/tests/test_invites.py -k "redact or no_pii or blocklist or registry or no_token_in_url"`
- [ ] AC6: every new route declares its `can()` action (the OpenAPI walk from APP-014 stays green) and the client is
      regenerated with no diff.
      Verify: `uv run pytest -q apps/api/tests/test_league_permissions.py`; `just api-client` twice, no diff

## Test requirements
Store contract tests on both backends; property tests for names; concurrency tests on the emulator; negative
authorisation tests per route (wrong role, wrong league, blocked, signed out).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified; requests, public joining, team rename/picture, leave/remove/block split to APP-023.

## Decisions
- Anyone with a valid link may preview but only an onboarded account may join: the preview reveals the minimum the link
  holder needs to decide.

## Known issues
_None._

## Follow-ups
- Email or SMS delivery of invites needs a processor decision (SEC-003); the link is shared by the commissioner for now.
- The fragment-based link depends on the web app reading `location.hash` before any third-party script runs (WEB-035).
