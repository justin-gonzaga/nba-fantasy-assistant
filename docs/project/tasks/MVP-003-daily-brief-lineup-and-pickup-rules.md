---
id: MVP-003
title: "Daily brief: lineup and pickup rules"
epic: EP-12 In-season MVP
phase: 5
component: mvp
status: done
ready: true
size: S
autonomy: auto
gate: G-01
depends_on: [MVP-001]
areas: [packages/decision/**, apps/pipeline/**]
standards: [software-engineering, testing]
assignee: claude
created: 2026-09-28
completed: 2026-09-27
---
# MVP-003 — Daily brief: lineup and pickup rules

## Objective
Rules over the rest-of-week table: start/bench (no game today, Out), questionable check times, free agents ranked by expected category gain where the week is close. A thin slice of DEC-007/DEC-008.

## Context to read (only these)
- docs/project/STATUS.md (MVP plan)

## Acceptance criteria
- [x] AC1: Lineup rules and a pickup ranking, tested on a sample league
      Verify: packages/decision/tests
- [x] AC2: Markdown brief rendered from structured evidence only (no free text)
      Verify: golden test

## Test requirements
TDD; offline tests with fixtures.

## Evaluation requirements
Baselines only (no new ML); anything measured is reported with CIs.

## Evidence
| AC | Kind | Reference | Result |
|---|---|---|---|
| AC1 | tests | packages/decision/tests/test_brief.py (9): bench no-game/Out, flag Questionable, slot filling, category win probabilities (TO reversed), pickups vs an opponent and without one; apps/pipeline/tests/test_daily_brief.py (3) | ✅ |
| AC2 | test + dry run | render uses structured values only, fits one Telegram message; live dry run on a snake-draft sample league for Wed 21 Oct: matchup 5.1 of 9 expected, 14-man lineup (5 without games benched), 5 pickups with category reasons | ✅ |

## Implementation history
- 2026-09-28: `fantasy_decision.brief` (lineup, normal-approximation category win probabilities, pickup gain in expected category wins) and `fantasy_pipeline.daily_brief` + CLI `brief` (league file, sample league). The dry run found that the backfilled old reports were being picked as "latest": fixed by using today's report (`injury_report.stored_report`).

## Decisions
- MVP plan (owner, 2026-09-27): a daily Telegram brief from tip-off (20 Oct), baselines only.

## Known issues
- Lineup is greedy by player value, not an optimiser (DEC-007). Win probabilities use Poisson/binomial variances (no game-to-game overdispersion yet).
- The opponent and league rosters come from a hand-maintained league file until the Yahoo import (DISC-011/DATA-026).

## Follow-ups
_None._
