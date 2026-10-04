---
id: ANL-010
title: "Measure team and coach effects on players and on our model's errors"
epic: EP-15 Draft assistant
phase: 7
component: evaluation
status: done
ready: true
size: M
autonomy: auto
gate: none
depends_on: [RSCH-009, DATA-038]
areas: [packages/evaluation/**, docs/evaluation/**, apps/pipeline/src/fantasy_pipeline/team_effects_study.py, apps/pipeline/src/fantasy_pipeline/cli.py]
standards: [ml, testing]
assignee: claude
created: 2026-10-03
completed: 2026-10-03
---
# ANL-010 — Team and coach effects: are they real, and does our model miss them?

## Objective
Answer with our own data before building anything:
1. How much of the season-to-season change in a player's minutes and per-minute production is explained by
   **team** and **head-coach** context?
2. Do the **current model's errors** (H1+aging+M1 backtests) line up with context changes: a new team, a new
   coach, a pace change, a high-usage teammate leaving?

If (2) is near zero, a team/coach feature cannot help, and EXP-004 is not run.

## Context to read (only these)
- `docs/research/lit-team-effects.md` (RSCH-009); DATA-038's staging models
- the pre-season backtest (`fantasy_evaluation.preseason_backtest`) for residuals

## Questions and designs
| Question | Design | Confounders handled |
|---|---|---|
| Q1 How big are team effects on per-36 rates and minutes? | share of the season-to-season change in per-36 PTS/REB/AST/3PM and in minutes explained by the new team-season (fixed effects, R²), against a permutation null (team labels shuffled, 200 draws), 2016-17 → 2025-26, players with ≥ 500 minutes both seasons | regression to the mean (changes, not levels); chance fit of many dummies (the permutation null) |
| Q2 Do movers change more than stayers, beyond regression to the mean? | movers design: change vs the model's prediction, movers vs matched stayers (age, role, prior minutes) | selection into trades (pre-trend check); regression to the mean (compare residuals, not raw changes) |
| Q3 Coaching changes | residuals of players whose opening-day team changed head coach in the off-season vs players whose team kept its coach (stayers only, so a trade isn't counted as a coach change) | roster turnover (usage freed is a separate flag in Q5); regression to the mean (residuals) |
| Q4 Pace | counting stats vs team pace change, per minute vs per possession | role change |
| Q5 Model residuals | regress the 2023-24 → 2025-26 projection residuals (per stat and fantasy value) on the context-change flags | multiple testing (pre-declared list; Holm correction) |

## Context flags (fixed before the analysis; all known at each season's draft)
For player i and target season t (team = the player's first team in t, i.e. the opening-day team):
- `moved`: team ≠ the player's last team in t−1.
- `new_coach`: the team's head coach in t ≠ its head coach in t−1 (`int_team_season_context.new_coach`; off-season
  changes only, unknown counts as no flag and is excluded from Q3).
- `pace_change`: pace of the team in t−1 minus pace of the player's last team in t−1 (both last season, so known at
  the draft; 0 for stayers).
- `usage_freed`: share of the team's t−1 field-goal attempts taken by players (attributed to their last t−1 team)
  who are not on the team's opening-day roster in t.
- Not used: anything measured during t (pace in t, the coach after a mid-season change).

Residuals: the shipped method (H1+aging+M1pre), leak-free per target (as in the DRAFT-009 replay), per-game stats
and a fantasy value score (`preseason_backtest.value_score`), actual minus projected, players with ≥ 20 games.
Q1 uses fixed effects and a permutation null instead of mixed models (no mixed-model library in the workspace;
adding one isn't needed for this question).

## Acceptance criteria
- [x] AC1: the report `docs/evaluation/reports/ANL-010-team-coach-effects.md` gives effect sizes with 95 % CIs for
      Q1–Q5, and the share of residual variance explained by context (Q5).
      Verify: the report + `test_team_effects.py` (synthetic data: a planted effect is recovered; with no
      planted effect the CI covers 0)
- [x] AC2: a pre-declared go/no-go for EXP-004. **Go** if any context flag explains ≥ 2 % of the fantasy-value
      residual variance with a Holm-adjusted p < 0.05 on 2023-24 → 2025-26; otherwise **no-go**, recorded with
      the numbers.
      Verify: the report's Decision section; this rule is committed here before the analysis runs
- [x] AC3: point-in-time: every feature used was available before each season's draft (as-of reader).
      Verify: `test_team_effects.py::test_no_future_context`

## Test requirements
Synthetic-data tests for each estimator (planted effect recovered; null case); a leakage test.

## Evaluation requirements
The go/no-go rule above (pre-registered). No model ships from this task.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | report + unit | `docs/evaluation/reports/ANL-010-team-coach-effects.md` (`fantasy team-effects-study`, dev warehouse, 1,298 player-seasons); `packages/evaluation/tests/test_team_effects.py` (planted effect recovered, null covers 0, Holm, permutation null) | Q1–Q5 with CIs; 7/7 tests |
| AC2 | decision | report § Decision; rule committed in `be7330e` before the study code (`f6d317f`) and the run | **NO-GO**: largest flag `moved` explains 0.23 % (Holm p 0.33); all four together < 0.4 % |
| AC3 | unit + review | `test_team_effects.py::test_no_future_context` (pace in t can't leak); review found `new_coach` uses the end-of-season coach of t (a mid-season firing leaks in), so AC3 holds for 3 of 4 flags; a sensitivity run without `new_coach` is in the report | met with a documented exception |

## Implementation history
- 2026-10-03 — Specified from the owner's request; the go/no-go rule fixed before any data is looked at.
- 2026-10-03 — Flag definitions and designs committed (`be7330e`), then the estimators (pure, tested on synthetic
  data) and the study job (`f6d317f`), then the run. Findings: a new team does explain part of a player's raw
  per-36 change (R² 3–9 points above chance for PTS/REB/AST/3PM), but the shipped projection's errors don't line
  up with the context flags (moved 0.23 %, new coach 0.02 %, pace change 0.01 %, usage freed 0.06 % of the
  value-residual variance). Movers came in slightly under projection (−0.24 value, p 0.09, not significant).
  Decision: NO-GO; EXP-004 is not run.
- 2026-10-03 — Review FAIL: `new_coach` leaks mid-season firings and the caveat said the opposite. Fixed the
  caveat and docstring, added a sensitivity run without `new_coach` (labelled as not pre-registered), and added
  the study job and CLI (`apps/pipeline`) to `areas:` (the study needs the warehouse and the replay's projection,
  which live in the pipeline app).

## Decisions
_None yet._

## Known issues
- Coach effects and roster changes are entangled (new coaches often arrive with new rosters). The report says
  how well each design separates them.
- `new_coach` is not strictly point-in-time: DATA-038's source records the end-of-season coach, so a coach fired
  during t counts as new for t. The leak can only favour finding an effect; the result is NO-GO with and without
  the flag (sensitivity run in the report).
- OLS uses classical (homoskedastic) standard errors; fine for this screen, revisit if EXP-004 is reopened.

## Follow-ups
- EXP-004 runs only on "go" (NO-GO, 2026-10-03: not run).
