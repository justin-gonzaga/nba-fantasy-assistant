# Evaluation Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

Four separate questions, **never conflated**:
1. **Software correctness**: does the code do what it says? (unit/property tests)
2. **Data correctness**: is the data right? (DQ tests, reconciliation)
3. **Model performance**: are predictions accurate and calibrated? (walk-forward metrics)
4. **Recommendation quality**: do decisions create value? (replay + outcome scoring)

A model never counts as successful just because (1) and (2) pass.

## 1. Temporal validity
- **Walk-forward (rolling-origin)** only [R-50, R-51]. Random K-fold is banned for any time-indexed target.
- Folds are split on the **decision timestamp**, not the game date alone. The inputs for game *g* at lead time *L* are those observed at or before `tipoff(g) − L`.
- Standard lead times: T-24h, T-6h (the lineup-setting default), T-1h.
- Holdout: the most recent complete season, used only at promotion time.

## 2. Leakage checklist (reviewed in every ML PR) [R-60]
- [ ] No input has `observed_at > as_of` (enforced by the instrumented `AsOfReader` test)
- [ ] No box-score fields from the target game (starter flag, minutes)
- [ ] Rolling/season aggregates exclude the target game and later games
- [ ] The injury designation used is the report version available at the lead time, not the final one
- [ ] Yahoo ownership, FA pool, and rosters come from snapshots at or before `as_of`; no data from before snapshot collection started is used
- [ ] Opponent and team context stats exclude the target game
- [ ] The player universe as of `t` includes players who were later waived, retired, or traded (survivorship)
- [ ] Hyperparameters were tuned without touching the holdout

## 3. Metrics
| Output | Primary | Secondary |
|---|---|---|
| Point projections (per stat) | MAE | RMSE, skill score vs baseline, bias |
| Distributions | CRPS / pinball loss [R-41, R-22] | interval coverage, PIT histogram [R-44] |
| Probabilities | log loss, Brier [R-40, R-41] | ECE, reliability diagram [R-48] |
| Lineup decisions | realised Δ objective vs B1/B2 per team-day | % days better, % days worse |
| Add/drop/stream | realised Δ objective over the next 7 days vs "no move" and vs the best-FA-by-rank baseline | hit rate by confidence bucket |
| Matchup/season probabilities | Brier on category and matchup outcomes | calibration by format |

## 4. Uncertainty and significance
- Report 95 % CIs using a **paired block bootstrap** over dates (block = 7 days) [R-54, R-55]. Report Diebold–Mariano p-values for model comparisons [R-53].
- Compare models on **the same rows** (paired). Never compare metrics computed on different samples.

## 5. Baselines (the minimum set)
- **Projections**: last-10 average; season average; Marcel-style weighted average + shrinkage [R-13, R-11].
- **Availability**: the static designation → rate table.
- **Lineup**:
  - B1: the owner's actual lineup, when known.
  - B2: start all active players ranked by Yahoo's own rank.
  - B3: maximise games started (count only).
- **Waiver/streaming**:
  - "no move"
  - the top-ranked FA by Yahoo rank with a game
  - the best FA by G-score [R-01]

## 6. Historical replay (the decision-level backtest)
- `just replay --start --end --policy <engine|baseline>` runs the decision engine at each historical decision time through `AsOfReader`, and scores the outcomes with realised box scores.
- Clean counterfactual: the owner's actions do not affect NBA stats. Limitations (opponent reactions, waiver competition) are listed in every replay report.
- Before snapshot collection existed (i.e. before 2026-10), a replay can evaluate lineups and projections, but **not** FA-pool-dependent decisions.

## 7. Recommendation outcome tracking (live)
- Every recommendation is logged (`recs.recommendation`). Once its horizon passes, `just score-recs` joins the outcomes and records:
  - followed? (from the next roster snapshot)
  - realised Δ vs the alternatives
  - which confidence bucket it was in
- The weekly report shows performance by recommendation kind, confidence, and category. It analyses followed and ignored recommendations separately (selection bias).

## 8. Reports
- They are generated as markdown under `docs/evaluation/reports/` so they can be read on a phone.
- Each report contains:
  - the config and data window
  - metrics with CIs
  - plots saved as PNGs
  - a limitations section
  - an error-analysis section (the worst 20 cases + slices by position, role change, and injury status)
