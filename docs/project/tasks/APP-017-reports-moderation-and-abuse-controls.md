---
id: APP-017
title: "Reports, owner moderation and suspension"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-016, APP-020, APP-012, APP-024]
areas: [apps/api/src/fantasy_api/moderation/**, apps/api/tests/test_moderation*.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-017 — Moderation and abuse controls

## Objective
Open sign-up and public leagues invite abuse: offensive names, bad pictures, spam leagues, link guessing, account
farming. This task adds a report endpoint and owner-only moderation actions (hide a league or picture, suspend an
account), all with an audit trail. It reuses the rate-limit mechanism from APP-024 (adding rows to its table) and the
blocklist from APP-012; it adds neither. Limits come from `docs/specification/leagues-and-accounts.md` §8.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §8, §9
- `docs/standards/user-data-and-auth.md` (abuse, logging), APP-020 (security events)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member seeing a rude name or picture | "I report it" | `POST /reports {kind, targetId, reason}`; ≤ 10 a day; one open report per (reporter, target); the target's owner is never told who reported |
| Several reports on a picture | "hide it quickly" | 2 independent reports hide the picture automatically (shown as the default avatar, object moved to quarantine) pending owner review; "independent" means reporters whose accounts are verified and at least 7 days old and who are not the same person's sock puppets (distinct leagues or no shared league); hidden state is reversible; the owner is alerted |
| Rude username | "report a name" | `kind: username`: the owner action `reset` gives the account a generated name and tells them (UDR-40) |
| Child-safety material or threat | "take it down now" | reason `severe` hides immediately, is never viewed by other users, and follows a runbook page (SEC-003) that names the legal reporting duty (US: NCMEC) as a legal item for the owner (G-35); no automated image scanning |
| Owner | "I review the queue" | `GET /admin/reports` (owner only, paginated), actions `hide`, `restore`, `delete`, `suspend` (account), each with a note; every action is a security event |
| Suspended account | "cannot use the product" | token still valid but 403 `suspended` on every route except `/me` and the export; the suspension reason is shown; appeals are an email (documented), not a feature |
| Script hammering the API | "slow down" | one rate-limit dependency: per account and per IP, token bucket per route group; 429 with `Retry-After`; limits in one config table (not scattered constants) |
| Cloud Run scale-out | limits still hold | short windows use a per-instance token bucket (documented tolerance: N instances allow up to N times the rate); the expensive daily limits (creates, uploads, reports) use Firestore counters so they hold across instances |
| Blocklist maintenance | "add a term" | one file in the repo, normalised (case, leetspeak, spaces); tests prove a term blocks `ba.d`, `B4D`; a false-positive allow-list exists (the Scunthorpe problem) |
| Privacy | no doxxing | the report reason is plain text ≤ 200 chars, kept 180 days, visible only to the owner |

## Acceptance criteria
- [ ] AC1: every write route is covered by the APP-024 rate-limit dependency (a route-walk test fails otherwise), and
      this task only adds table rows for reports and moderation; there is no second limiter.
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "ratelimit_rows"`;
      `grep -rln "class .*RateLimit\|def rate_limit" apps` lists only the APP-024 module
- [ ] AC2: the daily report limit (10) survives an instance restart and two concurrent instances, using APP-024's
      shared counters.
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "daily or concurrent"` on the Firestore emulator
- [ ] AC3: report reasons, league names and team names go through APP-012's `is_blocked`; there is one definition.
      Verify: `grep -rn "def is_blocked" apps packages` finds one; `uv run pytest -q apps/api/tests/test_moderation.py -k "blocklist"`
- [ ] AC4: `POST /reports` rules (10/day, one open per target, plain text, auto-hide at 2 independent reporters).
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "report"`
- [ ] AC5: owner-only actions (hide, restore, delete, suspend) work, are refused for every other role, and each writes
      a security event with actor, action, target id and note.
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "owner or suspend or event"`
- [ ] AC6: a suspended account gets 403 `suspended` everywhere except `/me` and export, and its leagues are hidden
      from discovery.
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "suspended"`
- [ ] AC7: reports older than 180 days are deleted by a TTL policy (INFRA-010); the reporter id is stored hashed with
      the reporter-hash secret (INFRA-010), not as a uid; reports are registered in `USER_DATA_OWNERS` (APP-026).
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "ttl or reporter_hash or registry"`
- [ ] AC8: auto-hide needs 2 reports from verified accounts at least 7 days old; two fresh accounts cannot hide a
      picture; `kind: username` reports and the `reset` action work; a `severe` report hides at once.
      Verify: `uv run pytest -q apps/api/tests/test_moderation.py -k "sockpuppet or username or severe"`

## Test requirements
Route-walk tests and emulator tests for the counters. No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- No automated image classification for now: it is a processor (privacy cost) and unnecessary at this scale; reports
  plus owner review. Revisit if abuse is real.

## Known issues
_None._

## Follow-ups
- A moderation screen in the web app (WEB-0xx) if the queue is used more than occasionally.
