---
id: DRAFT-019
title: "Practice room for points, roto and custom-category leagues"
epic: EP-15 Draft assistant
phase: 7
component: web
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DRAFT-017, DRAFT-018]
areas: [apps/web/**, apps/api/**, packages/core/**]
standards: [frontend, testing]
assignee:
created: 2026-10-04
completed:
---
# DRAFT-019 — Other scoring formats in the room

## Objective
The owner (2026-10-04): the model "should be able to handle different types of draft settings (points, category) and
different league types." The engine layer already speaks all five `ScoringFormat`s (ADR-0018); the room does not. Make
the preset's `scoring` choose the value vector, the bots' needs model, the team-needs panel, the recommendations and
the report, without a format `if` anywhere outside `ScoringObjective` (CLAUDE.md non-negotiable).

## Context to read (only these)
- ADR-0018, `packages/core/src/fantasy_core/league.py`, DRAFT-017, DRAFT-018
- `apps/web/src/features/draft/*` (needs panel, recommendations, report)

## Formats
| Format | Values from | Room differences |
|---|---|---|
| H2H categories (today) | category z-scores | needs panel = per-category bars; punt supported |
| Roto categories | category z-scores, season totals | no weekly framing; report = projected roto standings points |
| H2H points / season points | fantasy points per game × games from the preset's weights | needs panel = points by position/slot; no punt; report = projected points rank |
| Custom category set | z-scores over the chosen categories | any subset/superset within the supported stat list |

A generic `DraftPlayer.z` vector with `labels` (already any length) carries the dimension; the **same** room code
reads `labels` and `objective` from the valuation response, never the format name.

## User stories and edge cases
| Situation | Expected |
|---|---|
| Points league with the owner's weights (pts 1, reb 1.2, ast 1.5, stl 3, blk 3, tov −1 …) | values and bots follow points; stars with big usage rise, low-volume efficiency players fall |
| Weights all zero or a negative-only set | rejected at settings (APP-011) with a clear message |
| Custom categories: 5 chosen | needs panel shows 5 bars; the report ranks across 5 |
| Percentage categories included/excluded | attempts-weighted impact only when FG%/FT% are chosen |
| Punt in a points league | the control is hidden, not disabled silently |
| Roster slots differ (utility only, no positions) | position-needs panel hidden when the format has no positional constraint |
| Roto standings | the report says "projected roto points", not wins; never shows a win probability |

## Acceptance criteria
- [ ] AC1: the supported-combinations constant (APP-011) includes `h2h_points`, `season_points`, `roto` and custom
      category sets; the settings page lets the user pick them with the relevant extra fields (weights table or
      category checklist) and validates them.
      Verify: `uv run pytest -q apps/api/tests/test_draft_settings.py -k formats`; `DraftSettingsPage.test.tsx` ›
      "scoring format fields"
- [ ] AC2: the room runs a full seeded bot draft in each format with correct rosters and budgets; the needs panel,
      recommendations and report render from `labels`/`objective` only.
      Verify: `draftRoom.test.ts` › "full draft per format"; `NeedsPanel.test.tsx` › "any dimension"
- [ ] AC3: no format branching: a grep guard finds no `scoring ===`/format-name comparisons under
      `apps/web/src/features/draft`.
      Verify: `format-agnostic.test.ts` (greps the directory)
- [ ] AC4: points preset ranks match a hand-computed fixture for five players (weights × stat lines).
      Verify: `uv run pytest -q packages/models/tests -k points_fixture` and `DraftPractice.test.tsx` › "points board"
- [ ] AC5: reports label the outcome correctly per format (wins vs roto points vs points rank) and never show a number
      the format cannot support.
      Verify: `DraftReport.test.tsx` › "labels per format"
- [ ] AC6: phone fit and axe for the weights table and category checklist.
      Verify: e2e `draft-settings.spec.ts` › "points preset on phone"

## Test requirements
Seeded full-draft tests per format; fixtures for points; the grep guard; Playwright for the new controls.

## Evaluation requirements
n/a (no new prediction; valuation correctness is DRAFT-018 AC1–AC3).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified. Not required for the 18 Oct draft (the real league is H2H 9-cat). Priority P2.

## Decisions
- The room reads `labels` and `objective` from the data, so adding a format never touches the room.

## Known issues
_None._

## Follow-ups
- DRAFT-021 snake drafting.
