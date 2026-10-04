---
id: WEB-040
title: "Phone fit: nothing wider than the screen, no iOS focus zoom, a steady tab bar"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: S
autonomy: auto
gate: none
depends_on: []
areas: [apps/web/**]
standards: [frontend, testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-04
---
# WEB-040 — Phone fit and a steady tab bar

## Objective
The owner (2026-10-04) on a real phone: "the width is wider than my device so it doesn't fit without scrolling", and "a
bit of jitter when I play around with the menu at the bottom". Findings: the Playwright overflow checks passed on
the five original routes only; on the Players page the search box is 15 px and the two filters 13 px, so iOS Safari
zooms in when one is focused and leaves the page zoomed (looks wider than the device). The tab bar jitters because the
active tab changes from weight 500 to 600 (label widths shift), taps scale the tab, the shell uses `min-h-dvh` (the
height changes as Safari's toolbar collapses), and the translucent bar showed page text through its labels.

## Context to read (only these)
- `apps/web/src/components/ui/TabBar.tsx`, `apps/web/src/App.tsx` (Shell), `apps/web/src/index.css`
- `apps/web/e2e/phone.spec.ts`, `e2e/support/test.ts`

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner on an iPhone, any page | "The page fits my screen; focusing a box does not zoom" | form controls ≥ 16 px on touch devices; checkbox/radio/range unaffected |
| Owner tapping tabs | "The bar stays put" | no label width change when a tab becomes active; same bar top and height on every tab |
| Narrow phones (320 px) | "Nothing sticks out" | /draft, /practice, /replay, /sims included, not just the five tabs |
| Scrolling under the bar | "Labels stay readable" | bar background 90 % surface plus blur; opaque without backdrop-filter |

## Acceptance criteria
- [x] AC1: at 320, 360 and 390 px no element sticks out of the viewport (unless inside its own scrolling container) on
      /today /matchup /waivers /players /ask /practice /draft /replay /sims, and the page scroll width does not exceed
      the viewport.
      Verify: e2e `mobile-fit.spec.ts` › "nothing is wider than the screen at N px" (iPhone 13, Pixel 7)
- [x] AC2: every text input, select and textarea is at least 16 px on a touch device on all those routes.
      Verify: e2e `mobile-fit.spec.ts` › "controls are at least 16 px so iOS does not zoom the page on focus"
- [x] AC3: tapping each tab leaves the bar's top, height and every tab width unchanged.
      Verify: e2e `mobile-fit.spec.ts` › "the tab bar does not move or resize when tabs are tapped"
- [x] AC4: existing phone, a11y and design checks still pass.
      Verify: `pnpm exec vitest run` (design.test.ts material fallback at 90 %) and `playwright test` phone.spec.ts, a11y.spec.ts

## Test requirements
Playwright persona e2e on iPhone 13 and Pixel 7 (new `mobile-fit.spec.ts`); Vitest design test updated for the bar.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | e2e | `mobile-fit.spec.ts` › nothing is wider than the screen at 320, 360, 390 px | pass |
| AC2 | e2e | `mobile-fit.spec.ts` › controls are at least 16 px (Players had 15 and 13 px) | pass |
| AC3 | e2e | `mobile-fit.spec.ts` › the tab bar does not move or resize when tabs are tapped | pass |
| AC4 | unit+e2e | vitest 360 pass; playwright mobile-fit + phone + a11y 97 pass, 5 skipped | pass |

## Implementation history
- 2026-10-04 — Built: `@media (pointer: coarse)` 16 px control rule, `overflow-x: clip` and `touch-action: manipulation`
  backstops, `text-size-adjust`, `min-h-svh` shell, constant tab weight, opacity (not scale) press state, bar at 90 %
  surface. A `will-change` dock layer was tried and dropped: WebKit stopped blurring behind the bar.

## Decisions
- Fix the cause (focus zoom, label reflow, viewport-height change) rather than only clipping overflow; the clip is a backstop.

## Known issues
- Not reproduced on the owner's physical device; confirm after deploy.

## Follow-ups
_None._
