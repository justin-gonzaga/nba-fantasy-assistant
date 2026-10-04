---
id: DRAFT-012
title: "Injury-robust minutes and games: 3-season inputs after a short season (G-26 B)"
epic: EP-15 Draft assistant
phase: 6
component: models
status: done
ready: true
size: M
autonomy: auto
gate: G-26
depends_on: [DRAFT-011]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, docs/evaluation/**]
standards: [ml, testing]
assignee: claude
created: 2026-10-02
completed: 2026-10-02
---
# DRAFT-012 — Injury-robust minutes and games

## Objective
Giannis Antetokounmpo projects at 27.8 minutes and 45 games because the minutes model (M1, ridge) leans on last
season's minutes per game (28.9 over 36 games, mostly injury-return games) and the games forecast weights last
season 0.5. The owner: "if he's healthy he would be top 10." A what-if (published projection, Giannis alone at 34 min
and 65 games) puts him around #17. DRAFT-011 (replacement-filled games) did not ship: the replay favoured durability.
G-26 B (owner, "do both"): make the minutes and games inputs robust to one short season, and ship only if the draft
replay doesn't get worse.

## Context to read (only these)
- `packages/models/src/fantasy_models/preseason/breakouts.py` (`features`, `training_rows`)
- `packages/models/src/fantasy_models/preseason/methods.py` (`window`, `expected_games`)
- DRAFT-011 (the IL replay it reuses), D-51, D-55, D-65

## Pre-registration (committed before any run)
One variant, no tuning:
- **Minutes input**: when a player played < 60 % of his team's games last season (`gp_frac_last < 0.6`, the D-55
  population threshold), the model's `mpg_last` input is replaced by `mpg_window` (the recency-weighted 3-season
  minutes per game already used as a feature). Applied identically in training rows and prediction rows, so M1 is
  retrained on the same definition.
- **Games**: expected games fraction = `0.35·gp₁ + 0.25·gp₂ + 0.15·gp₃ + 0.25` (three seasons, the history weights
  still summing to 0.75 as now) instead of `0.5·gp₁ + 0.1·gp₂ + 0.25`. Seasons a player didn't play count as 0, as now.
- **Ship rule (non-inferiority)**: on the DRAFT-011 replay with IL replacements (2025-26, leak-free, 40 drafts,
  seed 0, 3 IL slots), B − current all-play share has its 95 % CI lower bound **> −0.005**. Otherwise keep the
  current method.
- **Reported, not deciding**: the replay without replacements; the 2025-26 minutes MAE (all players, and players
  with `gp_frac_last < 0.6`); the top-25 before/after and Giannis's rank and $.

## User stories and edge cases
| Situation | Expected |
|---|---|
| Star coming off an injury season (Giannis) | minutes from the 3-season window, games from 3 seasons |
| Healthy regular (≥ 60 % games) | unchanged minutes input; games weights shift slightly |
| Second-year player (one prior season) | window = that season; gp₂ = gp₃ = 0 as now |
| Rookie | unchanged (rookie path) |

## Acceptance criteria
- [x] AC1: `features(..., injury_robust=True)` swaps `mpg_last` for `mpg_window` exactly when `gp_frac_last < 0.6`.
      Verify: `uv run pytest -q packages/models/tests/test_breakouts.py -k injury_robust`
- [x] AC2: `expected_games(..., three_season=True)` uses the pre-registered weights.
      Verify: `uv run pytest -q packages/models/tests/test_methods.py -k three_season`
- [x] AC3: the replay command runs B vs current and writes the report with the ship decision by the rule.
      Verify: `docs/evaluation/reports/DRAFT-012-injury-robust.md`; a unit test of the decision/ordering guard
- [x] AC4: if shipped, the published values use the B method stamp and `/players` serves them.
      Verify: `/players` on the serve root → method contains `+robust`

## Test requirements
TDD with synthetic histories; the replay reuses DRAFT-011's tested IL logic.

## Evaluation requirements
The pre-registered replay above [R-54 bootstrap]; Marcel-style 3-season weighting [R-13].

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | packages/models/tests/test_breakouts.py::test_injury_robust_swaps_last_mpg_for_the_window_after_a_short_season | pass |
| AC2 | test | packages/models/tests/test_preseason.py::test_three_season_games_uses_the_preregistered_weights | pass |
| AC3 | report + test | docs/evaluation/reports/DRAFT-012-injury-robust.md: B − current with IL = **−0.1020** (95 % CI −0.1076 to −0.0965), B ahead in 0 of 40; without IL −0.0894; apps/pipeline/tests/test_draft_replay_run.py::test_robust_report_uses_non_inferiority | KEEP (rule not met) |
| AC4 | n/a | not shipped; published values unchanged | n/a |

## Implementation history
- 2026-10-02 — Pre-registered after DRAFT-011 (A) failed its ship rule and the owner chose "do both" (B + a
  healthy rank view, WEB-019).

## Decisions
- Result reading: both G-26 options lose on the 2025-26 replay; the current model's edge (DRAFT-010: +0.089 over
  Marcel) comes from trusting last season's minutes and games, and diluting either costs drafts. Caveat: one season;
  the CI covers draft-seat randomness, not season-to-season variation. Owner-facing remedies that don't change the
  model: the healthy rank (WEB-019) and per-player availability overrides (DATA-031) for news-based judgement.

## Known issues
_None._

## Follow-ups
_None._
