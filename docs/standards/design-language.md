# Design Language — "Courtside"

Status: **Accepted by owner request** (2026-10-02: "it should feel like someone from Apple designed it … create a
proper design spec and philosophy so that each time you touch the UI you align with it"). Choices marked **[owner]**
can be changed by the owner; everything else follows from them. Applies to `apps/web` (and later `apps/ios`).
Precedence: the owner's words > this document > `frontend.md` > a component's local style.

## 1. Philosophy
The app is a **calm coach on your phone**: it tells you what to do, shows why, and gets out of the way.
Four principles, in priority order (after Apple's Human Interface Guidelines: clarity, deference, depth):

1. **Clarity** — one decision per screen region, said in plain words; numbers are tabular and never truncated.
   If a user must think about the interface, it has failed.
2. **Deference** — content is the interface. Chrome is quiet (thin lines, soft materials); colour is reserved for
   meaning (win / lose / warning / accent action), never decoration.
3. **Depth** — layers explain hierarchy: ground → surfaces → raised (hover/press) → overlays (sheets, menus).
   Motion moves things *between* layers in a physically plausible way, so the user always knows where they are.
4. **Honesty** — every state is designed (loading, not ready, empty, stale, error; WEB-016); nothing pretends to be
   live when it isn't; sample data is always labelled.

Feel words: *precise, quiet, tactile, quick*. Never: *busy, gamey, neon, bouncy, decorative*.

## 2. Foundations (tokens; `apps/web/src/index.css` is the single source)
**Colour** — semantic tokens only (`ground, surface, surface-2, line, ink, ink-2, muted, accent, accent-tint,
accent-ink, win, lose, even, ok, warn`). Raw palette classes (`bg-red-500`, `text-gray-…`) are banned in components.
Both themes are designed, not inverted; the theme follows the phone (U7). Contrast ≥ 4.5:1 for text.

**Type** — Geist (variable), tabular figures for every number. iOS-like scale, nothing in between:

| Role | Size / line | Weight | Use |
|---|---|---|---|
| Large title | 28 / 34 | 700, −0.02em | page title |
| Title | 20 / 26 | 650 | sheet / section title |
| Headline | 17 / 22 | 600 | card title, player name in detail |
| Body | 15 / 21 | 400–500 | rows, text |
| Subhead | 13 / 18 | 400–500 | secondary lines |
| Caption | 11 / 14 | 500, +0.02em | labels, tab labels, uppercase eyebrows (+0.06em) |

**Space** — a 4-pt grid (4, 8, 12, 16, 20, 24, 32). Page gutter 20; card padding 16; list gap 8.
**Radius** — 8 (chips, inputs), 12 (rows, buttons), 16 (cards), 24 (sheets), full (avatars, pills). Nested radii
shrink by the padding (inner = outer − padding).
**Elevation** — four levels as tokens (`--shadow-0…3`): 0 flat; 1 resting card (hairline + 1px soft shadow);
2 hover/raised (y 4, blur 16, 8 % ink); 3 overlay (y 16, blur 48, 16 % ink). Dark mode uses lighter surfaces
(`surface-2`) plus a 1px inner highlight instead of heavier shadows.
**Materials** — the tab bar and sticky headers use a translucent material (sheets are opaque `surface`: the
scrim already separates them, and translucency over the scrim dropped badge text below 4.5:1 — WEB-008 axe finding):
`background: color-mix(in oklab, var(--surface) 72%, transparent); backdrop-filter: saturate(180%) blur(20px)`,
with a hairline (`--line` at 0.5px on retina) separating it from content.
**Icons** — one set: 24-grid stroke icons (Lucide-compatible paths), stroke 1.75, sizes 16/20/24; always paired
with a text label or an `aria-label`; never colour-only meaning.

## 3. Motion
Motion explains *change of place or state*; it is never ambient.

| Token | Duration | Easing | Use |
|---|---|---|---|
| `--motion-quick` | 120 ms | `cubic-bezier(0.2, 0, 0, 1)` | press, hover, toggles, chip state |
| `--motion-base` | 220 ms | `cubic-bezier(0.2, 0.8, 0.2, 1)` (spring-like, no overshoot) | list/row entry, expand/collapse, tab change |
| `--motion-sheet` | 360 ms | `cubic-bezier(0.32, 0.72, 0, 1)` (iOS sheet) | sheets/dialogs in; out is 240 ms ease-in |

Rules:
- **Enter from where it lives**: sheets rise from the bottom (phone) or scale 0.96→1 + fade (desktop); menus grow
  from their trigger; expanded rows reveal by height + fade.
- **Lists stagger** 24 ms per item, capped at 8 items (the rest appear together).
- **Numbers that change** cross-fade (no counting animations for money or ranks).
- **Skeletons shimmer** with a slow (1.6 s) linear sweep, never a pulse that flashes the whole block.
- **Reduced motion** (`prefers-reduced-motion: reduce`): every transform becomes an opacity fade ≤ 120 ms; no
  stagger, no shimmer. Tested.
- Animate only `transform` and `opacity` (and `height` via grid-rows for expanders) — never layout-thrashing props.

## 4. Interaction
- **Cursor**: every interactive element shows `cursor: pointer`; disabled shows `not-allowed`; draggable `grab`.
  Text inputs keep the text cursor.
- **Hover (pointer devices only, `@media (hover: hover) and (pointer: fine)`)**:
  - *Lift*: interactive cards/rows raise to elevation 2 and `translateY(-1px)` in `--motion-quick`.
  - *Light*: a soft spotlight follows the pointer across the surface — a radial gradient at `--x/--y`
    (`radial-gradient(240px circle at var(--x) var(--y), color-mix(in oklab, var(--accent) 10%, transparent), transparent 70%)`)
    plus a 1px border highlight on the same gradient. Implemented once in `Pressable`/`Surface`, not per page.
  - Buttons brighten ~4 % (primary) or gain `surface-2` (secondary).
- **Press**: scale 0.98 (rows/cards) or 0.96 (buttons/chips) for the press duration; release springs back.
  Touch devices get the press but never hover.
- **Focus**: a 2px `accent` ring with 2px offset on `:focus-visible` only; never removed.
- **Targets** ≥ 44×44 px; tab bar items full-height.
- **Feedback** within 100 ms of every action (press state, spinner in place of the label after 300 ms).

## 5. Components (the only way pages get these behaviours)
`Surface` (card with elevation + optional hover light), `Pressable` (row/card button with lift, light, press),
`Button`, `Chip`, `Sheet` (dialog: focus trap, Escape, scroll lock, drag-to-close on touch), `PageHeader`,
`StateCard` (WEB-016), `Skeleton`, `Badge` (icon + word; tones: neutral, accent, win, lose, warn), `Avatar`
(headshot with initials fallback), `TabBar` (material). A page that needs a new behaviour adds it to a primitive.

## 6. Content voice
Sentence case; verbs first on actions ("Start Smith tonight"); numbers with units ("+0.42 category wins");
no exclamation marks; no jargon on the surface (z-scores live in the "why"); dates as "Thu 1 Oct", times in the
owner's zone.

## 7. Checklist for every UI change (copy into the PR)
- [ ] Uses tokens and primitives only (no raw colours, no one-off shadows or durations)
- [ ] Type sizes from the scale; numbers tabular
- [ ] Every interactive element: pointer cursor, hover lift/light (pointer: fine), press, focus ring, ≥ 44 px
- [ ] Motion uses the three tokens; reduced-motion path checked
- [ ] All WEB-016 states covered for any new data view
- [ ] Light and dark both checked; 375 px and 1280 px both checked
- [ ] Icons paired with text or aria-label

## 8. Enforcement
- `tasks.py validate` (IMP-006) requires user stories/edge cases; web tasks list this document in `standards:` as
  `design`.
- Vitest guards: no raw palette classes in `src/` (grep test); `Pressable`/`Button` render `cursor-pointer` and
  focus-visible classes; the reduced-motion stylesheet exists.
- WEB-008 persona e2e adds visual checks (hover state screenshot on desktop, no overflow on phones).
- The `reviewer` subagent checks §7 and §9 on every web PR, and UI tasks attach a screenshot review (§9 loop).

## 9. Layout, density and data (v2, 2026-10-03)
The owner (2026-10-03): "the frontend is still not polished … desktop looks barebones … the player page's indicators
and stats aren't formatted the best." Grounded in `docs/research/ux-modern-interface.md` (UX-xx).

**Breakpoints and shell** (Material 3 window classes, UX-06; Apple sidebars, UX-01):
| Class | Width | Navigation | Content |
|---|---|---|---|
| Compact | < 600 px | bottom tab bar | single column, 20 px gutters |
| Medium | 600–839 px | bottom tab bar | single column, max 720 px |
| Expanded | 840–1199 px | **left sidebar** (240 px, icon + label, never hidden by default) | fluid column |
| Large / XL | ≥ 1200 px | sidebar | content max **1200 px**; list pages gain a **right detail panel** (≥ 400 px) instead of a modal |
The phone layout is never simply centred on a desktop.

**Home (Today) anatomy** (UX-32): the one-line recommendation → explicit freshness → 3–5 action cards → compact
summary (the scoreboard) → links to full tables. On desktop: two columns (actions left, scoreboard right).
**Signed-out landing** (UX-33): outcome-led hero + one primary action (sign in / view the demo) → "how it works" in
three steps → an honest principles section (the method, privacy; no fabricated testimonials, ratings or user counts).
The preview is the real component rendered on sample rows, not an image. "Explore with sample data" opens the app on
the sample fixtures inside the live build (no API calls), with a Sign in control to leave. The hero alone may use the
`display` size (40/44); app screens top out at `title-lg`.

**Data tables** (UX-14, UX-21–23): numeric columns right-aligned with tabular figures and a fixed number of decimals
per column; text left-aligned; the first column is the human name (with avatar); sticky header; a very subtle zebra
stripe (tables only); comfortable density by default with a compact toggle when > 15 rows; sortable headers
(`aria-sort`). Desktop list pages (Players, Waivers) are tables; phones keep rows/cards.

**Numbers**: the UI face (Geist) with `tabular-nums` for all figures; the mono face only for code/IDs. Stat grids never
leave an orphan cell (use a single table row, or fill the grid).

**Player detail anatomy** (UX-27, UX-28, UX-30): identity header (photo, name, team · position, ≤ 3 badges) → key
figures strip ($ value, rank, healthy rank) → **one signature visual**: the 9 categories as percentile bars on a
shared 0–100 scale against the draft pool (Savant-style; numbers at the bar end; never colour alone) → the projected
stat line as a compact one-row table (an 80 % range per stat when the API carries one) → indicators as a definition list (label · value · one short muted
line) → badges' why lines. On desktop it lives in the right panel; on phones in the sheet.

**Indicators and ranges** (UX-04, UX-15, UX-25): length/position encodes value; one colour scale per page; diverging
bars from zero for z-scores (`win`/`lose` either side); ranges as a thin track with the estimate marked, labelled at
the estimate and both ends only.

**Badges** (UX-10, UX-26): ≤ 3 per row/card + "+N"; filters live in one compact toolbar (search · strategy · sort ·
a "Filters" control), not stacked chip rows.

**Master-detail** (WEB-024): the right panel is non-modal (the list stays usable), takes focus on its first control,
closes on Escape / Close and returns focus to the row; a popover over the page claims Escape first. Beside an open
panel below 1600 px a table keeps its identity columns (#, name, $) and drops the stat columns the panel repeats.

**Status fills are opaque**: badge/chip tints are the tone mixed into the surface (`color-mix`), never translucent,
so contrast holds on zebra, hover and selected rows (axe found 4.19:1 with translucent fills).

**Empty / loading** (UX-17, UX-18): WEB-016's states, plus: skeletons for 0.4–3 s loads, a spinner only for longer or
indeterminate waits; every empty state says what it is, teaches, and links to the fixing action.

**Visual QA loop (required for UI tasks)**: `just web-screens` captures every route on phone and desktop; review the
images against §7 + this checklist, fix, re-capture; attach before/after notes to the task file:
- [ ] ≥ 1280 px: sidebar + content (+ detail panel where applicable); content ≤ 1200 px; nothing phone-sized centred
- [ ] tables: right-aligned tabular numbers, sticky header, subtle zebra, sortable headers
- [ ] player detail in the anatomy order above; one percentile visual; no orphan stat cells
- [ ] indicators/ranges use bars (length), never colour alone; ≤ 3 badges + overflow
- [ ] targets ≥ 24 px (pointer) / 44 px (touch); focus rings never hidden under sticky headers (WCAG 2.4.11)
- [ ] both themes; 375 px and 1280 px; no horizontal page scroll
