---
id: SIM-005
title: "Saved sims per user: practice drafts and replay leagues kept with the account"
epic: EP-17 Season replay
phase: 7
component: api
status: done
ready: true
size: M
autonomy: auto
gate: G-31
depends_on: [APP-009]
areas: [apps/api/**, apps/web/src/api/schema.gen.ts]
standards: [backend, testing, security]
assignee: claude
created: 2026-10-04
completed: 2026-10-03
---
# SIM-005 — Saved sims per user (API)

## Objective
A signed-in user's finished practice drafts and season-replay leagues are kept with the account, not the browser,
so they can be reopened on any device, compared over time, and continued (a replay season spans many sittings).
Each user sees only their own sims.

## Context to read (only these)
- APP-009 (`UserStore` port, CAS, `/me/...` routes); DRAFT-015 `features/draft/report.ts` (`RunSummary`)
- SIM-002 `features/replay/league.ts` (`ReplayLeague`)

## How people use it (drives retention)
- **Before the draft** (now to 18 Oct): many practice drafts, often 2–5 a day. People compare runs: "does punting
  FT% beat a balanced build?", "am I overspending early?" They need a sortable list of summaries (date, season,
  strategy, styles, score, category ranks, spend by phase) and can reopen any recent run's full report.
- **The best runs are references** ("my best balanced build") and are kept on purpose: pinned.
- **Season replay**: one league is played week by week over days, on phone and desktop, so it must resume
  anywhere. Finished leagues stay viewable (final record, weekly results) for comparison.
- **Privacy**: practice is personal. Never shared with other members; included in export; removed on delete.

## Retention (owner asked Claude to decide; reasons above)
| Kind | Kept | Why |
|---|---|---|
| Practice draft, full (summary + every sale) | the latest **30**, plus pinned | a fortnight of heavy practice; a full run is ~8 KB |
| Practice draft, summary only | the latest **200** (older full runs shrink to a summary) | trends over a season are cheap (~1 KB each) |
| Pinned practice drafts | up to **10**, never pruned | references; the 11th pin asks to unpin one |
| Replay leagues (draft + weekly results + moves) | up to **5**; the 6th asks to delete an old one (never silently) | each is a season-long project, ~30 KB |
| In-progress practice | 1 (resume), as now | a second start asks to discard it |

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Owner finishes a practice | the run is saved to the account; the list shows it at the top | offline / API down → kept locally and uploaded on the next load (idempotent by run id) |
| Owner on another device | the same list and reports | — |
| Owner pins a run | kept beyond the limits | 11th pin → 409 with why |
| Owner deletes one / all | gone from the account | deleting the active replay league asks first (web) |
| 31st full run | the oldest unpinned full run keeps only its summary | pruning happens in the same write (no cron) |
| Replay league saved from two tabs | compare-and-set on its version → 412 with the current copy | — |
| Member (invited friend) | sees only their own sims | another user's id → 404 (never 403: no existence leak) |
| Export / delete account | `/me/export` includes sims; `DELETE /me` removes them | — |
| Store not yet persistent (`users_backend=memory` until the owner's Firestore apply) | works, but resets on a deploy; the web keeps its local copy too | stated in Known issues |

## Acceptance criteria
- [x] AC1: `POST /me/sims` saves a practice run or replay league (idempotent by client id), `GET /me/sims` lists
      the caller's summaries newest first (filter by kind/season), `GET /me/sims/{id}` returns one, `DELETE` removes.
      Verify: `apps/api/tests/test_sims.py` (save, idempotent re-save, list, get, delete, another user's → 404)
- [x] AC2: retention per the table: summary-only pruning after 30 full runs, 200 summaries, 10 pins, 5 leagues
      (6th → 409 `too-many-leagues`), pinned never pruned.
      Verify: `test_sims.py::test_retention_*`
- [x] AC3: replay leagues update with compare-and-set (`If-Match`; 412 with the current copy; 428 without).
      Verify: `test_sims.py::test_league_cas_*`; `test_users_store.py` contract (memory + Firestore emulator)
- [x] AC4: export includes sims; deleting the account deletes them; payloads are size-capped (413 over 256 KB) and
      validated (422 names the field).
      Verify: `test_sims.py::test_export_and_delete`, `::test_limits`

## Test requirements
In-memory store + Firestore emulator contract tests; frozen clock; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | API | `apps/api/tests/test_sims.py::test_save_list_get_delete`, `::test_resaving_the_same_id_is_idempotent`, `::test_another_users_sim_is_404`, `::test_sims_need_sign_in` | pass |
| AC2 | unit + API | `test_sims_rules.py` (30 full → summary, 200 cap, pins never pruned, 10 pins, 5 leagues, idempotent) 7/7; `test_sims.py::test_retention_*` (trim in the same write, pin 409, league 409) | pass |
| AC3 | API + store contract | `test_sims.py::test_league_cas_update_and_stale`, `::test_league_cas_needs_if_match_and_a_league`; `test_users_store.py::test_sims_mutate_atomically_and_go_with_the_user` (memory; Firestore on the CI emulator: one transaction, reads before writes, nested arrays survive as JSON text) | pass |
| AC4 | API | `test_sims.py::test_export_and_delete`, `::test_limits` (422 names id/season/summary, 413 over 256 KB, nothing saved) | pass; `api` 147 passed, 10 skipped (emulator); ruff + mypy clean; OpenAPI + TS types regenerated |

## Implementation history
- 2026-10-04 — Specified from the owner's request ("the user signed in should be able to view previous sims";
  retention left to Claude). Storage follows D-64 (the users store, Firestore when applied): no new technology.
- 2026-10-04 — Built: `users/sims.py` (pure rules: `prune`, `plan_save`, `plan_pin`), one atomic store primitive
  `mutate_sims(uid, decide)` (a lock in memory, a transaction in Firestore over `sims/{uid}:{id}`), routes in
  `users/sims_routes.py` (`GET/POST /me/sims`, `GET/PUT/DELETE /me/sims/{id}`, `PATCH …/pin`), export includes
  sims, deleting the account deletes them in the same transaction. CORS allows PUT. Housekeeping outside
  `areas:`: APP-009 marked done (merged in #123; its task close was left over) and the board regenerated.
- 2026-10-04 — Review PASS; every route now checks the id's shape (404 for a malformed one).

## Decisions
- Retention as tabled above (owner delegated, 2026-10-04).

## Known issues
- Until `users_backend=firestore` (the owner's Terraform apply), saved sims live in the API's memory and reset on a
  deploy; SIM-006 keeps a local copy and re-uploads, so nothing is lost on the device that made them.

## Follow-ups
_None._
