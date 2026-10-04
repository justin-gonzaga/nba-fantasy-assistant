---
id: WEB-008
title: "Persona e2e: Playwright user stories on phone and desktop + axe"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-005]
areas: [apps/web/**, .github/workflows/ci.yml, justfile, platform-manifest.yaml]
standards: [frontend, testing]
assignee:
created: 2026-09-24
completed: 2026-10-02
---
# WEB-008 — Persona e2e tests

## Objective
Prove the site serves each kind of visitor well, in a real browser, on a phone and a desktop: the owner asked for
"different user agents so we can test different 'user stories' using the website". Each persona is a Playwright
spec running against the production build with the API mocked at the network layer, on three device profiles,
with axe accessibility checks. Runs in CI.

## Context to read (only these)
- `apps/web/src/App.tsx`, `apps/web/src/api/select.ts`, `apps/web/src/auth/auth.tsx`
- `.github/workflows/ci.yml` (web job)

## User stories and edge cases
| Persona / situation | Story | Edge cases the e2e must cover |
|---|---|---|
| **Demo visitor** (sample build, no sign-in) | "What is this? Show me." | every tab renders with "Sample data"; no request leaves for the API or Firebase; deep link `/players?q=jok` works on first load |
| **Owner pre-draft** (live build, signed in) | "Find what Wembanyama is worth; compare punting assists" | Players with a 589-row realistic payload; Today/Matchup show the friendly "no brief yet" state (404) instead of an error |
| **Owner in-season** | "What do I do today? Who should I pick up?" | Today actions expand; Matchup categories; Waivers filter; Players status badges |
| **Owner on a stale day** (the PC didn't fetch) | "Can I trust this?" | the StaleNotice ("Data from Tue 20 Oct") on Today/Matchup/Waivers; nothing claims to be live |
| **Stranger** (signed in, not invited) | "Why can't I see anything?" | API 403 → a clear "This account doesn't have access" + Sign out, on every tab; no data shown |
| **API down / slow** | "Is it broken?" | 502 → error + Retry that recovers; a 3 s response shows loading, never a blank page; a route 404 (site ahead of API) shows "being updated" |
| **Draft prep** (owner, desktop) | "Show me injury-prone players and open one" | Players badge filter + detail sheet badges with why lines (WEB-018); healthy-rank sort (WEB-019) |
| **Keyboard-only user** | Uses Tab/Enter/Escape | reaches every tab link; opens and closes a player with focus restored |
| **Phone user** (iPhone 13 WebKit, Pixel 7 Chromium) | One-handed use | no horizontal scroll on any page at 375–412 px; tab labels not clipped; tap targets ≥ 44 px on the tab bar |
| **Desktop user** (1280×800 Chromium) | Laptop | the column layout is centred and readable |

## Acceptance criteria
- [x] AC1: Playwright is set up with three projects (iPhone 13 WebKit, Pixel 7 Chromium, Desktop Chrome) against
      `vite preview` of the production build; `just web-e2e` runs it locally.
      Verify: `just web-e2e` → all specs pass on 3 projects
- [x] AC2: live-mode personas use a build-time e2e auth seam (`VITE_E2E_AUTH=1` → a fake adapter with a
      fixed identity; tree-shaken out of normal builds) and API mocks via `page.route`; no real Google or API calls.
      Verify: `grep -c E2E dist/assets/*.js` on a normal build → 0; e2e network log shows only mocked hosts
- [x] AC3: one spec per persona row above (10), each asserting its edge cases.
      Verify: `apps/web/e2e/*.spec.ts` → 10 persona files, all pass on every project
- [x] AC4: the stranger persona sees a dedicated no-access screen (new UI if missing) rather than a generic error.
      Verify: `e2e/stranger.spec.ts`, plus a Vitest unit test for the screen
- [x] AC5: axe (`@axe-core/playwright`) reports 0 serious/critical violations on every page in every persona.
      Verify: `e2e/a11y.spec.ts` (all routes × demo + owner) → 0 serious/critical
- [x] AC6: no horizontal overflow (`scrollWidth <= innerWidth`) on every route on both phone projects.
      Verify: `e2e/phone.spec.ts`
- [x] AC7: CI runs the e2e job on PRs touching `apps/web/**` (browsers cached), uploading the HTML report and
      screenshots on failure; wall time ≤ 6 min.
      Verify: the PR's CI run → `web-e2e` green; duration from the run page

## Test requirements
Playwright specs in `apps/web/e2e/`, fixtures in `e2e/fixtures/` (typed against `src/api/types.ts`). Write each
persona spec first against today's UI; where it fails for a real gap (e.g. the no-access screen), fix the UI in this
task if small, or file a follow-up.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | command | `just web-e2e` (apps/web/playwright.config.ts: iphone-13 WebKit, pixel-7 Chromium, desktop-chrome 1280×800; webServer = `vite build` + `vite preview` of the demo and e2e-live builds) | 175 passed, 5 skipped, 0 failed in 46 s (16 workers): iphone-13 57 ✓ / 3 skip, pixel-7 58 ✓ / 2 skip, desktop-chrome 60 ✓ |
| AC2 | test + command | src/auth/e2eAuth.ts (+ e2eAuth.test.ts, 2 tests); `node scripts/check-no-e2e.mjs dist` (also a CI step in `web`); `grep -ci e2e dist/assets/*.js`; e2e/support/test.ts auto fixture fails any test whose page hits a host other than the site, `api.e2e.test` (mocked) or the aborted headshot CDN | normal build: 0 hits in all 4 chunks; a live-mode build with dummy Firebase vars: 0 hits; e2e build: seam present; no test reached an unmocked host; owner calls carry `Bearer e2e-token:…` |
| AC3 | test | apps/web/e2e/{demo-visitor, owner-pre-draft, owner-in-season, owner-stale-day, stranger, api-down, draft-prep, keyboard, phone, desktop}.spec.ts | 10 persona files, all pass on every project (skips: desktop persona on the 2 phone projects; Tab-to-links on WebKit, where Safari skips links by default) |
| AC4 | test | e2e/stranger.spec.ts (6 tests: 4 data tabs, Ask, Sign out → sign-in screen); src/features/noAccess.test.tsx (4 Vitest cases) | pass; the existing WEB-016 forbidden card is the dedicated screen ("This account doesn’t have access", account named, Sign out, no data, no Retry) |
| AC5 | test | e2e/a11y.spec.ts: 5 routes × demo light, demo dark, owner in-season; sheet open (light, dark); 404 page; sign-in screen; not-ready, no-access and error states; tags wcag2a/aa, 21a/aa, 22aa | 0 serious/critical on all 3 projects after one UI fix (sheet contrast, see history) |
| AC6 | test | e2e/phone.spec.ts: every route at 375, 390 and 412 px in the demo and owner builds, plus the open sheet and an expanded action; tab bar labels unclipped and targets ≥ 44 × 44 | pass on iphone-13 and pixel-7 (and desktop-chrome) |
| AC7 | CI run | https://github.com/justin-gonzaga/nba-fantasy-assistant/actions/runs/37077834727/job/111071899910 (PR #99) | web-e2e green in 5 min 34 s (cold browser cache) |

## Implementation history
- 2026-10-02 — Refined from the placeholder (owner: test different user stories with different user agents).
  Depends on WEB-005 instead of WEB-002/004/006, since the trade analyser (WEB-006) is later and the specs cover the
  pages that exist; WEB-006 adds its own persona spec.
- 2026-10-03 — Built. `@playwright/test` 1.63 + `@axe-core/playwright` 4.13. Auth seam: `select.ts` reads
  `import.meta.env.VITE_E2E_AUTH` directly so Vite inlines it, and `e2eAuth()` (identity from localStorage
  `e2e-email`) is only reachable when it is `'1'`; in e2e mode Firebase config is not required. Fixtures typed against
  `src/api/types.ts`: the SAMPLE brief, a stale-day copy (`staleSince` 2026-10-20), and a seeded 589-row players
  payload (the 10 sample players + 579 fictional) with badges and healthy ranks. Vitest now includes only
  `src/**/*.test.*`; `tsconfig.e2e.json` typechecks e2e; `pnpm format` covers e2e.
  UI fix found by axe: the player sheet's translucent material over the scrim dropped the "Injury prone" (lose) badge
  to 3.9:1 on Pixel 7; sheets are now opaque (`.sheet-panel.material`, index.css), giving the page's ≥ 4.5:1.
  Checks: vitest 217 passed (16 files); typecheck, lint, prettier clean; tasks.py validate 0 errors; manifest_check
  exit 0; tools tests 76 passed.

## Decisions
- Review: sheets are opaque by design (documented in design-language §2 Materials); the web-e2e job has
  `permissions: contents: read`.
- Mock the API at the network layer instead of running FastAPI in CI: the API has its own contract tests, and the
  generated types keep fixtures honest; e2e here proves the browser experience.
- A build-time auth seam rather than real Google sign-in: automated Google logins are brittle and against their
  terms; WEB-013's real sign-in stays covered by its manual live check.

## Known issues
- axe's target-size rule reads a row under the sticky tab bar (mid-scroll) as an obscured target; a11y.spec scrolls
  to the page end before each scan, where the bar sits below the content. Real taps scroll first.
- WebKit (iPhone 13 project) doesn't Tab to links without Safari's "Press Tab to highlight each item" setting, so the
  Tab-to-tab-links test skips there; the player open/close keyboard test runs on all three projects.
- platform-manifest.yaml: the platform glob `apps/web/*.ts` (fnmatch `*` crosses `/`) classifies the new e2e files
  (and existing `src/**/*.ts`) as platform before the domain `apps/*` entry is reached. Fixing it means narrowing that
  glob (manifest is outside this task's areas): left for GEN/manifest follow-up.

## Follow-ups
- The stale-day persona checks WEB-016's StaleNotice ("Data from …").
- 2026-10-03 — Manifest follow-up done: `apps/web/*.ts|js` (which matched subfolders) replaced by the explicit root
  configs, so e2e specs and the Playwright config classify as domain (checked with `manifest_check.layer`).
