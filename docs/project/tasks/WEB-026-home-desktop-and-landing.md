---
id: WEB-026
title: "Home on desktop and a real signed-out landing page"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-023]
areas: [apps/web/**, docs/standards/design-language.md]
standards: [frontend, design]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# WEB-026 — Home on desktop and the landing page

## Objective
Today on desktop is the phone column; the signed-out screen is a bare sign-in box. Per design-language §9: a
two-column home (actions + freshness left, scoreboard right) and a landing page (hero, how it works with real sample
screens, honest proof, sign in / view the demo).

## Context to read (only these)
- design-language §9 (home, landing); `features/today/TodayPage.tsx`, `auth/auth.tsx` (SignInGate)

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner on a laptop, morning | the recommendation line, freshness, action cards left; the 9-category scoreboard right | before the season: the not-ready card spans both columns |
| Visitor not signed in | landing: outcome headline, one primary action (Sign in with Google), a secondary "Explore with sample data", a product preview built from the real components with sample rows, a 3-step how it works, an honest principles section, a footer disclaimer | sign-in errors inline; phones stack the hero; no horizontal scroll at 375 px |
| Visitor exploring | "Explore with sample data" enters the app on the sample fixtures (no API or auth calls), the Sample data badge shows, and a "Sign in" control leaves sample mode | refresh keeps sample mode for the tab (sessionStorage); a blocked storage just means it doesn't persist |
| Owner signs in | the app on live data, as today | — |

## Acceptance criteria
- [x] AC1: ≥ 1200 px Today renders two columns in the §9 order; phones unchanged.
      Verify: `App.test.tsx` › "today desktop"; e2e desktop persona
- [x] AC2: the signed-out screen is the landing (hero, preview, how it works, principles, primary + secondary actions);
      sign-in errors inline.
      Verify: `Landing.test.tsx` › "landing"
- [x] AC3: "Explore with sample data" opens the app in sample mode with no API calls; "Sign in" leaves it.
      Verify: `Landing.test.tsx` › "sample mode"
- [x] AC4: no fabricated claims (no user counts, ratings or testimonials).
      Verify: review + `Landing.test.tsx` › "no fabricated claims"

## Plan
1. `Landing` (auth/Landing.tsx) replaces the bare sign-in box; `SignInGate` takes `onExplore`.
2. `App`: sample mode state (sessionStorage) → fixture client + sample flag, no gate; a `SampleMode` context gives
   the Sidebar / phone footer a "Sign in" control that leaves it.
3. Today ≥ 1200 px: two columns (actions + freshness left, scoreboard right, sticky); `/today` joins the wide routes.
4. Tests first; e2e stranger persona updated; screenshot loop on the landing (phone + desktop).

## Test requirements
Vitest; persona e2e green; the §9 visual QA loop with a before/after review.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit + e2e | `App.test.tsx` › today desktop (1280 two columns; 390 one); `desktop.spec.ts` | pass |
| AC2 | unit + e2e | `Landing.test.tsx` › landing (hero, preview, 3 steps, principles, both actions) + inline error; `landing.spec.ts` | pass |
| AC3 | unit + e2e | `Landing.test.tsx` › sample mode (no live calls, refresh, Sign in leaves); `landing.spec.ts` (no API requests) | pass |
| AC4 | unit + review | `Landing.test.tsx` › no fabricated claims; copy reviewed against the repo (eval-gate, pseudonymisation, overnight ingest) | pass |

## Implementation history
- 2026-10-03 — Specified from the owner's request and the screenshot review.
- 2026-10-03 — Built `Landing` (hero, live-component preview on sample rows, how it works, principles, footer
  disclaimer), sample mode in the live build (sessionStorage per tab; the query cache is cleared on entry/exit so
  sample answers never show as live), Sidebar/phone "Sign in" control, Today two columns ≥ 1200 px, `display` type
  token. Screens: before — a bare sign-in box; Today a single column. After — the landing (desktop two-column hero,
  phone stacked; the preview drops REB/AST < 480 px after the first phone shot crammed the figures); Today actions
  left, scoreboard right. design-language §9 updated (landing, master-detail, opaque fills). Vitest 251; e2e 182.

## Decisions
- Tier B: adds to design-language §9 (merged under the owner's standing approval for UI standards work).
- The §9 "Master-detail" and "Status fills are opaque" paragraphs come from WEB-024, whose Decisions deferred them
  to this task (WEB-024 is merged, #107).
- Review: "Projections as ranges" overstated the API (point estimates + Range/Certainty indicators) → reworded to
  "Projections with certainty".
- "See the demo" became an in-app sample mode: there is no separately hosted demo build.

## Known issues
_None._

## Follow-ups
_None._
