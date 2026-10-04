---
id: DATA-038
title: "Team and head-coach context by season, point-in-time"
epic: EP-20 Ingestion
phase: 7
component: ingest
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: []
areas: [packages/ingest/**, packages/dikit/src/dikit/store/**, packages/dikit/tests/**, apps/pipeline/**, warehouse/**, docs/research/nba-data.md]
standards: [data, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# DATA-038 — Team and head-coach context history

## Objective
ANL-010 needs, for every team-season since 2015-16 and for the coming season: the **head coach**, **team pace**,
offensive/defensive rating, and how concentrated the team's minutes and shots are. None of this is in the
warehouse today. Land it raw (immutable), stage it in dbt, and read it point-in-time, so a projection for 2026-27
sees only what was known before the draft.

**Source check (live, 2026-10-03)**: `commonteamroster` for a past season lists that season's head coach in its
`Coaches` result set (MIL 2019-20 Budenholzer, LAL 2019-20 Vogel), but only the **end-of-season** coach: MIL
2023-24 shows Doc Rivers, who replaced Adrian Griffin mid-season. So this task gives one head coach per
team-season (off-season changes are visible; mid-season changes are not). `leaguedashteamstats`
(MeasureType=Advanced) returns PACE, OFF_RATING, DEF_RATING for all 30 teams per season.

## Context to read (only these)
- `docs/research/nba-data.md` (sources; D-63: the PC fetches NBA data)
- `packages/ingest/src/fantasy_ingest/draft_pool.py` (plan → skip stored → fetch → store) and the
  `stg_nba_stats__roster` staging model as the pattern

## User stories and edge cases
| Persona / situation | Expected | Edge cases |
|---|---|---|
| Analyst (ANL-010) | one row per team-season: head coach (id, name), previous season's head coach and a `new_coach` flag, pace, ORtg, DRtg, the top-3 share of team minutes and of team FGA | a coach who moves teams keeps his id; the first season (2015-16) has no previous coach (flag null, not false); a relocated/renamed team keeps its team id |
| Projection as of the draft (2026-27) | the head coach listed in the latest roster snapshot taken before the cutoff, and last season's context | a coach hired after the cutoff is invisible to the draft projection (as-of read) |
| Mid-season coaching change | the season shows the end-of-season coach; documented as a limitation | ANL-010 treats mid-season changes as out of scope |
| Coach fired after the season | the source lists no head coach: coach unknown, `new_coach` null | 10 of 341 team-seasons (e.g. LAL and SAC 2015-16) |
| Source unavailable | the fetch fails loudly, raw stays untouched, the backfill resumes where it stopped | rate limits; the PC-only fetch (D-63) |

## Acceptance criteria
- [x] AC1: a resumable `team-context-backfill` lands `commonteamroster` for every team, 2015-16 → 2025-26, and
      `leaguedashteamstats` (Advanced) per season in `raw/` (immutable, with metadata), run on the PC per D-63.
      Verify: `test_team_context.py` (plan + run with a fake client) + the raw counts in Evidence
- [x] AC2: dbt `stg_nba_stats__head_coach`, `stg_nba_stats__team_season_advanced` and `int_team_season_context`
      with tests (at most one head coach per team-season; 30 teams with pace per season and ≥ 26 known coaches;
      pace within 90–110; shares within 0–1).
      Verify: `dbt build` output for these models in Evidence
- [x] AC3: point-in-time: `SnapshotStore.as_of(source, endpoint, key, t)` returns the latest snapshot observed at
      or before t, and the head coach read through it ignores a later snapshot.
      Verify: `test_snapshot.py::test_as_of*` (dikit) + `test_team_context.py::test_head_coach_as_of`
- [x] AC4: the sources, fields and the mid-season limitation are documented in `docs/research/nba-data.md`.
      Verify: section present

## Test requirements
Recorded fixtures (no network in tests); dbt tests; the as-of property test.

## Evaluation requirements
n/a (data). Coverage (team-seasons, stints, coach changes) recorded in Evidence.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | unit + live run | `packages/ingest/tests/test_team_context.py` (plan, resumable run with a fake client); `fantasy team-context-backfill` on the PC 2026-10-03 | fetched=341 skipped=0 (330 rosters + 11 team tables); synced to `gs://nbafa-hdfo-dev-raw` with `--no-clobber` |
| AC2 | dbt | `just dbt build --select stg_nba_stats__snapshots stg_nba_stats__head_coach stg_nba_stats__team_season_advanced int_team_season_context … assert_team_context_has_30_teams_each_season` | PASS=40 (incl. the new tests); 330 team-seasons, 30 per season, 320 coaches known, 61 off-season coach changes, pace 91.7–105.5, mean top-3 share 0.350 of minutes, 0.423 of FGA |
| AC3 | unit | `packages/dikit/tests/test_snapshot.py::test_as_of_*` (2); `test_team_context.py::test_head_coach_as_of_ignores_a_later_snapshot` | pass |
| AC4 | doc | `docs/research/nba-data.md` § Team and head-coach context | present (sources, fields, end-of-season and fired-after-season limits) |

## Implementation history
- 2026-10-03 — Specified for the team and coaching research (owner request).
- 2026-10-03 — Sources checked live first (spec rewritten: end-of-season coach only). Built `SnapshotStore.as_of`
  (platform), `team_context` (plan, head coach, as-of read, team advanced), the `team-context-backfill` command, a
  `result_set` option on the `nba_stats_rows` macro, two staging models and `int_team_season_context`. First run of
  the CLI failed on a missing import (nothing fetched); fixed and rerun. The 30-teams test then failed for 6
  seasons: the source lists no head coach when the coach was fired after the season (10 of 341). The model now
  starts from the team stats (always 30) with the coach left-joined, `new_coach` null when unknown.

## Decisions
- Verified live (2026-10-03): coaches per season come from `commonteamroster` (end-of-season head coach only).
  Mid-season stints would need another source; out of scope (ANL-010 studies off-season changes).
- The as-of read is a generic `SnapshotStore.as_of` (platform, project-agnostic), not a domain helper.

## Known issues
- No head coach for 10 of 341 team-seasons (coach fired after the season) and none for mid-season stints.
- 2026-27 has coaches (rosters captured 2026-09-25) but no team stats yet, so it is not in the intermediate model;
  a draft projection reads the coach with `head_coach_as_of` and last season's context.

## Follow-ups
_None._
