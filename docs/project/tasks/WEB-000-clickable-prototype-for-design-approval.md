---
id: WEB-000
title: "Clickable prototype of key screens for design approval (U8)"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: review
gate: none
depends_on: []
areas: [docs/design/**]
standards: [frontend]
assignee: claude
created: 2026-09-24
completed: 2026-09-27
---
# WEB-000 — Clickable prototype for design approval

## Objective
Before any real frontend work: a shareable, clickable prototype of the Today, Matchup, Waivers and Chat screens (+ the public demo landing page), each in 2–3 variants, built to U1–U7. The owner picks the variants via panels.

## Acceptance criteria
- [x] AC1: A clickable prototype of Today (3 variants + dark mode), Matchup (2), Waivers (2), Ask/chat (1) and the public demo landing (1), at phone width (390x844) except the landing (1280), on sample data only, with other managers pseudonymised
      Verify: the prototype canvas (link under Implementation history), 10 artboards
- [x] AC2: Built to U1-U7 and the frontend standard: actions first, action cards with an expandable why, simple and drill-down, colour never the only signal (icon + text), 44 px touch targets, freshness shown
      Verify: open Today A in Play: Why? expands; win/loss rows use ▲/▼ plus text
- [x] AC3: The owner picks one variant per screen; the choices are recorded as the spec for WEB-001..WEB-009
      Verify: a Decisions entry in this file naming each chosen variant

## Test requirements
A design artefact, not code: verified by the owner using Play mode. The real screens get Vitest and Playwright tests in WEB-001..008.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | prototype | canvas https://claude.ai/artifact/5KKRXC7BHLjhYojeXNg1qQ: 10 artboards (Today A/B/C + dark, Matchup A/B, Waivers A/B, Ask, Demo) | ✅ |
| AC2 | review | Play mode: Why? expands, filters and category taps work; ▲/▼/● + text; 44 px targets; freshness line | ✅ |
| AC3 | owner | picks recorded under Decisions (Today B, Matchup A, Waivers A) | ✅ |

## Implementation history
- 2026-09-27: The owner asked to start the mockups now; the ANL-007 dependency was dropped (mockups use sample data). Prototype canvas: https://claude.ai/artifact/5KKRXC7BHLjhYojeXNg1qQ (private to the owner). Look: Geist + Geist Mono, warm-neutral ground, one orange accent, blue/orange for win/loss (colour-blind safe); the name "Courtside" is a placeholder.

## Decisions
- 2026-09-27, owner picks (the spec for the real screens):
  - **Today: B, scoreboard first.** The 9-category projected scoreboard on top, then a compact "Do today" list whose rows open the action card with its why (WEB-002).
  - **Matchup: A, category board.** All 9 categories with a win-chance bar, ▲/▼/● plus text; tap a category for what moves it (WEB-003).
  - **Waivers: A, ranked list.** Ranked by expected category wins gained this week, with category filter chips and a suggested drop (WEB-004).
  - Ask/chat and the public demo landing: the single variants shown, as-is (WEB-009, D-38).
  - Theme follows the phone; the dark palette is as in "Today A in dark mode".

## Known issues
_None._

## Follow-ups
_None._
