---
id: RSCH-008
title: "Are in-season trends real? Second-half splits, late-season rest/tanking, playoff schedule"
epic: EP-15 Draft assistant
phase: 6
component: evaluation
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DRAFT-012]
areas: [packages/evaluation/**, apps/pipeline/**, docs/evaluation/**, docs/research/**]
standards: [ml, testing]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# RSCH-008 — In-season trends and the fantasy-playoff schedule

## Objective
The owner (2026-10-02): "Do we also take into account trends throughout the season? Some players play better at the
start, some after the All-Star break." The draft values are one number per season; the in-season EB update (D-61,
ANL-005) adapts to sustained changes after they appear. This spike measures, on our own game logs, which calendar
effects are real and large enough to matter, before any model change. Anything that survives becomes a separate,
pre-registered model task.

## Context to read (only these)
- `docs/architecture/ml-methodology-plan.md` Part 2 §14 (in-season EB update) and the common evaluation
- `docs/research/ml-literature-review.md` (cite only verified `[R-xx]`; new sources via the `researcher` agent)
- League settings: playoffs weeks 18–20 (ends Sun 21 Mar), 6 teams (`data/samples/yahoo/league_settings.txt`)

## Questions and pre-registered analyses (fixed before looking)
Data: player game logs 2015-16 … 2025-26 (warehouse), players with ≥ 20 games in each half. "Half" = before / after
the All-Star break date of that season. Value = 9-cat per-game z-sum (`breakouts._zsum` definition).

**Q1. Is a "second-half player" a repeatable trait?** For each player-season, Δ = second-half minus first-half
per-game value (also per-minute, to separate role from skill). Statistic: correlation of Δ in season s with Δ in
s+1 (same player), pooled, with a bootstrap CI over players [R-54]. **Decision rule**: if the CI includes 0 or
r < 0.15, treat individual split tendencies as noise and do not model them.

**Q2. Late-season rest and tanking.** Per player-game after 1 Mar: minutes and games-played share vs the same
player's pre-1 Mar rates, grouped by (a) team context on 1 Mar (playoff-locked top seeds, mid-race, eliminated or
bottom-6 teams) × (b) role (top-60 value stars vs rotation players vs age ≤ 23 on bottom-6 teams). Report effect
sizes with CIs. **Decision rule**: an effect ≥ 2 games missed or ≥ 3 mpg change, with a CI excluding 0, is
"material" and gets a model task.

**Q3. Fantasy-playoff schedule.** For 2026-27, games per NBA team in league weeks 18, 19 and 20 (from the published
schedule). Recompute draft values with those weeks weighted (each playoff week = w × a regular week, w ∈ {1, 2, 3}
reported, none chosen here). Report how many top-150 players move ≥ 10 ranks and the $ shifts. **Decision rule**: if
w = 2 moves ≥ 15 of the top 150 by ≥ 10 ranks, a pre-registered DRAFT task evaluates playoff weighting on the replay.

## User stories and edge cases
| Situation | Handling |
|---|---|
| Player traded mid-season | halves are by date, team context by the team on 1 Mar |
| Short half (< 20 games) | excluded from Q1/Q2 (reported count) |
| 2019-20 (COVID suspension) and 2020-21 (72 games, no normal ASB timing) | reported separately and excluded from pooled estimates |
| Schedule not yet published for a week | Q3 stops with a clear message; no guessed games |

## Acceptance criteria
- [x] AC1: Q1 computed exactly as pre-registered, with n, r and bootstrap CI, and the decision stated.
      Verify: `docs/evaluation/reports/RSCH-008-in-season-trends.md` § Q1; unit test of the split/Δ computation on synthetic logs
- [x] AC2: Q2 effect table with CIs per group and the decision per group.
      Verify: report § Q2; unit test of the team-context classification on a synthetic standings table
- [x] AC3: Q3 playoff-week games per team and the rank-movement table for w ∈ {1, 2, 3}, with the decision.
      Verify: report § Q3; unit test that w = 1 reproduces the current values exactly
- [x] AC4: follow-up tasks created only for decisions that passed, each with its own pre-registration.
      Verify: task files linked in *Follow-ups* (or "none passed")

## Test requirements
Synthetic logs for the computations (TDD); the real run reads the warehouse.

## Evaluation requirements
The pre-registered rules above; bootstrap CIs [R-54]. Literature on second-half effects / load management to be
added via the `researcher` agent before the report (cite only verified entries).

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | report + test | docs/evaluation/reports/RSCH-008-in-season-trends.md § Q1: 827 player-pairs; per-game r = +0.081 (CI +0.017 to +0.146), per-36 r = +0.025 (CI −0.046 to +0.093) → **noise** by the rule (r < 0.15); tests packages/evaluation/tests/test_season_trends.py (split, ASB, persistence on a planted trait vs noise, consecutive pairs) | pass |
| AC2 | report + test | report § Q2: material for bottom-6 stars (+6.2 extra games), bottom-6 rotation (+3.7), contender stars (+2.4), young on bottom-6 (+4.3 mpg); tests ::test_team_context_groups_by_win_pct, ::test_late_season_measures_missed_games, ::test_material_rule | pass |
| AC3 | report + test | report § Q3: playoff-week games 9–12 per team; w = 2 moves 0 of the top 150 by ≥ 10 → not material; tests ::test_playoff_weight_one_reproduces_the_current_ranks, ::test_rank_changes_are_signed, apps/pipeline/tests/test_trends_study.py | pass |
| AC4 | task | ANL-009 created for Q2 (the only material result); none for Q1/Q3 | pass |

## Implementation history
- 2026-10-02 — Specified and pre-registered from the owner's question.
- 2026-10-03 — **Pre-run amendments (before any result was computed)**, forced by the data:
  1. The game logs carry no conference, so Q2's team context uses a league-wide proxy on 1 Mar: win % rank
     1–4 = "contender" (likely seed-locked), 25–30 = "bottom-6", the rest = "mid-race".
  2. All-Star break date per season = the first day of the longest league-wide gap with no games between 1 Feb
     and 15 Mar (computed from the logs).
  3. Q1/Q2 per-game value = the 9-cat z-sum of a player's per-game line within that season and half (the
     `breakouts._zsum` definition, per game played); age ≤ 23 from `int_player_season`.
  4. Q2 effect sizes: games missed = (pre-1 Mar share of team games − post share) × team games after 1 Mar;
     mpg change = post − pre mpg; players with ≥ 10 games before and a team with ≥ 10 games after 1 Mar.
  5. Q3 weighting: playoff weeks = league weeks 18–20 = Mon 1 Mar – Sun 21 Mar 2027 (settings: ends Sun 21 Mar).
     Weighted value = value × (1 + (w − 1) × P/S), with P = the player's team's games in those weeks and S = the
     team's season games (82), i.e. the share of his season played in the playoff weeks gets w× weight.
- 2026-10-03 — Ran on 11 seasons of logs. **Bug caught before reporting**: Q3 rank changes used unsigned ints, so
  fallers wrapped to 4294967295 and inflated "moved ≥ 10" to 19 (would have triggered a model task); fixed (signed,
  tested), corrected result 0 → not material. Literature R-106…R-109 via the researcher agent. Lessons: lesson 38.

## Decisions
- Review: evidence figures copied verbatim from the committed (final-code) report; the first run's CIs differed
  slightly in the third decimal because the report was regenerated after the code cleanup.

## Known issues
_None._

## Follow-ups
- ANL-009 late-season availability adjustment (from Q2).
