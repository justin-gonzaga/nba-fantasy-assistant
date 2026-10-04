---
id: DRAFT-020
title: "Practice room feel: closing-ring clock, sound effects and motion"
epic: EP-15 Draft assistant
phase: 7
component: web
status: in_progress
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DRAFT-016]
areas: [apps/web/**]
standards: [frontend, testing]
assignee: claude
created: 2026-10-04
completed:
---
# DRAFT-020 — Practice room feel

## Objective
The owner (2026-10-04): "more animations, sound effects when doing the practice draft (like clock ticking, a circle
that animates closing and turns red when 5 s left)." Make the room feel like draft night under time pressure
without costing legibility, accessibility or bundle size: a ring clock, synthesised sounds (no audio files), and
restrained motion that respects reduced-motion.

## Context to read (only these)
- `apps/web/src/features/draft/DraftPracticePage.tsx` (`Countdown`, `Timer`, `Room`), `practice.ts`
- `docs/standards/design-language.md` (motion tokens, §9 screenshot loop)

## Design
**Ring clock.** An SVG ring (stroke-dasharray) that *closes* from full to empty over the lot's seconds, with the
seconds in the centre. Pure function `clockState(left, total)` → `{ fraction, phase }`, phase = `calm` (> 10 s),
`warn` (≤ 10 s, amber), `urgent` (≤ 5 s, red + a pulse), `expired` (0). The ring is driven by `requestAnimationFrame`
from the same `end` timestamp as the digits (no drift, and it pauses visually when the tab is hidden). Colour is never
the only signal: the digits go bold, the ring pulses, and a visually hidden "5 seconds left" is announced (polite,
once at 10 and 5 s, as today). Replaces the thin bar everywhere `Timer` is used (nominate and bid).

**Sounds.** Synthesised with the Web Audio API (oscillator + gain envelope), so no files, licences or bytes.
`AudioPort` interface (`play(cue)`, `setVolume`, `unlock`) with a real implementation and a silent fake for tests.
Cues:

| Cue | When | Voice |
|---|---|---|
| `tick` | each second in the last 10 s (setting: off · last 10 s · every second) | short high click; quicker, higher in the last 5 s |
| `expire` | the clock hits 0 | low buzzer |
| `nominate` | a lot opens | soft two-note ping |
| `bid` | your bid is placed | click |
| `outbid` | a rival tops you | low blip |
| `soldYou` / `soldOther` | gavel: you won / someone else | bright chime / soft thud |
| `done` | the draft ends | short rising arpeggio |

`unlock()` runs inside the **Start practice draft** click (browsers only allow audio after a gesture); if the context
is still suspended the room shows "Sound is off — tap to enable", never fails silently. No sound while
`document.hidden`. A visible mute button and volume in the room header; the choice persists on this device
(`draft-fx-v1`; DRAFT-017 later syncs it to the account). Default: sound **on**, volume 60 %, tick **last 10 s**.

**Motion** (CSS transform/opacity only, 120–300 ms, no animation library): the nominated player slides in; the price
pops on each bid and the leading bidder chip flashes; **sold** stamps the card and the player slides into the buyer's
roster row; your budget bar eases; on the report, category-rank bars grow once and numbers count up. With
`prefers-reduced-motion: reduce` (or the setting "Reduce motion") there are no transforms or pulses: states change
instantly and the ring updates once per second without easing. Sound is independent of reduced motion.

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner practising under pressure | "I should feel the last 5 seconds" | ring red + pulse + faster ticks at ≤ 5 s; digits stay readable (contrast ≥ 4.5:1 in light and dark) |
| Owner in a quiet place or on a call | "Mute now" | one tap on the room header; persists; no sound after, including queued cues |
| iPhone with the ringer switch off, or a blocked autoplay | "Why no sound?" | hint "Sound is off — tap to enable"; the draft is fully usable without sound |
| Switching tabs mid-lot | timers continue (existing behaviour) | no catch-up burst of ticks on return; ring jumps to the true value |
| Screen-reader user | not spammed | only the 10 s and 5 s announcements, as now; ticks are not announced |
| Reduced-motion user | calm room | no running animations; ring steps once per second |
| Untimed pace | no clock | no ring, no tick; other cues still play |
| Fast-forward / "Sim the rest" | many sales at once | no sound flood: cues are rate-limited to one per 150 ms and skipped during fast-forward |
| Low-end phone | stays smooth | a lot's whole animation set adds no long task (> 50 ms) in the profile check |

## Acceptance criteria
- [ ] AC1: `clockState` is correct at the boundaries (total, 11, 10, 6, 5, 1, 0) and never returns `fraction`
      outside [0, 1].
      Verify: `clock.test.ts` › "clockState phases and fraction"
- [ ] AC2: the ring replaces the bar in nominate and bid; it closes with the remaining time, turns red at ≤ 5 s, and
      the digits and the polite announcements are unchanged.
      Verify: `DraftFeel.test.tsx` › "the ring closes with the time and turns urgent at 5 s" and "with reduced motion
      the ring steps once a second" (fake timers); axe on the room in the e2e
- [ ] AC3: cues fire for the right events and only then — tick per the setting, `expire` at 0, `nominate`, `bid`,
      `outbid`, `soldYou`/`soldOther`, `done` — through the `AudioPort`; muted or hidden → nothing plays; fast-forward
      plays at most one cue per 150 ms.
      Verify: `cues.test.ts` (pure event → cue mapping) and `DraftFeel.test.tsx` › "sounds follow the draft", "a bid plays the
      bid cue", "an expired clock plays the expire cue" (fake `AudioPort`)
- [ ] AC4: `unlock()` is called from the Start click; a suspended context shows the enable hint; mute and volume
      persist in `draft-fx-v1` and are read back; storage blocked → defaults, no crash.
      Verify: `fx.test.ts`, `DraftFeel.test.tsx` › "mute persists", "enable hint", "the hint clears by itself
      when the context resumes"
- [ ] AC5: the real voices render: each cue's `voiceSpec` (frequencies, durations, envelope) is finite, positive and
      ≤ 0.6 s, and the Web Audio adapter creates and stops oscillators without leaks (nodes disconnected on end).
      Verify: `voices.test.ts`, `webAudio.test.ts` (fake `AudioContext`)
- [ ] AC6: reduced motion: with `reducedMotion: 'reduce'`, a whole lot (nominate → bid → sold) leaves no running
      animations (`document.getAnimations().length === 0`) and the ring changes once per second.
      Verify: e2e `draft-feel.spec.ts` › "reduced motion has no running animations" (phone + desktop)
- [ ] AC7: the room still passes its existing tests and e2e scenarios; the draft page is lazy-loaded as its own route
      chunk (it is a static import today) and the fx code adds < 5 KB gzip to that chunk; no animation uses a
      layout-affecting property.
      Verify: `just web test`; `just web build` then `node apps/web/scripts/check-chunk-size.mjs` (new; fails over the
      budget, unit-tested); `animations.test.ts` (grep guard: only transform and opacity animate)
- [ ] AC8: §9 screenshot loop at 390 px and desktop for calm / warn / urgent states, read and checked for contrast
      and no overlap. The states are captured by a new fake-clock spec (`e2e/draft-feel-screens.spec.ts`, which advances
      the page clock to 12 s, 5 s and 0 s left) since `screens.spec.ts` only visits routes.
      Verify: `just web-screens` output in `apps/web/screens/` (draft room in calm, warn and urgent states), read, and
      noted in the task history
- [ ] AC9: owner listening pass: after deploy the owner hears each cue once and the voice table is adjusted or
      accepted.
      Verify: owner reply recorded in the task history (a human step; the task completes with AC1-AC8 and this one as a
      follow-up)

## Test requirements
Vitest with fake timers and a fake `AudioPort`/`AudioContext`; pure functions for state and cue mapping so the
timing logic is tested without audio; Playwright for reduced motion and phone fit. **Not testable by me**: how the
sounds actually sound; the owner listens and changes the voice table in a follow-up (listed below).

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit | `fx/clock.test.ts` › clockState phases and fraction (7 boundaries + out-of-range clamp) | pass |
| AC2 | unit | `DraftFeel.test.tsx` › the ring closes with the time and turns urgent at 5 s (digits and phase), reduced-motion ring steps once a second and never calls requestAnimationFrame; a11y suite unchanged | pass |
| AC3 | unit | `fx/cues.test.ts` (event to cue, tick map, rate limit and backlog), `DraftFeel.test.tsx` › sounds follow the draft, expire cue, bid cue | pass |
| AC4 | unit | `fx/fx.test.ts` (defaults, round-trip, repair, blocked storage), `DraftFeel.test.tsx` › Start unlocks, mute persists, enable hint, hint clears when the context resumes; `fx/webAudio.test.ts` subscribe | pass |
| AC5 | unit | `fx/voices.test.ts` (9 cues finite, positive, at most 0.6 s), `fx/webAudio.test.ts` (nodes disconnected on end) | pass |
| AC6 | e2e | `draft-feel.spec.ts` › reduced motion has no running animations (iPhone 13, Pixel 7, desktop); with motion on there are running animations | pass |
| AC7 | unit+build | vitest 434 pass; `just web-e2e` (build, then `check-chunk-size.mjs`, wired into the recipe): lazy DraftPracticePage chunk, fx 4086 B gzip of 5120 B; `animations.test.ts` (only transform and opacity) | pass |
| AC8 | screens | `SCREENS=1 playwright test e2e/draft-feel-screens.spec.ts`: calm (12 s), warn (8 s), urgent (3 s) at iPhone 13, Pixel 7, desktop; read: ring and digits legible, red on white readable, no overlap | pass |
| AC9 | human | owner listening pass after deploy | follow-up |

## Implementation history
- 2026-10-04 — Specified from the owner's request. Priority P1 (before the draft on Sun 18 Oct, after WEB-029).
- 2026-10-04 — Built under `features/draft/fx/` (clock, voices, Web Audio adapter, prefs, cues, ring, controls). The draft
  route is now lazy. A named chunk for fx was tried and dropped (it pulled React into that chunk); the budget script
  bundles the fx modules alone instead. Screens read for AC8: the tab bar still shows faint page text behind it in
  emulated WebKit (blur is not rendered there); unchanged from WEB-040.

- 2026-10-04 — Review fixes: `AudioPort.subscribe` so the enable hint clears when the context resumes (and
  `useSyncExternalStore` in `useFx`); cue player `dispose()` on unmount; the sold stamp is a fixed overlay (no layout
  shift); the ring digits stay readable by screen readers (only the svg is hidden) and `price-pop` moved off the
  `aria-live` node; report bars honour the reduced-motion preference; the nominate cue plays when entering on an open
  lot; the chunk budget check runs in `just web-e2e` (marker narrowed to the synth, since the report view legitimately
  reads the tiny prefs module).

## Decisions
- Synthesised audio over sample files: zero bytes, no licensing, and every voice is a few numbers the owner can ask
  to change.
- CSS/WAAPI over an animation library: the motion set is small; no new dependency (bundle and supply-chain cost).
- Sound defaults on, with a one-tap mute: the owner asked for it; unexpected sound is handled by the mute and the
  hidden-tab rule.

## Known issues
- iOS silences Web Audio when the ringer switch is off; the hint explains how to enable it.

## Follow-ups
- Add `node apps/web/scripts/check-chunk-size.mjs` to `.github/workflows/ci.yml` after the build (Tier B; it only runs
  locally via `just web-e2e` for now).
- Motion in the spec but not built: a won player sliding into its roster row, the budget bar easing, and the report
  count-up.
- Owner listening pass: adjust pitch/length of any cue (edit `voices.ts`).
- DRAFT-017 stores these preferences with the account.
