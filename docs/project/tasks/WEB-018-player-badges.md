---
id: WEB-018
title: "Player badges: breakout, bounce-back, injury history, rookie, top tier"
epic: EP-70 Dashboard
phase: 7
component: web
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [WEB-017]
areas: [apps/web/**, apps/api/**, apps/pipeline/src/fantasy_pipeline/**]
standards: [frontend, design, backend]
assignee:
created: 2026-10-02
completed: 2026-10-02
---
# WEB-018 — Player badges

## Objective
The owner (2026-10-02): "in the UI players page, there should be icons, e.g. potential breakout, injury prone, all
star, etc." Each badge is an icon + a word, and each one comes from stored evidence (explanations standard: no
invented facts), with a one-line "why" in the player detail.

## Context to read (only these)
- `docs/standards/design-language.md` (Badge), D-55/D-57 (the breakout flags' ship rule)
- `docs/evaluation/reports/DRAFT-007-backtest.md`, `DRAFT-008-backtest.md` (what passed)
- `apps/api/src/fantasy_api/players.py`

## Badge rules (evidence first)
| Badge | Shown when | Evidence source | Why line (detail) |
|---|---|---|---|
| **Breakout chance** (spark) | growth-breakout probability in the top 20 % of the pool (the lift20 cut tested in DRAFT-008) | `predictions.breakout_probability` (ships per D-55/D-57) | "Breakout chance 34 % (pool top 20 %)" |
| **Bounce-back** (arrow-up-right) | bounce-back probability in the top 20 % | same table, M2a (DRAFT-007) | "Bounce-back chance 41 %" |
| **Injury prone** (bandage, lose tone) | in 2 of the last 3 seasons he was a rotation player (≥ 20 min per game played) yet played < 60 % of his team's games | `int_player_season` (games_played, season_team_games, minutes) | "Played 38, 19 and 39 of 82 games in the last three seasons" |
| **Missed time** (calendar-x, warn tone) | last season: rotation player who played < 60 % of team games, and not already Injury prone | same | "Played 36 of 82 games last season" |
| **Rookie** (sprout) | drafted in the target season's draft | `stg_nba_stats__draft_pick` | "2026 draft, pick 3" |
| **Top tier** (star) | tier 1 under the selected strategy | `auction_values.tier` | "Tier 1 of 6 for this strategy" |
| **Injured today** (exists as status) | today's injury report lists him | week projection `status_today` | "Questionable on today's report" |

**All-Star**: not shown in this task: we don't hold All-Star selections. Follow-up DATA-033 ingests NBA award
history (from the PC fetch, D-63); until then "Top tier" carries "elite" honestly. The owner may cancel DATA-033.

## User stories and edge cases
| Persona / situation | Story | Edge cases |
|---|---|---|
| Owner pre-draft | "Show me breakout candidates" | a "Badges" filter (multi-select chips) + badges in rows; the filter combines with search/position |
| Owner, phone | Reads a row | at most 2 badges in a row (priority: injured today > injury prone > missed time > breakout > bounce-back > rookie > top tier) then "+N"; all in the detail |
| Owner (2026-10-03) | "Tell me if a player is injury prone" | the injury badges replace the "Healthy #N" row hint (removed); the healthy rank stays as a sort and a detail line |
| Bench player with few games | Low games from not playing, not injury | seasons under 20 min per game don't count (real data: removed Collin Gillespie's false flag) |
| Screen reader | Hears a row | badges read as words ("Breakout chance"), not icon names |
| Data gaps | No breakout table published yet | breakout/bounce-back badges simply absent, a note in the detail ("Breakout model not published"), no error |
| Rookie with no history | | no injury badges (Injury prone needs 2 rotation seasons) |
| Missed games for other reasons (suspension, rest, personal) | | a known proxy limit: the why line states games, never claims an injury; injury-report history (only 2025-26 so far) can refine it later |

## Acceptance criteria
- [x] AC1: the pipeline publishes `predictions/breakout_probability.parquet` and `predictions/player_history.parquet`
      (games played vs team games, last 3 seasons; draft year/pick) to the serve root.
      Verify: `apps/pipeline/tests/test_publish.py::test_badge_inputs_are_published`
- [x] AC2: `/players` returns `badges: [{code, label, why}]` per player by the rules table, absent inputs → no badge.
      Verify: `apps/api/tests/test_players.py::test_badges_*` (one per rule + missing inputs)
- [x] AC3: rows show ≤ 2 badges + "+N" by priority; the detail lists all with why lines; a Badges filter works.
      Verify: `PlayersPage.test.tsx` (badges, overflow, filter)
- [x] AC4: badges use the design-language `Badge` (icon + word, tokens only).
      Verify: `design.test.ts` passes; Badge unit test

## Test requirements
API contract tests with seeded parquet; page tests with fixtures.

## Evaluation requirements
n/a (presents shipped model outputs and facts).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | delivered by DATA-035 (#95): apps/pipeline/tests/test_draft_publish.py::test_build_returns_the_three_tables_with_the_contract_columns, ::test_history_carries_one_draft_only_row_per_rookie; test_publish.py::test_draft_files_are_published_when_present; contract cross-checked by the DATA-035 reviewer | pass |
| AC2 | test | `uv run pytest -q apps/api` (`test_players.py::test_badges_*`, 14 tests: constants, each rule, last-3-seasons window, rookie season, top-fifth cut, latest season, priority, missing inputs + notes) | 49 passed |
| AC3 | test | `corepack pnpm exec vitest run` (`PlayersPage.test.tsx` "Players: badges": ≤ 2 + "+N", detail why lines, notes, filter + search, URL restore, clear; healthy hint removed) | 211 passed (14 files) |
| AC4 | test | `PlayerBadges.test.tsx` (Badge primitive, stroke icon 16/1.75, word only for screen readers, icon per code) + `design.test.ts` | passed; `pnpm typecheck` and `pnpm lint` clean |
| all | ci | `just ci-local` | 469 passed, coverage 93.53 % |

## Implementation history
- 2026-10-02 — Specified from the owner's request.
- 2026-10-03 — Injury rule refined on real data before building: "< 60 % in 2 of 3" alone flagged a bench player
  (Gillespie: 80, 33, 24 games); counting only rotation seasons (≥ 20 min) gives 6 Injury prone in the top 150
  (Embiid, Porziņģis, LaMelo Ball, Markkanen, Herro, Mark Williams) and 13 Missed time (Antetokounmpo, Tatum,
  Davis, Curry, Jalen Williams, …). The owner prioritised injury indicators over the healthy-rank hint (PR #94 closed).

- 2026-10-03 — API + web built (pipeline inputs left to DATA-035). `fantasy_api/badges.py` holds the rules
  and their constants (pinned by a test); `/players` returns `badges` (priority order) and `badgeNotes`
  (inputs not published). Rows show 2 badges + "+N", the detail lists all with why lines, a "Filter by badge"
  chip group (any chosen; URL `badge=`) combines with search and position. The "Healthy #N" row hint is removed
  (sort and detail sentence kept). Demo fixture has sample badges.

## Decisions
- Input contract for DATA-035: `predictions/player_history.parquet` (nba_player_id, season, games_played,
  season_team_games, minutes = season total, draft_year, overall_pick; a rookie with no seasons is one row with a
  null season) and `predictions/breakout_probability.parquet` (nba_player_id, kind, p_breakout, season; the latest
  season is used). The target season comes from `auction_values.season`; without it there is no Rookie badge and
  the history window is the latest 3 seasons in the file.
- The injury window is the 3 seasons right before the target (a missing season stays missing; the why line then
  names the seasons). Breakout/bounce-back cut: the top ceil(20 % × n) probabilities, ties included.
- The badge filter matches any chosen badge (OR); the detail header's "Today: status" badge moved into the
  Badges list ("Out on today's report").

## Known issues
- Review note: `PlayerRow.status` is still served (useful to other clients) but the row now shows it only as the
  "Injured today" badge.
- Growth-breakout probabilities aren't stored yet (only bounce-back), so "Breakout chance" stays absent until a task
  writes them.
_None._

## Follow-ups
- DATA-033 All-Star / awards ingest (optional).
