---
id: DRAFT-017
title: "Draft settings page: saved presets, and a practice room driven by them"
epic: EP-15 Draft assistant
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: [APP-011, DRAFT-020]
areas: [apps/web/**]
standards: [frontend, testing]
assignee:
created: 2026-10-04
completed:
---
# DRAFT-017 — Draft settings page and a parametrised room

## Objective
The owner (2026-10-04): "a proper draft settings page that saves your settings. You can also configure the settings."
Today the setup screen has a few inline controls and the room hard-codes 16 teams, $200, 14 spots and the nine
categories. Build one **Draft settings** page (reachable from the Practice hub and from the setup screen) where the
user edits, names, saves and picks presets; make the **engine and room read every league parameter from the preset**
instead of constants. This task handles the shapes the room supports today (category auction with any team count,
budget, roster size, seat, pace, bot styles, punt); DRAFT-019 adds other scoring formats and DRAFT-021 adds snake.

## Context to read (only these)
- `apps/web/src/features/draft/room.ts`, `practice.ts`, `DraftPracticePage.tsx`, `DraftSetup*` (the current inline controls)
- APP-011 (the document and its limits), `apps/web/src/api/*` (the typed client and the `sync.ts` conflict pattern)
- `docs/standards/design-language.md`

## Settings (what the page edits)
| Group | Fields | Notes |
|---|---|---|
| League | scoring (read-only chip until DRAFT-019), teams 4–20, budget $50–1000, roster spots 5–25; my seat shown only for snake drafts (DRAFT-021), ignored by auction | showing the derived total money and total picks ("16 teams × 14 = 224 picks, $3,200") |
| Room | pace (Real / Fast / Untimed / Custom), nominate and bid seconds, bot styles | Real = today's clocks, Fast = a fixed scale (about a third of Real), Custom reveals the two second fields; today the code only knows real and untimed, so Fast and Custom are new |
| Strategy | punt category (none / one of the league's categories) | |
| Season | current board, or a past season (as today) | |
| Sound and motion | sound on/off, volume, tick mode, motion auto/reduced | the same fields DRAFT-020 reads |

Built-in presets (not editable, can be duplicated): **My league** (16 × $200 × 14, real clocks), **Quick 8-team**,
**Mock with fast bots**. User presets: up to 10; save, rename, duplicate, delete, set as default (`activeId`).

## Engine parametrisation
`createRoom(preset, players)` takes the preset's league block. Budgets, number of teams, spots, and the minimum bid
($1) come from it. For a league that is not the default shape, the values come from a **labelled approximation**: the
default board's values are rescaled so the money of the drafted pool equals teams × budget (the pool share by rank is
re-derived, not hard-coded), the bots' reserve rules unchanged, and the room shows "approximate values for this league
size". When DRAFT-018 ships (decision D-70), the exact server values replace the approximation and the label goes; this
task does not pre-empt that decision, it only keeps non-default sizes usable. **Calibration check**: bot final prices at
two other league sizes still land near the (rescaled) board (a sweep, see AC4).

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner prepping the real draft | "my exact league, one tap" | **My league** is the default; the setup screen shows the active preset's one-line summary and a "Settings" link |
| Owner trying another size | "what if 12 teams" | teams = 12 → 12 rosters and bots, values marked approximate; the saved `seat` is clamped to teams (snake only) and says so |
| Impossible budgets | prevented, not crashed | budget < spots (can't afford $1 each) → inline error and Save disabled; spots × teams > player pool (e.g. 20 × 20 = 400 > pool size) → warning with the max |
| Signed-out / demo user | "can I still set it up?" | presets live in `localStorage` (`draft-presets-v1`), a note says "sign in to keep them on all devices"; on sign-in they merge once (names deduped with " (2)") |
| Offline or API down | works | edits stay local and queue; a banner shows "not saved yet"; save retries on reconnect |
| Two devices edit | no lost updates | 412 → reload, re-apply the user's change on the fresh document, retry once, else show both versions |
| Unsaved edits and navigation | no silent loss | a leave-guard asks to save or discard; Reset restores the preset's saved values |
| Deleting the active preset | sane | falls back to **My league**, announced |
| Saving a name that exists | clear | "That name is used" inline, nothing saved |
| Unsupported combination (future formats) | clear | greyed with "Coming with …", never silently coerced |
| Screen reader / keyboard | usable | every field labelled, errors tied via `aria-describedby`, Save reachable by Tab, focus moves to the first error |
| Phone | usable | single column, steppers ≥ 44 px, sticky Save bar above the tab bar |
| Old draft in progress | not broken | an unfinished practice draft keeps the preset it started with (stored in its snapshot) |

## Acceptance criteria
- [ ] AC1: the page lists built-in and user presets, and creates, edits, renames, duplicates, deletes and sets a
      default; validation mirrors APP-011 (same ranges) and blocks Save with inline, labelled errors; the derived
      totals line is correct.
      Verify: `DraftSettingsPage.test.tsx` (table of fields × invalid values; totals; default/delete flow)
- [ ] AC2: saving signed-in uses `PUT /me/draft-settings` with `If-Match`; a 412 is merged by re-applying the edit on
      the fresh document; the failing case shows both versions; signed-out uses `localStorage` and merges on sign-in.
      Verify: `draftSettingsSync.test.ts` (MSW: 200, 412 then 200, 412 twice, offline queue, merge on sign-in)
- [ ] AC3: `createRoom(preset)` honours teams, budget, spots and min bid for 4, 8, 12, 16 and 20 teams: roster
      counts, money totals and the final all-teams-complete state are correct; the default preset reproduces today's
      room exactly (golden snapshot of one seeded draft).
      Verify: `draftRoom.test.ts` › "parametrised league sizes", "default preset equals legacy room"
- [ ] AC4: calibration sweep: for 8 × $260 × 13 and 12 × $200 × 14, over 20 seeded bot-only drafts, the mean
      |final price − board value| for the top 50 players is ≤ the same statistic for the default league plus 15 %, and
      no team ends over budget or under roster.
      Verify: `draftRoom.calibration.test.ts` (prints the table into the task Evidence)
- [ ] AC5: the setup screen shows the active preset summary and starts the room from it; the room header names the
      preset; an unfinished draft resumes with the preset it began with.
      Verify: `DraftPractice.test.tsx` › "starts from the active preset", "resume keeps its preset"
- [ ] AC6: phone and accessibility: the page works at 390 px (single column, sticky Save above the tab bar, no
      horizontal scroll), keyboard-only completes create → save, axe passes.
      Verify: e2e `draft-settings.spec.ts` (iPhone 13 + desktop, axe) and the §9 screenshots read and noted
- [ ] AC7: sound and motion fields read and write the same record DRAFT-020 uses (`fx`), signed-in and local, with no
      duplicate source of truth.
      Verify: `fx.test.ts` › "settings page and room share fx"
- [ ] AC8: pace maps to clocks: Real equals today's durations, Fast is the fixed scale, Untimed has no clock, Custom
      uses the two fields (5–120 s); the room's timers and the lot-expiry behaviour follow it.
      Verify: `practice.test.ts` › "pace to seconds" (table) and `DraftPractice.test.tsx` › "fast pace expires sooner"
- [ ] AC9: non-default league sizes show the "approximate values" label, and the default league shows none.
      Verify: `DraftPractice.test.tsx` › "approximate label only off-default"

## Test requirements
Vitest + MSW for the page and sync; engine tests are pure and seeded; Playwright for phone and a11y. No new
dependencies (hand-written controlled form; no form library).

## Evaluation requirements
The calibration sweep in AC4 is the only quantitative check; the bot behaviour itself is unchanged.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified from the owner's request. Priority P1. Order: WEB-029 → DRAFT-020 and APP-011 in parallel →
  DRAFT-017. If time is short before 18 Oct, ship the page with presets stored locally and add the account sync after.

## Decisions
- Engine reads the preset, no global constants: this is the prerequisite for formats (DRAFT-019, 021) and tests.
- Built-in presets are immutable and duplicable: the owner's real league cannot be broken by experiments.
- Hand-written form: the form is small and the repo avoids a dependency for it.

## Known issues
- Past-season boards exist for 2023-24 → 2025-26 only; other seasons are disabled in the picker.

## Follow-ups
- DRAFT-019, DRAFT-021 enable more scoring and draft types in this page.
