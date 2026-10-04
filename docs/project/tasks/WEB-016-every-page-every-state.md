---
id: WEB-016
title: "Every page handles every state: shared state screens, staleness, boundaries"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-005]
areas: [apps/web/**, apps/api/src/fantasy_api/schemas.py, apps/api/src/fantasy_api/views.py, apps/api/tests/**, apps/api/openapi.json, .github/workflows/ci.yml, tools/tests/test_ci_workflow.py, platform-manifest.yaml]
standards: [frontend]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# WEB-016 — Every page, every state

## Objective
The owner (2026-10-02): "we need better handling in the website if the page isn't ready yet, everything should be
properly formatted and follow our UI vision and standards. We need edge case handling for every scenario." Today a
missing brief shows "Couldn't load this. No brief published" in red: an error for a normal pre-season situation.
The frontend standard requires loading/empty/error states, a visible staleness badge, and per-feature error
boundaries; not all exist. Build them once, as shared components, and apply them to every page.

## Context to read (only these)
- `docs/standards/frontend.md` (decision-first UI, freshness always visible, error handling, accessibility)
- `docs/project/tasks/WEB-000-clickable-prototype-for-design-approval.md` § Decisions (the UI vision)
- `apps/web/src/components/ui/QueryState.tsx`, `Freshness.tsx`; the API problem types (`no-brief`, `no-matchup`,
  `no-players`, `unauthenticated`, `forbidden`, `rate-limited`, `snapshot-schema`)

## User stories and edge cases
States × pages. Each cell is the behaviour required; "—" means the state can't happen there.

| State (cause) | Today | Matchup | Waivers | Players | Ask |
|---|---|---|---|---|---|
| **Loading** (first fetch) | skeleton shaped like the scoreboard + list | skeleton of 9 rows | skeleton list | skeleton list (exists) | — |
| **Slow** (> 8 s) | skeleton + "Still working… the server may be waking up" | same | same | same | — |
| **Not ready yet** (404 `no-brief`: pre-season, before the first brief) | "Your daily brief starts once the season does" + what it will show + a link to Players | same message, Matchup wording | same, Waivers wording | 404 `no-players` (exists, restyled) | — |
| **No opponent** (404 `no-matchup`: bye / pre-season week) | — | "No matchup this week" (neutral) | — | — | — |
| **Empty** (data, nothing to show) | "Nothing to do today: your lineup is set" | — | "No free agent helps this week" | filters match nothing (exists) | — |
| **Coming soon** (feature not built) | — | — | — | — | the shared Coming-soon card (same header/typography as other pages) |
| **Stale** (brief built on old NBA data: `staleSince`) | a badge on top "Data from Thu 1 Oct: today's NBA update didn't run" + the freshness line | same | same | — (projections are pre-season) | — |
| **Signed out / expired** (401) | "Your sign-in expired" + Sign in again | same | same | same | — |
| **No access** (403) | "This account doesn't have access" + the signed-in email + Sign out | same | same | same | — |
| **Rate limited** (429) | "Too many requests: try again in a minute" + Retry | same | same | same | — |
| **Server problem** (5xx, 503 `snapshot-schema`) | "Something went wrong on our side" + Retry, never a stack trace or raw status as the headline | same | same | same | — |
| **Offline** (fetch fails, `navigator.onLine` false) | "You're offline" + retries automatically when back online | same | same | same | — |
| **Render crash** (a bug in one page) | that page shows "This page hit a problem" + Reload; the tab bar keeps working | same | same | same | same |
| **Site ahead of the API** (deploy in progress: 404 `not-found` for the route itself) | "This part is being updated: try again in a few minutes" + Retry; never the "not ready yet" copy | same | same | same (seen live 2026-10-02) | — |
| **Unknown URL** | a Not-found page with a link to Today, tab bar visible | | | | |

Cross-cutting edge cases: dark mode (tokens only, no raw colours); 375 px width (cards wrap, no overflow);
screen readers (state screens use `role="status"` for neutral states and `role="alert"` only for failures);
colour is never the only signal (an icon or word with each tone); sample (demo) mode never shows error states.

## Acceptance criteria
- [x] AC1: a shared `StateCard` (tone neutral/warning/error, icon, title, body, optional action) and `PageHeader`
      give every page the same header (title 26 px, sample badge) and state layout; Ask uses them.
      Verify: `apps/web/src/components/ui/StateCard.test.tsx`; states.test.tsx › "Ask is a coming-soon card under the shared header"
- [x] AC2: a `problemOf(error)` mapping turns every API problem type, HTTP status and network failure into one of
      the states above, with its copy and action; unknown problems fall back to "Server problem".
      Verify: `apps/web/src/api/problems.test.ts` (one case per row of the table, plus an unknown type)
- [x] AC3: Today, Matchup and Waivers render each applicable row of the table (not ready, no opponent, empty, 401,
      403, 429, 5xx, offline, slow) with the right role and action; Retry refetches; offline retries on `online`.
      Verify: `apps/web/src/features/states.test.tsx` (a parametrized page × state matrix) → all pass
- [x] AC4: the API exposes `staleSince` (date or null) in `freshness` from the brief snapshot, and every brief page
      shows the stale badge when it's set.
      Verify: `apps/api/tests/test_views.py::test_freshness_carries_stale_since`; states.test.tsx stale cases
- [x] AC5: a per-page error boundary catches a render crash, shows the crash card with Reload, and keeps the tab bar;
      an unknown URL shows the Not-found page.
      Verify: states.test.tsx (a page that throws; `/nope`)
- [x] AC6: no raw colour classes outside the tokens in the new components, and the whole suite stays green.
      Verify: `grep -rnE "(text|bg|border)-(red|green|blue|gray|zinc|slate)-" apps/web/src` → no matches; `just web test`, typecheck, lint

- [x] AC7: deploys can't put the site ahead of the API: the `hosting` job runs only after `deploy-api` succeeds on main (PR
      previews, and setups with Cloud Run disabled, don't wait), and "not ready" copy shows only for the specific problem types
      (`no-brief`, `no-matchup`, `no-players`), never for a generic 404.
      Verify: `.github/workflows/ci.yml` hosting `needs:` includes deploy-api (tests/test_ci_workflow or a yaml check);
      problems.test.ts (a `not-found` 404 → "being updated")

## Test requirements
Vitest + Testing Library with a fake `ApiClient` per state; fake timers for the slow state; `window` online/offline
events for offline. Real-browser coverage of the same states comes with WEB-008's personas.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/web/src/components/ui/StateCard.test.tsx (tone → role, icon, action outside the live region); states.test.tsx › "Ask is a coming-soon card under the shared header" | pass |
| AC2 | test | apps/web/src/api/problems.test.ts (13: every problem type/status, unknown fallback, offline vs unreachable, no status code in headlines) | pass |
| AC3 | test | apps/web/src/features/states.test.tsx (37: Today/Matchup/Waivers × not ready, 401, 403, 429, 500, 503, route-404, offline + online retry, slow; empty states; no-matchup) | pass |
| AC4 | test | apps/api/tests/test_views.py::test_freshness_carries_stale_since; states.test.tsx stale cases (3 pages + fresh case) | pass |
| AC5 | test | states.test.tsx › "a page that throws…", "an unknown address…" | pass |
| AC6 | test | design.test.ts (no raw palette classes); web suite 180 passed, tsc 0, eslint 0 | pass |
| AC7 | test | tools/tests/test_ci_workflow.py::test_hosting_waits_for_the_api_deploy_on_main; problems.test.ts (404 `not-found` → "being updated"); Players uses the shared ProblemCard | pass |

## Implementation history
- 2026-10-02 — Live incident: after PR #89 merged, Firebase Hosting deployed the new Players page ~10 min before the
  API's new revision was ready; `/players` returned the router's 404 `not-found`, which the page showed as "Player
  values aren't published yet" to the owner. Recovered once deploy-api finished (verified: the API's `/players` now
  401 without a token; the same code on `gs://nbafa-hdfo-dev-serve` returns 589 players). Added the row + AC7.
- 2026-10-02 — Specified from the owner's request; the state × page table drives the tests.
- 2026-10-02 — Built on the WEB-017 primitives: `problems.ts` (problem → state), `StateCard`, `QueryState` (slow,
  offline auto-retry, `ProblemCard`), `StaleNotice`, `RouteCrash` per route, `NotFoundPage`; page copy for not-ready
  and empty states; Ask coming-soon. App.test's old "shows the raw error" assertion was updated to the new rule
  (stricter: the raw text must NOT be shown). Players now uses ProblemCard, closing the live incident's root cause.

## Decisions
- Review (2026-10-03): the CI-ordering change makes this Tier B (`.github/`); areas and autonomy updated, merged under
  the owner's standing approval for Tier B. Demo mode is covered by a test (no problem states in sample mode).
  The Not-found action uses the new `ButtonLink` (design language §7).
- Pre-season copy avoids dates the app doesn't hold as data ("once the season does", not "on 20 Oct").

## Known issues
_None._

## Follow-ups
- WEB-008 persona e2e reuses this table for the real-browser checks.
