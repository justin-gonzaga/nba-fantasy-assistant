---
id: APP-014
title: "Leagues: create, read, update, delete, and the permission function"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-021, APP-012, APP-011, APP-026, APP-027]
areas: [apps/api/src/fantasy_api/leagues/**, apps/api/tests/test_leagues.py, apps/api/tests/test_league_permissions.py, packages/core/**]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-014 — Leagues core

## Objective
A league is a named group with settings and a visibility. This task adds the league resource, its settings (the same
`LeagueShape` as the draft presets, validated by the same code as APP-011), the commissioner's first team, optimistic
concurrency, the activity log, and the permission function `can()` for read/update/delete (APP-016 completes the
matrix). Listing public leagues and the creation limits are APP-022. Spec:
`docs/specification/leagues-and-accounts.md` §3, §4, §7.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §2-§4, §7
- `apps/api/src/fantasy_api/users/*` (store/ETag pattern) and the APP-011 draft-settings validation module

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member creating a league | "I name it and choose rules" | name 3-40 (blocklist from APP-012, no `<>` or control chars); capacity 2..30 equals `settings.teams`; unsupported format → 422 `unsupported-format`; the creator's team (default name from APP-012's `default_name`, or the name given) is created in the same transaction and they are `commissioner`; a repeated `Idempotency-Key` returns the same league instead of a second one |
| Non-member asks for a private league | "it should not exist for me" | 404 with the same body as a missing id; never 403 |
| Member of a league | "what can I do here?" | every league response carries `viewer: {role, permissions[]}` from `can()` |
| Two commissioners edit | "no silent overwrite" | `PATCH` needs `If-Match` (rev); stale → 412 with the current document; none → 428 |
| Shrinking capacity | "can't kick people by accident" | capacity below `memberCount` → 422 `capacity-below-members`; format change allowed only while status is `setup` |
| Public name clash | fair names | case-insensitive uniqueness among public leagues via a name-claim document; changing to public re-checks it (409 `league-name-taken`) |
| Delete | "typed confirmation" | `DELETE` needs the exact name in the body; removes the league and every sub-collection in batches; idempotent |
| Description / hostile text | safe | ≤ 280 chars, plain text; HTML is stored as text and never interpreted |
| Hidden by the owner | moderation | a hidden league 404s for non-members and shows a banner to its commissioner |
| Finished or paused league | "put it away" | `PATCH {status: archived}` and back to `setup`; an archived league is read-only (other changes 409 `league-archived`), leaves discovery and does not count toward the creation limit |
| Commissioner reading history | "what changed?" | `GET /leagues/{id}/log` returns the activity log to commissioners, newest first, paged |

## Acceptance criteria
- [ ] AC1: `POST /leagues` creates the league and the commissioner's team atomically (the team name from APP-012's
      generator unless given), is idempotent for a repeated `Idempotency-Key`, and returns the league with `rev` and an
      `ETag`.
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "create"`
- [ ] AC2: `GET /leagues/mine` lists the account's leagues (collection-group index); `GET /leagues/{id}` returns the
      overview to members and to any onboarded account for a public league; a private league returns 404 to
      non-members. Each response carries `viewer: {role, permissions[]}`.
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "mine or read or private_404 or viewer"`
- [ ] AC3: `PATCH` uses If-Match with the 412/428 behaviour, validates settings with the shared `LeagueShape` code
      (one implementation, imported from APP-011) and enforces the capacity and format rules.
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "patch or etag or capacity or format"`;
      `grep -rn "def validate_league_shape" apps packages` finds exactly one definition
- [ ] AC4: `DELETE` requires the typed name, deletes the league, teams (and their avatar objects through the APP-013
      delete function in the registry), members, invites (query on `leagueId`), requests, blocks, the log subcollection
      and the name claim, is idempotent for the commissioner, and is in the step-up table (APP-027).
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "delete"` on both stores
- [ ] AC5: every action goes through `can(actor, action, league, target)`, whose table is data; a test iterates every
      route in the OpenAPI document and fails if a league route does not declare its action.
      Verify: `uv run pytest -q apps/api/tests/test_league_permissions.py`
- [ ] AC6: public name uniqueness holds under 20 concurrent creates/renames (exactly one wins).
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "concurrent"` plus the emulator job in CI
- [ ] AC7: the activity log records create, settings change, visibility change, archive and delete with `actorTeamId`
      only (no uid, email or IP) and a 180-day TTL field, and `GET /leagues/{id}/log` returns it to commissioners only.
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "log"`
- [ ] AC9: `status` moves between `setup` and `archived` by `PATCH`; an archived league rejects other edits and is
      excluded from discovery and the creation count; league documents are registered in `USER_DATA_OWNERS` (APP-026).
      Verify: `uv run pytest -q apps/api/tests/test_leagues.py -k "archive or registry"`
- [ ] AC8: the generated client is refreshed with no diff on a second run.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Store contract tests for both backends; table-driven validation; permission table test; concurrency tests. No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (discovery and limits split out to APP-022 because tasks are S or M).

## Decisions
- A league the caller may not see is `404`, not `403`, so existence is not leaked (OWASP object-level authorisation).
- Name uniqueness among public leagues uses a claim document, the same pattern as usernames.

## Known issues
_None._

## Follow-ups
- APP-022 (discovery, limits).
