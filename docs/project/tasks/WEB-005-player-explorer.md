---
id: WEB-005
title: "Player explorer: ranked values, search, filters, headshots, detail"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [WEB-001]
areas: [apps/web/**, apps/api/**]
standards: [frontend, backend]
assignee: claude
created: 2026-09-24
completed: 2026-10-02
---
# WEB-005 — Player explorer

## Objective
A Players tab where the owner can look up any projected player: auction value, rank and tier, per-game projection,
category strengths, team and today's injury status, under the all-category ranking or a punt strategy. It is the
first page that works before the season (the draft is 18 Oct), so it serves real data now. API: `GET /players`
(D-62 read path, published parquet).

## Context to read (only these)
- `apps/api/src/fantasy_api/views.py` (the existing endpoint pattern)
- `apps/web/src/features/waivers/` (the existing page pattern), `apps/web/src/components/ui/QueryState.tsx`
- `apps/web/firebase.json` (CSP)

## User stories and edge cases
| Persona / situation | Story | Edge cases the page must handle |
|---|---|---|
| Owner pre-draft, phone | "Find Jokić and see what he's worth" | accents and case (`jokic` finds `Jokić`), no match, partial names |
| Owner pre-draft | "Show only centers, sorted by $" / "What changes if I punt assists?" | filter + sort + strategy combine; strategy refetch keeps the filters; the URL keeps the state (back button, refresh) |
| Owner in-season | "Is this player hurt, and who does he play for?" | no week table yet (pre-season) → no team/status shown, no blank badges |
| Any | Browsing ~500 players on a phone | render in pages of 50 + "Show more"; a count of matches |
| Any | Images | a headshot that fails to load (new player, CDN down, CSP) → initials avatar, no broken-image icon |
| Any | Data gaps | no projection → "No projection yet"; no position; long names truncate |
| Any | System states | loading skeleton; values not published (404) → explained empty state; network/5xx → error with Retry; a stale `variant` in the URL → falls back to `all` |
| Keyboard / screen reader | Navigate and open details | labelled search; filter chips are toggle buttons (`aria-pressed`); detail is a dialog: Escape closes, focus returns to the row |

## Acceptance criteria
- [x] AC1: `GET /players[?variant=]` returns players ordered by rank with values, strengths, projection (FG%/FT% derived
      from makes/attempts, rounded to 3), team/status from the week table when present; the variant list; freshness
      from the projection's `created_at`. 404 `no-players` when unpublished, 422 `invalid-request` for an unknown
      variant; requires sign-in like the other views.
      Verify: `uv run pytest -q apps/api/tests/test_players.py` → 5 passed
- [x] AC2: the committed OpenAPI contract and the generated TS types include `/players` (no drift).
      Verify: `uv run pytest -q apps/api/tests/test_openapi.py` passes; `just api-client` leaves `git diff` empty
- [x] AC3: a 5th "Players" tab routes to `/players`; the list shows rank, headshot, name, team · positions, $ and
      tier, and the status badge when present; a failed headshot shows the player's initials.
      Verify: `apps/web/src/features/players/PlayersPage.test.tsx` (renders rows; image `error` → initials)
- [x] AC4: search is case- and accent-insensitive; position chips G / F / C filter (NBA positions like `F-C` match both); sort by
      rank, $, or a category; the strategy picker refetches with `variant`; search/position/sort/variant live in
      the URL query and survive a reload; an unknown `variant` in the URL falls back to `all`.
      Verify: PlayersPage tests (`jokic` → Jokić; chip filter; sort order; variant request URL; initial URL state)
- [x] AC5: tapping a player opens a detail dialog with per-game projection, FG%/FT%, games and minutes, category
      strengths (sign shown, not colour alone) and status; Escape closes it and focus returns to the row.
      Verify: PlayersPage tests (dialog role, Escape, focus return, Tab stays inside)
- [x] AC6: states: loading skeleton, 404 → "Player values aren't published yet" with what publishes them, other
      errors → message + Retry that refetches, no matches → "No players match" + Clear filters, no projection →
      "No projection yet".
      Verify: PlayersPage tests (one per state)
- [x] AC7: renders 50 rows, "Show more" adds 50, and "N players" reflects the filtered count; changing filters
      resets to the first 50.
      Verify: PlayersPage tests (120-player fixture)
- [x] AC8: the hosting CSP allows `https://cdn.nba.com` images and nothing else new.
      Verify: `apps/web/src/firebase.test.ts`
- [x] AC9: sample (demo) mode serves a players fixture, so the page works without the API.
      Verify: `apps/web/src/api/fixtures` test / `App.test.tsx` (Players tab renders in sample mode)

## Test requirements
API: contract tests with seeded parquet (tmp data root). Web: Vitest + Testing Library against a fake `ApiClient`;
TDD per AC. Phone-width layout and real-browser checks belong to WEB-008 (persona e2e).

## Evaluation requirements
n/a (presents stored model outputs; no new numbers are computed except FG%/FT% from stored makes/attempts).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/api/tests/test_players.py (5 tests incl. gzip) | 5 passed; real data: 589 players, 10 strategies, 0.22 s, 244 KiB before gzip |
| AC2 | test + command | apps/api/tests/test_openapi.py; `just api-client` → no diff | pass |
| AC3 | test | PlayersPage.test.tsx › "Players: list (AC3)" (3 tests: tab + row content, headshot → initials, pre-season nulls) | pass |
| AC4 | test | PlayersPage.test.tsx › "search, filters, sort, strategy (AC4)" (5 tests) | pass |
| AC5 | test | PlayersPage.test.tsx › "detail (AC5)" (3 tests: dialog, Escape, focus return, focus trap, no projection) | pass |
| AC6 | test | PlayersPage.test.tsx › "states (AC6)" (4 tests: 404, Retry, loading, no match + clear) | pass |
| AC7 | test | PlayersPage.test.tsx › "paging (AC7)" (120-player fixture: 50/100/120, reset on filter) | pass |
| AC8 | test | apps/web/src/firebase.test.ts (img-src exactly self, data:, lh3, cdn.nba.com) | pass |
| AC9 | test | PlayersPage.test.tsx AC3/AC4 tests run on `fixtureClient` (sample mode) | pass |

`just ci-local`: 431 passed, coverage 93.64 %; web: 41 tests, tsc, eslint, prettier clean.

## Implementation history
- 2026-10-02 — Started API work (tests + `/players` router) before refining the spec; the owner pointed out
  specs come first, so the spec above was written before any web code. API: `DataStore.read_parquet`,
  `fantasy_api/players.py`, schemas `PlayerProjection`/`PlayerRow`/`Players`; `test_players.py` 4 passed.
  Next: regenerate OpenAPI/TS (AC2), then the page TDD per AC3–AC9.
- 2026-10-02 — Web: `features/players/` (PlayersPage, PlayerDetail, Headshot, format), `usePlayers` with
  keepPreviousData, 5th tab, CSP img-src. 15 page tests written first. `tsc` caught a contract bug the
  runtime tests missed: pydantic's to_camel turns `fg3m` into `fg3M`, so the live detail would have crashed;
  pinned the alias + an API assertion. Added GZip (payload ~250 KB). Lint flagged setState-in-effect for paging;
  replaced with a render-time reset keyed on the filters. Lessons: lesson 35 (to_camel and digit-bearing names).

## Decisions
- Headshots from `cdn.nba.com/headshots/nba/latest/260x190/{id}.png` (public, the same id space as our
  `nba_player_id`); the browser loads them (residential IPs aren't blocked, unlike our cloud jobs, D-63).
- Positions come from NBA (`nba_position`: G/F/C combos), not Yahoo eligibility, until the league import lands.

## Known issues
- Reviewer (2026-10-02): the 5-tab bar is tight at 375 px (~72 px a tab); confirm in WEB-008's phone pass.

## Follow-ups
- WEB-008 persona e2e covers this page at phone width.
