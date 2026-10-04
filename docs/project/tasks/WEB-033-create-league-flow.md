---
id: WEB-033
title: "Create a league: name, visibility, settings, your team, invite link"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-015, DRAFT-017, WEB-032]
areas: [apps/web/src/leagues/create/**, apps/web/e2e/league-create*.spec.ts]
standards: [frontend, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-033 — Create a league

## Objective
A short guided flow: name the league, choose private or public (and join mode), set the rules (the same form as the
draft settings page, DRAFT-017, reused not copied), name your team (default `<username> <Keyword>` with a Shuffle
button) and optional picture, then get the invite link with Copy and Share. You become the commissioner.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §5, §6 (create), §8
- the DRAFT-017 league-settings form component and the APP-011 preset schema

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| New commissioner | "I name it and get a link" | steps: Basics → Rules → Your team → Invite; Back keeps data; progress is visible; the league exists only after the final confirm (no half-created leagues from abandoned steps) |
| Choosing visibility | "private by default" | private is preselected; choosing public explains it will be listed and shows join mode (open / approval) |
| Rules | "same as my preset" | a "use my default preset" shortcut; unsupported format combinations are disabled with the reason (server constant), not hidden |
| Names | immediate feedback | league name 3-40; public name clash message after the server check; team name default + Shuffle; blocklist message |
| Limits | clear | 5 active leagues / 3 a day reached → explains and links to Mine |
| Invite step | "share it on my phone" | link shown with Copy; Web Share sheet where available; warns that anyone with the link can join until it expires; default 7 days, max uses option |
| Double tap on Create | idempotent | the request carries an idempotency key; one league is created |
| Network failure at the end | no loss | the form data is kept and Retry works; no duplicate on retry |
| Keyboard / phone | usable | one question per screen on phones; focus moves to the heading on each step |

## Acceptance criteria
- [ ] AC1: the four steps work end to end and end on the invite link; the league is created by one request at the end.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "league-create"`
- [ ] AC2: the rules step renders the shared league-settings component from DRAFT-017 (one implementation); a grep test
      fails if a second league-settings form is added.
      Verify: `corepack pnpm@10 --dir apps/web test src/leagues -t "single settings form"`
- [ ] AC3: default team name and Shuffle use the API suggestion endpoint or the shared generator output, never a
      second client-side word list.
      Verify: `corepack pnpm@10 --dir apps/web test src/leagues -t "team name"`
- [ ] AC4: server problems (name taken, limit, unsupported format) are mapped to sentences and keep the entered data.
      Verify: `test:e2e --grep "league-create-errors"`
- [ ] AC5: a retried or double-submitted create produces one league (idempotency key).
      Verify: `test:e2e --grep "league-create-idempotent"`
- [ ] AC6: axe clean, 320 px layout, keyboard-only completion.
      Verify: `test:e2e --grep "a11y|keyboard|phone"` extended

## Test requirements
Component tests per step; Playwright with the API stubbed at the network layer.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- The team-name word list lives once, on the server (APP-015); the client asks for suggestions.

## Known issues
_None._

## Follow-ups
_None._
