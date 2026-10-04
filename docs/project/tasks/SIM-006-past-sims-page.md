---
id: SIM-006
title: "Past sims page: compare practice drafts, reopen reports, continue replay leagues"
epic: EP-17 Season replay
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: G-31
depends_on: [SIM-005, SIM-002]
areas: [apps/web/**]
standards: [frontend, testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-03
---
# SIM-006 — Past sims page

## Objective
One place to see past sims: practice drafts (compare and reopen) and replay leagues (continue or review), synced
with the account (SIM-005) and usable on a phone between practice runs.

## Context to read (only these)
- SIM-005 (API, retention); DRAFT-015 `features/draft/report.ts`; SIM-002 `features/replay/league.ts`;
  design-language §9

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner opens Past sims | two tabs: Practice drafts (score, strategy, season, date, spend, best/worst categories) and Season replays (season, record so far, week reached) | none yet → an empty state pointing to Draft practice |
| Comparing runs | sort by date or score; filter by strategy and season; a small trend of score over the last runs | one run → no trend line, just the value |
| Reopen a run | the full DRAFT-015 report (read-only) | a summary-only run (older than 30) says the full report was trimmed |
| Pin / delete | pin keeps it; delete asks in-page (no `confirm()`) | 11th pin → why, and which to unpin |
| Continue a replay | opens the matchup simulator at the next unplayed week | 6th league → choose one to delete first |
| First sign-in after DRAFT-015 | the browser's local history (last 10) is uploaded once, without duplicates | upload fails → retried next load |
| API down | the local copy is shown, marked "not synced" | — |
| Phone | one column, list → detail | — |

## Acceptance criteria
- [x] AC1: list, sort, filter and trend for practice drafts; replay leagues with record and week; empty state.
      Verify: `PastSims.test.tsx` › "list", "sort and filter", "empty"
- [x] AC2: reopen (full or trimmed), pin (limit), delete (in-page confirm), continue a replay.
      Verify: `PastSims.test.tsx` › "reopen", "pin", "delete", "continue"
- [x] AC3: sync: finished practices and replay results save to the account; local history migrates once (no
      duplicates); offline shows the local copy marked not synced.
      Verify: `sync.test.ts`; e2e `past-sims.spec.ts` (phone + desktop, axe)

## Test requirements
Vitest with mocked API; persona e2e + axe; the §9 screenshot loop.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | component | `apps/web/src/features/sims/PastSims.test.tsx` › list (counts, trend with its numbers said), sort and filter, empty, signed out | pass |
| AC2 | component | › reopen (a finished draft is saved to the account and its full report reopens: 9 category ranks, the team), reopen trimmed (summary only, why), pin (10, then why), delete (in-page confirm, Keep keeps), continue a replay (opens /replay at week 1) | pass |
| AC3 | unit + e2e | `sync.test.ts` (queue → upload, offline stays queued, no duplicates, permanent 4xx dropped, history migrated once, league: the copy with more kept weeks wins across devices; a week kept offline reaches the account later through the merge, not a plain save; a 412 without the stored copy reads it first; a league deleted elsewhere is saved afresh); e2e `past-sims.spec.ts` on iphone-13, pixel-7, desktop-chrome with axe | 6/6; e2e 3/3, 0 serious/critical; web suite 349 pass, eslint + tsc clean |

## Implementation history
- 2026-10-04 — Specified from the owner's request (view previous sims when signed in).
- 2026-10-04 — Built: the draft report extracted as `ReportView` (a saved run keeps exactly what it shows: the
  report, the names it mentions, the team), `features/sims/sync.ts` (local queue first, then upload; idempotent by
  id; the old browser history migrates once; a league's copy with more kept weeks wins between devices), the
  `/sims` and `/sims/:id` pages, the http client's write methods (ETag/If-Match; a 412 carries the stored copy),
  sidebar links (Season replay, Past sims) and links from the draft setup for phones. Found and fixed in tests: a
  device with an older league and no ETag would have overwritten the newer one on its first save.
- 2026-10-04 — Review FAIL → fixed: a week kept offline was retried as a plain save, which keeps the stale stored
  copy (lost update, shown as synced). Leagues now retry from their own list through the full merge
  (`flushLeagues`, on Past sims and Season replay loads), a 412 without the stored copy reads it, and a league
  deleted elsewhere is saved afresh; unsynced leagues show "not synced yet". Regression tests added.
- 2026-10-04 — Re-review PASS (findings resolved; ReportView unchanged: DraftReport tests pass untouched). e2e past-sims,
  season-replay and draft-practice on 3 devices: 12/12.

## Decisions
_None._

## Known issues
- Until the owner's Firestore apply, the API keeps sims in memory (reset on deploy); this browser's queue re-uploads
  what it made, but runs made on another device since the last deploy are gone.

## Follow-ups
_None._
