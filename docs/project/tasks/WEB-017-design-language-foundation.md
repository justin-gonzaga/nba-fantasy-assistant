---
id: WEB-017
title: "Design language foundation: tokens, motion, hover light, primitives on every page"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: [WEB-005]
areas: [apps/web/**, docs/standards/design-language.md, docs/standards/frontend.md, .claude/agents/reviewer.md]
standards: [frontend, design]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# WEB-017 — Design language foundation

## Objective
The owner (2026-10-02): "more dynamic animations, cursor changes, lighting changes when hovering over components …
it should feel like someone from Apple designed it. Create a proper design spec and philosophy so that each time you
touch the UI you align with it." Write that spec (`docs/standards/design-language.md`), encode it as tokens and
primitives, apply it to every existing page, and make the reviewer check it.

## Context to read (only these)
- `docs/standards/design-language.md` (this task writes it), `docs/standards/frontend.md`
- `apps/web/src/index.css`, `apps/web/src/components/ui/*`

## User stories and edge cases
| Persona / situation | Story | Edge cases |
|---|---|---|
| Owner on a laptop (mouse) | "It feels alive and precise when I move over things" | hover lift + light only with `pointer: fine`; pointer cursor on everything clickable; no hover jank while scrolling |
| Owner on a phone (touch) | "Taps feel physical, sheets slide like iOS" | press scale on touch; no sticky hover states after a tap; sheet rises from the bottom; drag-down closes |
| Motion-sensitive user | Reduced motion set in the OS | transforms become short fades; no stagger, no shimmer |
| Keyboard user | Tabs through | the focus ring is visible on every control, never clipped by overflow |
| Dark mode at night | Uses the app in bed | elevation reads via lighter surfaces + inner highlight, not heavy black shadows; contrast ≥ 4.5:1 |
| Low-end phone | Scrolls a 589-player list | animations only on transform/opacity; list stagger capped at 8; no layout thrash |
| Browser without `backdrop-filter` | Old WebView | the material falls back to an opaque surface |

## Acceptance criteria
- [x] AC1: `design-language.md` covers philosophy, foundations, motion, interaction, components, voice, a PR
      checklist and enforcement; `frontend.md` points to it; the reviewer agent checks its §7 on web PRs.
      Verify: files present; `grep -n "design-language" docs/standards/frontend.md .claude/agents/reviewer.md`
- [x] AC2: tokens in `index.css` for type scale, radii, elevation 0–3 (both themes), motion durations/easings,
      the material (with a no-`backdrop-filter` fallback) and a reduced-motion block.
      Verify: `apps/web/src/design.test.ts` (parses index.css: every token defined in light and dark; the
      reduced-motion block disables transforms)
- [x] AC3: primitives `Pressable`, `Surface`, `Sheet`, `Skeleton`, `Badge`, `Avatar`, `PageHeader` implement hover
      lift + pointer light (fine pointers only), press scale, pointer cursor, focus-visible ring; `Sheet` animates
      in/out, traps focus, locks scroll, closes on Escape/backdrop/drag-down.
      Verify: `apps/web/src/components/ui/*.test.tsx` (classes/attributes, light CSS vars update on pointermove,
      no update for touch pointers, Sheet behaviours)
- [x] AC4: every page (Today, Matchup, Waivers, Players, Ask) uses the primitives: no raw palette classes, no
      one-off shadows/durations; list rows stagger in; the tab bar uses the material.
      Verify: `apps/web/src/design.test.ts::no raw palette classes` (grep over src) and the existing page tests pass
- [x] AC5: bundle stays under the frontend budget (initial JS < 200 kB gzipped) — no animation library.
      Verify: `just web build` → the size line for the main chunk

## Test requirements
Vitest + Testing Library; CSS assertions by parsing `index.css`; pointer events via `fireEvent.pointerMove` with
`pointerType`. Visual checks (hover screenshots, both themes) belong to WEB-008.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | docs | `grep -n "design-language" docs/standards/frontend.md .claude/agents/reviewer.md` | ✅ frontend.md:12 and reviewer.md:42 both point to the doc; `design-language.md` §1–§8 present |
| AC2 | unit | `apps/web/src/design.test.ts` › "design tokens (AC2)": 23 themed tokens defined in light **and** dark (incl. `--surface-2`, `--warn`, `--raised`, `--scrim`, `--shadow-0..3`), 5 motion tokens, 14 scale tokens in `@theme`, durations 120/220/360/240 ms + 24 ms stagger, dark elevation has `inset` highlight, material `@supports` fallback, reduced-motion block (`transform: none !important`, `--stagger: 0ms`, no shimmer), stagger capped at 8, hover only under `(hover: hover) and (pointer: fine)`, light gradient at `--x/--y` | ✅ 49/49 pass |
| AC3 | unit | `components/ui/Pressable.test.tsx` (11: cursor/focus/lift/light/press classes, `--x/--y` update on mouse pointermove, none for touch/pen, handlers composed, bare variant, disabled not-allowed, Button + Chip, Surface static vs interactive); `Sheet.test.tsx` (9: labelled modal + `data-state`, first-control focus + Tab trap both ways, Escape, backdrop vs inside click, body scroll lock restore, touch drag ≥ 80 px closes, short/upward drag springs back, `data-sheet-close` closes once, mouse drag ignored); `Primitives.test.tsx` (13: Skeleton, Badge tones ×5 with icon + words, Avatar fallback + retry on new src + initials ×4, PageHeader) | ✅ 33/33 pass |
| AC4 | unit + regression | `design.test.ts` › "pages use tokens and primitives (AC4)": no raw palette classes, no one-off shadows/durations/easings/`animate-*`, type sizes only from the scale, no hex colours in components (grep over all non-test `src/**/*.{ts,tsx}`); existing page tests (App 9, PlayersPage 16, auth 5, WinLabel 5, http 3, firebase 4 = 42) unchanged and passing | ✅ 5/5 + 42/42; full suite 129/129 (`just web test`) |
| AC5 | build | `just web build` → `dist/assets/index-*.js 382.80 kB │ gzip: 119.90 kB`; CSS 6.84 kB gzip; `package.json` has no animation library | ✅ 119.90 kB < 200 kB |

Also run: `just web typecheck` (0 errors), `just web lint` (0 problems), `just web format` (clean), `python tools/tasks.py validate` (0 errors).

## Implementation history
- 2026-10-02 — Spec and `design-language.md` written first (owner request); implementation next.
- 2026-10-02 — Implemented test-first. `index.css`: light/dark semantic tokens (+ `surface-2`, `warn`, `raised`,
  `scrim`), elevation `--shadow-0..3` (dark = inner highlight), motion durations, `@theme static` type scale
  (`text-title-lg … text-caption`), radii (`rounded-chip/row/card/sheet`), easings, Tailwind default transition =
  quick token; base layer gives every control a pointer cursor and the focus ring; component classes `surface`,
  `material` (+ `@supports` blur), `lift`, `light` (radial spotlight + border highlight), `press`/`press-strong`,
  `skeleton` shimmer, `stagger` (24 ms, cap 8), `reveal`, sheet enter/exit keyframes; reduced-motion block.
  Primitives: `Pressable`, `Surface`, `Sheet`, `Skeleton`, `Badge`, `Avatar` (from `Headshot`, now deleted),
  `PageHeader`, `Chip`, `usePointerLight`, shared `INTERACTIVE` classes; `Button`/`Card`/`TabBar`/`QueryState`
  (skeleton loading)/`SampleBadge` updated. All five pages + sign-in screen moved to the primitives and type scale;
  `PlayerDetail` is now a `Sheet`. Light `--warn` darkened to #854d0e so warn badges reach ≥ 4.5:1 on their tint.

## Decisions
- No animation library (Framer Motion etc.): CSS transitions + a tiny pointer hook keep the bundle small and the
  motion tokens in one place. Revisit only if gesture physics (drag-to-close) needs it.

## Known issues
- Not yet built (no current UI needs them): number cross-fade on change, "spinner after 300 ms" on async
  actions, menus growing from their trigger. Expanders (Today actions, Matchup categories) reveal with fade + rise
  on open but collapse instantly (no grid-rows height animation yet).
- Drag-to-close works from the grabber at the top of the sheet (touch only), not from anywhere in the content.
- Under reduced motion the press scale is also removed (transforms off); feedback is the colour/shadow change.
- Hover/both-theme/375 px visual checks are WEB-008 (jsdom can't verify rendering).

## Follow-ups
- WEB-018 player badges use `Badge`.
