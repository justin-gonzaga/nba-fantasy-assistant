---
id: WEB-032
title: "Leagues panel: my leagues and discover public leagues"
epic: EP-75 Accounts and leagues
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: G-34
depends_on: [APP-014, WEB-030]
areas: [apps/web/src/leagues/**, apps/web/src/components/ui/Sidebar.tsx, apps/web/src/components/ui/TabBar.tsx, apps/web/src/features/practice/PracticeHub.tsx, apps/web/src/App.tsx, apps/web/e2e/leagues-panel*.spec.ts]
standards: [frontend, design-language, testing]
assignee:
created: 2026-10-04
completed:
---
# WEB-032 — The Leagues panel

## Objective
A Leagues area with two tabs: **Mine** (leagues I belong to, with my role and team) and **Discover** (public leagues I
can view and join). On desktop it is a sidebar item; on a phone it is reached from the avatar menu and a card on the
Practice hub (D-72 Q5), so the six-tab bar is unchanged.

## Context to read (only these)
- `docs/specification/leagues-and-accounts.md` §6 (discover, request), §7
- `apps/web/src/components/ui/Sidebar.tsx`, the mobile tab bar and the Practice hub (WEB-029)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Member with leagues | "my leagues at a glance" | role badge, `filled/capacity`, format chips, my team name; commissioner leagues first |
| Member with none | "where do I start?" | empty state with two actions: Create a league, Browse public leagues |
| Browsing | "find a league to join" | list with search (prefix), filters (format, has open spots), infinite scroll with a "load more" button for keyboard users; skeletons while loading; a result of zero is a message with the filters shown |
| Joining from the list | "one click" | open → joins then goes to the league; approval → a request form (team name, message ≤ 140) and a "requested" state; full → disabled with the reason |
| Slow or offline | resilient | cached page shown with a "may be out of date" note; errors have retry; no layout jump |
| Phone width | usable | cards stack; filter chips scroll horizontally; targets ≥ 44 px; works at 320 px |
| Signed-out visitor | no panel | redirected to sign-in, `/join#<token>` stays reachable |
| Private leagues | not exposed | never in Discover; no count mentions them |

## Acceptance criteria
- [ ] AC1: Mine and Discover lists render with role/format/occupancy chips; empty states offer the two actions.
      Verify: `corepack pnpm@10 --dir apps/web test:e2e --grep "leagues-panel"`
- [ ] AC2: search, filters and paging use the API cursor; a stale response never overwrites a newer search.
      Verify: `corepack pnpm@10 --dir apps/web test src/leagues -t "search race"`
- [ ] AC3: join (open), request (approval) and full states behave as specified, with the API problem codes mapped to
      sentences.
      Verify: `test:e2e --grep "leagues-join"`
- [ ] AC4: navigation: desktop sidebar item; phone avatar-menu entry and Practice-hub card; the phone tab bar still
      has six tabs and the 320 px fit test still passes.
      Verify: `test:e2e --grep "phone-nav|leagues-nav"`
- [ ] AC5: axe clean at 320 and 1280 px; keyboard-operable; loading and error states have tests.
      Verify: `test:e2e --grep "a11y|keyboard"` extended

## Test requirements
MSW-backed component tests; Playwright with fixture leagues (public open, public approval, full, private).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
