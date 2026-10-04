---
id: APP-012
title: "Usernames, the shared text blocklist and the team-name generator"
epic: EP-75 Accounts and leagues
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-34
depends_on: [APP-008, APP-009, APP-024, APP-026]
areas: [apps/api/src/fantasy_api/usernames/**, apps/api/src/fantasy_api/textrules/**, apps/api/tests/test_usernames.py, apps/api/tests/test_blocklist.py, apps/api/tests/test_team_names.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-012 — Usernames and the text blocklist

## Objective
Every account gets a unique public username (the only name other users see). This task adds the username rules, an
atomic claim so two people cannot get the same name, the 30-day change rule, and **the one text blocklist
normaliser** that league names (APP-014) and team names (APP-023) also use, and **the one team-name generator** (pure
function and word list, `textrules/team_names.py`) that APP-014 calls for the commissioner's team and APP-015 exposes as
`GET /team-names/suggest`. Onboarding itself, the sign-up flag and
the onboarding gate are APP-021.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5
- `docs/standards/user-data-and-auth.md` (usernames, impersonation)
- `apps/api/src/fantasy_api/users/*` (store, ETag pattern)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Two people want the same name | "first one wins, fairly" | claim is one transaction on `usernames/{lower}`; the loser gets 409 `username-taken` with up to 3 free suggestions; case-insensitive (`LeBron` vs `lebron`) |
| Bad or rude name | "refused with a reason" | length 3-20, charset `A-Za-z0-9_`, reserved words (`admin`, `owner`, `support`, `commissioner`, `nba`, `yahoo`, `system`, `courtside`...), blocklist, lookalikes (the charset excludes Unicode; `l`/`I`/`1` lookalike rule for reserved names), each a distinct problem field |
| Probing for names | "cannot enumerate cheaply" | availability check is rate-limited (30/min/account) and needs a verified identity; no unauthenticated lookup |
| Name change | "I changed my mind" | once per 30 days (429 `username-cooldown` with the date); old name reserved to the account for 30 days; If-Match |
| Innocent word flagged | "Scunthorpe" | an allow-list of innocent words beats the blocklist; one test file documents each entry |
| Leetspeak, spacing, punctuation | blocked | `b.a.d`, `B4D`, `b_a_d` normalise to the same term |
| Existing owner / invited member | unchanged | backfilled with a suggested username on first call (`PATCH` allowed once without cooldown) |
| Release | fair | a deleted account's name is released after 30 days (APP-025) |
| Default team name | "my team has a good name" | `default_name(username, taken, shuffle)` is deterministic for (username, shuffle), steps through 20 keywords, steps on a collision with `taken`, adds a roman numeral after the list, and never exceeds 30 characters for a 20-character username |
| Name reports | "report a rude username" | a reported username can be reset by the owner (APP-017 `username` report kind); the account gets a generated name and is told |

## Acceptance criteria
- [ ] AC1: username rules are table-tested (length, charset, reserved, blocklist, case-insensitive uniqueness,
      suggestions).
      Verify: `uv run pytest -q apps/api/tests/test_usernames.py -k "rules or suggestions"`
- [ ] AC2: claiming is atomic under 20 concurrent claims on the in-memory and Firestore stores (exactly one wins).
      Verify: `uv run pytest -q apps/api/tests/test_usernames.py -k "concurrent"` and the emulator job in CI
- [ ] AC3: `PATCH /me/profile` changes the username under the 30-day cooldown and reservation rule, with If-Match.
      Verify: `uv run pytest -q apps/api/tests/test_usernames.py -k "change or cooldown or reserved"`
- [ ] AC4: `GET /usernames/{name}/available` needs a verified identity, is limited by its row in APP-024's table
      (30/min/account; this task adds the row and no limiter), and never returns the owner of a name.
      Verify: `uv run pytest -q apps/api/tests/test_usernames.py -k "available or ratelimit"`
- [ ] AC5: the blocklist normaliser blocks case, spacing, punctuation and leetspeak variants and not the allow-listed
      words; `is_blocked()` is the only implementation.
      Verify: `uv run pytest -q apps/api/tests/test_blocklist.py`; `grep -rn "def is_blocked" apps packages` finds one
- [ ] AC6: privacy: responses never include email or uid next to a username; logs contain no username in clear
      (APP-020 filter).
      Verify: `uv run pytest -q apps/api/tests/test_usernames.py -k "privacy"`
- [ ] AC7: the team-name generator is the only place the word list lives; names are deterministic, step on shuffle and
      collision, and stay within 30 characters (property tests).
      Verify: `uv run pytest -q apps/api/tests/test_team_names.py`; `grep -rln "Ballers" apps packages` lists only
      `textrules/team_names.py`
- [ ] AC8: the `usernames` and `users` profile fields are registered in `USER_DATA_OWNERS` (APP-026) with export and
      release-after-30-days behaviour.
      Verify: `uv run pytest -q apps/api/tests/test_lifecycle_registry.py -k "usernames"`
- [ ] AC9: OpenAPI and the TypeScript client are regenerated with no diff on a second run.
      Verify: `just api-client` twice, `git diff --exit-code`

## Test requirements
Contract tests shared by both stores; property test for the normaliser (idempotent, case-insensitive). No network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- Username claims use a separate `usernames/{lower}` document so uniqueness is a transaction, not a query.
- The blocklist lives here once; later tasks import it.

## Known issues
_None._

## Follow-ups
- APP-021 (onboarding), APP-025 (release on deletion).
