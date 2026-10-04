---
id: WEB-029
title: "Reach Draft practice, Season replay and Past sims from a phone"
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
# WEB-029 — Reach the simulators from a phone

## Objective
The owner (2026-10-04): "the simulator doesn't show when I open in mobile view." Cause (found in code): the only link
to a practice tool is under "Tools" in the desktop sidebar (`Sidebar.tsx`: Draft practice, Season replay, Past sims,
all present on `main`); the phone tab bar (`TabBar.tsx`) has five tabs and none leads there, and the sidebar is not
shown on a phone. The pages themselves render on a phone (the persona e2e runs them at iPhone 13 and Pixel 7 by URL).
Fix the phone navigation, and prove on a phone-sized viewport that the practice room is usable without typing a URL.
The hub lists only tools whose route exists (all three do now).

## Context to read (only these)
- `apps/web/src/components/ui/TabBar.tsx`, `Sidebar.tsx`, `apps/web/src/App.tsx` (routes, `WIDE`)
- `docs/standards/design-language.md` (tab bar, §9 screenshot loop)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner on a phone, any page | "I want to start a practice draft without typing a URL" | a sixth tab at 320 px wide still has ≥ 44 px targets and readable labels |
| Owner on a phone, mid practice | "Take me back to my draft" | the **Practice** tab stays highlighted on `/draft`, `/replay`, `/sims`, `/sims/:id`, `/practice` |
| Owner with a saved replay league or an unfinished practice | "Show what I can resume" | the hub shows **Resume** only when a saved run exists; none → no empty card |
| Signed-out / demo visitor | "What is this?" | the hub still lists the three tools; Past sims explains it needs sign-in (SIM-006) |
| Resizing across 840 px (WEB-028) | page state kept | the hub is not a second copy of the page: it only links |
| Screen reader / keyboard | one landmark, the tab named "Practice" | `aria-current="page"` on the active tab; no duplicate "Main" navigation landmark |

## Acceptance criteria
- [x] AC1: a sixth tab **Practice** (`/practice`) opens a hub linking every practice tool that has a route (Draft
      practice, Season replay; Past sims when its route exists). It is the active tab on every practice route.
      Verify: new `TabBar.test.tsx` › "Practice is active on /draft, /replay, /practice (and /sims, /sims/x when
      routed)"
- [x] AC2: the hub offers **Resume** for an unfinished practice draft or a saved replay league when one exists, and
      nothing when none does.
      Verify: `PracticeHub.test.tsx` › "resume appears only with a saved run"
- [x] AC3: at 320 px and 390 px wide, all six tabs are ≥ 44 px tall and wide, no label is clipped, and the page has no
      horizontal scroll.
      Verify: e2e `phone-nav.spec.ts` › "six tabs fit" (iPhone SE-size 320 × 568 and iPhone 13)
- [x] AC4: on iPhone 13 and Pixel 7, starting at `/today`, the owner reaches the practice room by taps only
      (Practice → Draft practice → Start) and sees the countdown; same for Season replay and Past sims. axe passes on
      the hub.
      Verify: e2e `phone-nav.spec.ts` › "tap to the practice room" (no `page.goto` after the first load)
- [x] AC5: on a phone-sized viewport, the setup, the room (nominate and bid), the report and `/replay` have no
      horizontal page scroll and every primary action is inside the viewport without zooming.
      Verify: e2e `phone-nav.spec.ts` › "practice pages fit the phone" (`scrollWidth <= clientWidth`, button boxes
      inside the viewport)
- [x] AC6: the desktop sidebar already lists the three tools under Tools; it is unchanged (the Practice tab is phone
      only, no second "Main" landmark).
      Verify: new `Sidebar.test.tsx` › "lists the five destinations and the practice tools; unchanged by the phone
      Practice tab"; desktop `screens.spec.ts` passes

## Test requirements
Vitest + Testing Library for the tab bar and hub; Playwright persona e2e at phone sizes with axe; the §9 screenshot
loop for the hub at 320 / 390 / desktop (read the PNGs).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `TabBar.test.tsx` › six tabs; Practice active on /practice, /draft, /replay, /sims, /sims/run:1 | pass |
| AC2 | unit | `PracticeHub.test.tsx` › resume appears only with a saved run; ignores a corrupt save | pass |
| AC3 | e2e | `phone-nav.spec.ts` › six tabs fit at 320 px and 390 px (≥ 44 px, no clip, no x-scroll), iPhone 13 + Pixel 7 | pass |
| AC4 | e2e | `phone-nav.spec.ts` › tap to the practice room, Season replay and Past sims (clicks only after the first load; axe on hub) | pass |
| AC5 | e2e | `phone-nav.spec.ts` › practice pages fit the phone, report included | pass |
| AC6 | unit | `Sidebar.test.tsx` › lists the five destinations and the practice tools | pass |

## Implementation history
- 2026-10-04 — Built: a sixth Practice tab (`Link` with explicit `aria-current`, active on /practice, /draft, /replay,
  /sims/*), `features/practice/PracticeHub.tsx` (links + Resume), route `/practice`; sidebar untouched. Tab clicks in
  the e2e (WebKit emulation drops `.tap()` on the sticky bar; a real tap is a click).
- 2026-10-04 — Specified from the owner's report. Priority P0 (draft is Sun 18 Oct).

## Decisions
- A sixth tab over a "More" sheet: one tap fewer, and "Practice" is a place the owner returns to every day until the
  draft. The hub can grow (settings, DRAFT-017) without touching the tab bar again.

## Known issues
_None._

## Follow-ups
_None._
