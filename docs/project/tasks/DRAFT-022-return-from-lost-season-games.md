---
id: DRAFT-022
title: "Project games for players returning after a lost season (the Lillard case)"
epic: EP-15 Draft assistant
phase: 6
component: models
status: done
ready: true
size: M
autonomy: review
gate: G-32
depends_on: [DRAFT-012, DATA-036]
areas: [packages/models/**, packages/evaluation/**, apps/pipeline/**, apps/api/**, apps/web/src/features/players/**, docs/evaluation/**, docs/architecture/ml-methodology-plan.md]
standards: [ml, testing]
assignee: claude
created: 2026-10-04
completed: 2026-10-04
---
# DRAFT-022 — Games for players returning after a lost season

## Objective
The owner (2026-10-04): "the model predictions do not account for players coming back from injury. Damian Lillard is
definitely more than $1 because he is coming back from injury even though he missed past season."

Diagnosis (read from `data/predictions/preseason_projection.parquet`, 2026-10-04): Lillard's per-game line is
fine (35.7 mpg, 23.4 pts, 6.9 ast, 3.2 3PM) but his **projected games are 26.3 of 82 (32 %)**, so his season total is
a third of a healthy season and the board prices him at **$1, rank 221**. The games forecast weights last season at
0.5 (`expected_games`); a season of 0 games counts as "0 % durable", with no notion that a missed season is an
injury gap that has ended. Two earlier attempts to fix a *similar* complaint (Giannis) by changing inputs for all
short-season players lost the draft replay (DRAFT-011 replacement fill; DRAFT-012 three-season inputs, −0.10 all-play
share), and DATA-036 (cited per-player raise rows) was the answer there. This task tests a **narrower** rule that
targets only the "lost season" cohort, on evidence, and ships only if the pre-registered rule passes.

## Context to read (only these)
- `packages/models/src/fantasy_models/preseason/methods.py` (`expected_games`), `breakouts.py` (`features`)
- DRAFT-011, DRAFT-012 (the replay harness and its non-inferiority rule), DATA-036, D-65
- `docs/architecture/ml-methodology-plan.md` (the amendment goes here), G-23 (precedent for amendments)

## Pre-registration (committed before any run; no tuning)
**Cohort ("lost season")**: a player-season (s) where, in the previous season, `gp_frac < 0.25` (games played ÷
team games) and, the season before that, `gp_frac ≥ 0.6` and `mpg ≥ 22`. The thresholds are round numbers chosen from
the shape of the problem (an essentially absent season after a rotation-level one) and are frozen here; they are **not**
tuned on outcomes. Honest caveat: the exploratory count below used the same data the folds will test (including
2025-26), so the confirmation is a leak-free *procedure* on partly seen data, not a fresh sample; the replay check
(3) on 2025-26 is likewise not independent of the Lillard observation.

**Exploratory look (disclosed, not the test)**: while drafting this spec, the cohort was counted from
`leaguedashplayerstats` 2015-16 → 2025-26: **n = 62** player-seasons (2017-18 → 2025-26); the realised games
fraction in the return season has **mean 0.60 and median 0.62** (≈ 49 games), against the model's 0.32 for Lillard.
The confirmation below is a separate, leak-free, expanding-window test.

**Variant R (one variant)**: for a cohort player, `expected_games_frac = max(current, r̄_s)` where `r̄_s` is the mean
realised games fraction of cohort players in seasons **before s** (expanding window; needs ≥ 30 earlier cohort
player-seasons, else R does nothing). Raise-only, like DATA-036. Minutes and per-minute rates are unchanged (the
minutes model already uses the 3-season window). Overrides (DATA-031 caps, DATA-036 raises) apply after R, so a cited
"still out" row always wins.

**Ship rule (all three must hold, else keep the current method and use overrides)**:
1. **Accuracy** — expanding-window folds 2021-22 → 2025-26 (first fold with ≥ 30 earlier cohort rows; ≈ 30 holdout
   player-seasons): mean absolute error of the games fraction for cohort players, R vs current; the paired bootstrap
   95 % CI of (current − R) is entirely above 0 [R-54].
2. **Calibration** — across those folds, |mean predicted − mean realised| games fraction for cohort players ≤ 0.08.
3. **Non-inferiority** — on the DRAFT-011 replay with IL replacements (2025-26, leak-free, 40 drafts, seed 0, 3 IL
   slots), R − current all-play share has a 95 % CI lower bound **> −0.005**.

**Power expectation (stated up front)**: the folds hold about 30 holdout player-seasons in total. If the base rate is
near the observed 0.60 and the current method predicts about 0.3 to 0.4 for these players, the error gap is large
relative to its spread and the CI should clear 0; if it does not, the correct outcome is "no ship" and the owner uses
cited override rows. A non-significant result is reported as inconclusive, not as support for R.

**Reported, not deciding**: Lillard's rank and $ before/after (a fact to report, **not a target to tune to**); the
top movers; the subgroup aged ≥ 33 (realised vs predicted); players in two consecutive lost seasons (excluded from
the cohort, reported); the replay without IL replacements.

## User stories and edge cases
| Situation | Expected |
|---|---|
| Star missed all of last season, healthy before (Lillard) | games raised to the cohort base rate; per-game line unchanged; value rebuilt |
| Missed 20 % of last season (gp_frac 0.20), healthy before | in the cohort (< 0.25): treated the same |
| Missed 40 % of last season (gp_frac 0.60) | **not** in the cohort: current method (DRAFT-012 found changing these hurts) |
| Never played before (rookie), or only one prior season | not in the cohort (needs `gp_frac ≥ 0.6, mpg ≥ 22` two seasons back) |
| Two lost seasons in a row | not in the cohort; reported |
| A cited "out" row (DATA-031) for a cohort player | the cap wins over R (a news fact beats a base rate) |
| A cited "cleared" row with `expected_games` (DATA-036) | the raise wins over R if higher; otherwise R stays |
| Owner opens the player | the detail says why: "Missed most of 2025-26; projected N games from players in the same situation (n, mean)" — from structured fields only |
| Fewer than 30 earlier cohort rows | R does nothing; the method stamp shows no `+return` |

## Acceptance criteria
- [x] AC1: `cohort(history, season)` returns exactly the players meeting the pre-registered definition, on synthetic
      histories (boundary cases: 0.25 / 0.6 / 22 mpg exactly, rookie, two lost seasons).
      Verify: `uv run pytest -q packages/models/tests/test_returners.py -k cohort`
- [x] AC2: `base_rate(history, season)` uses only seasons before `season`, returns `None` below 30 rows, and
      `expected_games(..., returners=True)` is raise-only.
      Verify: `uv run pytest -q packages/models/tests/test_returners.py -k "base_rate or raise_only"` (includes a
      leakage test that mutates season ≥ s and sees no change)
- [x] AC3: the evaluation command runs the three checks, writes the report with the numbers and the ship decision by
      the rule, and a unit test guards the decision logic (including "one check fails → keep current").
      Verify: a new `returners-eval` subcommand in `apps/pipeline/src/fantasy_pipeline/cli.py` (module `returners_report.py`,
      like the existing `*_run` / report modules) writes `docs/evaluation/reports/DRAFT-022-returners.md`;
      `uv run pytest -q apps/pipeline/tests/test_returners_report.py`
- [x] AC4: if shipped: the daily build uses R before overrides, the method stamp gains `+return`, and each affected
      row carries `returning = {lastGames, baseRate, n}` in `/players`; the player detail shows the explanation line.
      If not shipped, this AC is marked n/a with the report as evidence. **n/a: not shipped (check 3 failed).**
      Verify: `uv run pytest -q apps/api/tests -k returning`; `PlayerDetail.test.tsx` › "returning explanation";
      `/players` on the serve root → `method` contains `+return`
- [x] AC5: the methodology plan has the amendment (component card: cohort, variant, folds, ship rule, [R-xx]) and the
      gate G-32 is APPROVED before any evaluation code runs.
      Verify: `docs/architecture/ml-methodology-plan.md` §amendments; `python tools/tasks.py gates` shows G-32 APPROVED

## Test requirements
TDD with synthetic histories. Leakage test (AC2). The evaluation reuses DRAFT-011's tested IL replay and DRAFT-012's
decision guard. No network.

## Evaluation requirements
The pre-registered checks above. Grounding: Marcel-style multi-season weighting and regression to the mean [R-13]
(a practitioner source: it supports using a population base rate for sparse individual evidence, not this exact rule,
which is why the rule is tested rather than assumed); paired bootstrap [R-54]; verified entries only (ML standard §0). The researcher cites any new injury-return paper
into `docs/research/` first (e.g. return-to-play literature) and marks it verified or drops it.

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | `uv run pytest -q packages/models/tests/test_returners.py -k cohort` | pass (22 passed across both new test files) |
| AC2 | test | `-k "base_rate or raise_only"` incl. leakage test | pass |
| AC3 | report + test | `returners-eval --drafts 40` wrote `docs/evaluation/reports/DRAFT-022-returners.md`; `test_returners_report.py` | pass; decision KEEP current: accuracy pass (CI +0.013..+0.139), calibration pass (gap 0.063), replay non-inferiority FAIL (CI low -0.0103 vs > -0.005) |
| AC4 | n/a | report above | not shipped; R is not wired into the daily build. Lillard/Giannis remain the cited-override route (DATA-036) |
| AC5 | doc + gate | `ml-methodology-plan.md` Part 1d; `tasks.py gates` | G-32 APPROVED 2026-10-04 before any run |

## Implementation history
- 2026-10-04 — Specified from the owner's Lillard complaint. Priority P0 for the draft on Sun 18 Oct: the evaluation
  (AC3) must finish by Thu 15 Oct, which needs G-32 approved by about Wed 7 Oct (implementation and the run take
  roughly a week); otherwise the board keeps the current method and the owner adds cited override rows.

- 2026-10-04 — Implemented and run (40 drafts). R is more accurate and calibrated but did not clear replay non-inferiority, so by the pre-registered rule the current method stays; nothing shipped.

## Decisions
- A narrow cohort rule rather than re-opening DRAFT-012: that test changed inputs for every short-season player
  (including partial seasons, where durability is informative) and lost clearly. This one touches only players who
  were absent for essentially the whole previous season.
- Raise-only, and overrides still win: a base rate must never override a cited fact.
- Gate G-32 because it changes the projection method (G-19 / G-23 precedent): the owner approves the
  pre-registration, not the outcome.

## Known issues
- Only two seasons of NBA injury reports are on disk (2024-10 onwards), so the cohort is defined from games played
  alone; an injured/not-injured split is out of scope until more history exists.
- Age: Lillard is 36 in 2026-27; the cohort is mostly younger. The ≥ 33 subgroup is reported; no age term is fitted.

## Follow-ups
- A cited `cleared` override row for Lillard (DATA-036) is the immediate, independent route if a source is found; it
  needs the owner's review of the quote.
- In-season returners (back after weeks out) are handled by the in-season availability adjustment (ANL-009), not here.
