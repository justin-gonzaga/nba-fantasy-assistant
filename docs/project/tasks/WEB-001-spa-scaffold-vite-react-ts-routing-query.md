---
id: WEB-001
title: "SPA scaffold (Vite/React/TS, routing, query, UI kit)"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-07
depends_on: [WEB-000]
areas: [apps/web/**]
standards: [frontend]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# WEB-001 — SPA scaffold (Vite/React/TS, routing, query, UI kit)

## Objective
SPA scaffold (Vite/React/TS, routing, query, UI kit), built against typed sample fixtures until the API client exists (APP-003 then swaps the data layer only).

## Context to read (only these)
- docs/standards/frontend.md
- docs/project/tasks/WEB-000-clickable-prototype-for-design-approval.md (Decisions)

## Acceptance criteria
- [x] AC1: `apps/web`: React 19 + Vite + strict TypeScript + React Router + TanStack Query + Tailwind, pnpm; `just web <cmd>`
      Verify: `just web typecheck`; `just web build`
- [x] AC2: Routes /today, /matchup, /waivers, /ask with a tab bar; the WEB-000 picks are rendered from fixtures (Today B, Matchup A, Waivers A); the theme follows the phone
      Verify: `just web test` (App.test.tsx)
- [x] AC3: One data layer (`src/api`, `ApiClient` interface) with loading and error states on every query
      Verify: App.test.tsx "query states"
- [x] AC4: Accessibility: colour never the only signal (icon + words), aria-expanded/pressed, 44 px targets, a labelled table; ESLint strict + jsx-a11y strict clean
      Verify: `just web lint`; WinLabel.test.tsx
- [x] AC5: CI job `web` (format, lint, typecheck, tests, build, initial JS < 200 kB gzipped) and a required check on main
      Verify: PR checks; ruleset 24059050 contexts

## Test requirements
Vitest + Testing Library page tests against the fixture client; Playwright e2e comes in WEB-008.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | command | `pnpm typecheck` clean; `pnpm build` ok | ✅ |
| AC2 | tests | 13 tests pass (App.test.tsx, WinLabel.test.tsx) | ✅ |
| AC3 | tests | error + loading state tests | ✅ |
| AC4 | lint/tests | `eslint .` clean (typescript-eslint strict, jsx-a11y strict) | ✅ |
| AC5 | CI | PR #39: all 7 checks pass incl. `web`; `web` added to the required checks of ruleset 24059050 | ✅ |

## Implementation history
- 2026-09-27: APP-003 dependency dropped (the owner asked to continue the frontend now): pages read typed fixtures through `ApiClient`. The initial JS is 112.8 kB gzipped. `apps/web` is excluded from the uv workspace.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
