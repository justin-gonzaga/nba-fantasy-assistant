---
id: WEB-034
title: "League page: overview, team grid, my team, settings and activity"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-023, WEB-033, DRAFT-017]
areas: [apps/web/src/leagues/league/**, apps/web/e2e/league-page*.spec.ts]
standards: [frontend, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-034 — The league page

## Objective
The home of a league: overview (name, description, format, occupancy, commissioner), the teams with pictures, my team
(rename, picture, leave), the settings form for those allowed to change it, and the activity list. What a person can
see and do comes from the API's `viewer.permissions`, not from a copy of the matrix in the web app. Members, invites,
requests and the danger zone are WEB-038.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §3, §6
- APP-014 and APP-023 response shapes (the viewer's `permissions` list)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Manager | "see my league and edit my team" | team grid with avatars and names; "You" marker; rename and picture; Leave with confirmation |
| Commissioner | "change settings" | settings form (the shared component from WEB-033); If-Match conflict shows what changed and asks to reload; capacity cannot go below members |
| Co-commissioner | "I can run things but not own it" | commissioner-only actions are not shown (not merely disabled); a direct URL shows a clear "not allowed" page |
| Anyone | "what changed?" | activity list (who, what, when) with team names for commissioners; members see a "settings changed" note |
| Non-member viewing a public league | read-only | overview and teams, Join or Request; no private controls |
| Hidden / archived league | honest | banner for the commissioner; 404 page for others |
| Concurrency | safe | two commissioners editing: the second save gets the conflict flow, never silently overwrites |
| Phone / keyboard / zoom | usable | 320 px, axe clean, destructive actions need a second step |

## Acceptance criteria
- [ ] AC1: overview and team grid render for member, public-visitor and commissioner viewers; unauthorised controls are
      absent, driven by the API `permissions`; there is no role matrix in the web source.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "league-page"`; `grep -rn "co-commissioner" apps/web/src`
      finds only labels
- [ ] AC2: settings save with If-Match, conflict flow tested with two sessions, capacity and format rules shown from
      the API problems.
      Verify: `test:e2e --grep "league-settings"`
- [ ] AC3: my team: rename and picture with the unique-name error shown, and leave with confirmation.
      Verify: `test:e2e --grep "league-team"`
- [ ] AC4: the activity list (read from `GET /leagues/{id}/log`, commissioners only) shows entries with team names,
      never uids or emails.
      Verify: `corepack pnpm@10 --dir apps/web test src/leagues -t "activity"`
- [ ] AC6: "Practice this league" opens the practice draft pre-filled from the league's settings through the shared
      DRAFT-017 settings schema (no second mapping), and an archived league still allows it.
      Verify: `test:e2e --grep "league-practice"`
- [ ] AC5: 320/768/1280 px layouts, axe clean, keyboard-only path (rename a team) works.
      Verify: `test:e2e --grep "a11y|keyboard|phone"` extended

## Test requirements
Fixture leagues for each role; Playwright with the API stubbed; component tests for the permission gating.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified (commissioner tools split to WEB-038).

## Decisions
- The API returns the viewer's permissions per league; the web app never re-implements the matrix (one source of truth).

## Known issues
_None._

## Follow-ups
_None._
