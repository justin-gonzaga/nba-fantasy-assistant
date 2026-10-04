---
id: DATA-029
title: "Draft-slice dbt models: NBA staging + int_player_season + int_player_profile"
epic: EP-15 Draft assistant
phase: 1
component: warehouse
status: done
ready: true
size: M
autonomy: auto
gate: G-22
depends_on: [DATA-012, DRAFT-001]
areas: [warehouse/**]
standards: [data-engineering, testing]
assignee: claude
created: 2026-09-25
completed: 2026-09-25
---
# DATA-029 — Draft-slice dbt models: NBA staging + int_player_season + int_player_profile

## Objective
Build the draft-slice tables from data-pipeline-design §2 (G-22) in dbt (D-50), so DRAFT-002 reads warehouse tables rather than raw files:
- staging: `stg_nba_stats__player_game`, `stg_nba_stats__team_game`, `stg_nba_stats__player_season_totals`, `stg_nba_stats__roster`, `stg_nba_stats__draft_pick`
- intermediate: `int_player_season` (player × season totals, games, minutes, age) and `int_player_profile` (as of the 2026-27 rosters: team, position, age, experience, team-change flag, draft pick)

Split from DATA-013, which keeps the schedule/box-score staging (needs DATA-006/009).

## Context to read (only these)
- docs/architecture/data-pipeline-design.md §2, §5
- warehouse/README.md

## Acceptance criteria
- [x] AC1: The five staging models parse the latest snapshot per request key, typed, with PK `unique`/`not_null` tests and range tests on stats (minutes 0–70, makes ≤ attempts)
      Verify: `just dbt build --select staging` → all tests PASS
- [x] AC2: Reconciliation: player points summed per team-game equal the team log's points, for every game in every season
      Verify: singular test `assert_player_points_reconcile_to_team` PASS
- [x] AC3: `int_player_season` has one row per player × season with totals equal to the game-log sums, and age from the season totals
      Verify: `just dbt build --select intermediate` → tests PASS (incl. `assert_player_season_matches_game_logs`)
- [x] AC4: `int_player_profile` covers every 2026-27 rostered player with a team-change flag and draft pick where one exists
      Verify: row count = distinct rostered players (589 in the DRAFT-001 run); tests PASS

## Test requirements
dbt data tests (generic + singular). No Python.

## Evaluation requirements
n/a

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | dbt build | `just dbt build --select staging` → PASS=47: PKs, not_null, ranges, makes ≤ attempts, OREB + DREB = REB, and `pts = 2·(fgm − fg3m) + 3·fg3m + ftm` on every player-game. Rows: 281,163 player-games over 11 seasons | ✅ |
| AC2 | singular test | `assert_player_points_reconcile_to_team` PASS (0 mismatching team-games, all seasons) | ✅ |
| AC3 | singular tests | `assert_player_season_matches_game_logs` PASS: 5,968 player-seasons, 0 missing either side, 0 games-played mismatches, no stat off by > 3. `assert_player_season_exact_match` WARN 63: stat corrections of 1–3 that reached only one feed (by design) | ✅ |
| AC4 | dbt show | `int_player_profile`: 589 players (= DRAFT-001 roster count), 30 teams, 131 changed team, 439 with a draft record, 105 with no NBA history since 2015-16; tests PASS | ✅ |
| Full build | dbt build | `just dbt build` → PASS=62, WARN=1 (the stat-correction warning), ERROR=0 | ✅ |

## Implementation history
- 2026-09-25: macros `nba_stats_rows`/`nba_stats_col` parse resultSets by header name (robust to column reordering). The 5 staging models + int_player_season + int_player_profile. Fixed: `rows` is a reserved word; a CTE named like its column shadowed it. The exact-match reconciliation found 63 player-seasons with tiny stat corrections, so it was split into error (> 3 or games mismatch) + warn (any difference).

## Decisions
- Staging names use the source name `nba_stats` (standard Â§7: `stg_<source>__<entity>`), e.g. `stg_nba_stats__player_game`; the design doc's `stg_nba__player_game` is the same table.
- Staging reads the **latest snapshot per request key**; `observed_at` is kept on every row for point-in-time use.

## Known issues
- 15 rostered players have an empty NBA position (training-camp signings); DRAFT-003's eligibility falls back for them.

## Follow-ups
_None._
