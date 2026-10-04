# ML Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

## 0. Owner mandate (2026-09-25): explicit, verified academic grounding BEFORE implementation
1. **Verified references only.** A reference may be cited only once its entry in `docs/research/ml-literature-review.md` is marked **Verified**. That means:
   - the primary source is checked (DOI, arXiv or the publisher page URL, with the access date)
   - the bibliographic details are confirmed
   - a 2–3 sentence summary of the key result is written
   - the specific claim we rely on is checked against the source ("supports / partially / does not support")
   - the access level is stated (full text vs abstract only)
2. **Plan before code.** The ML methodology plan (`docs/architecture/ml-methodology-plan.md`, task RSCH-004) must be **approved by the owner (gate G-19)** before any ML, projection or decision-model task starts. The plan covers each component's problem, method, features, target, validation, baselines and metrics, with verified citations, and states what is unsupported by literature.
3. **No silent gaps.** Where no literature supports a choice, the plan says so explicitly and names the empirical test that will justify it.

## 1. Theoretical grounding (mandatory)
- Every model, statistical method, and decision algorithm cites its grounding from `docs/research/ml-literature-review.md` (`[R-xx]`) in:
  - its model card
  - its experiment report
  - any related ADR or approval gate
- A method with no citable grounding must say so explicitly ("empirical / practitioner method"). It must also justify itself by beating a grounded baseline under the evaluation gate.
- **Approval gates for ML decisions** (G-14 and later) list:
  - the references
  - a one-line summary of what each establishes
  - how our setting differs from the paper's (e.g. baseball → basketball, season-level → game-level)
- New references are added to the literature review (with a `(to read)` flag until they have been read) *before* they are cited.

## 2. Baselines first
- Every predictive component has named baselines (see `ml-and-decision-design.md`). Baselines are implemented **before** the ML model and use the same `Projector`/`Predictor` interface.
- The promoted model is whichever one wins under the gate. If the baseline wins, the baseline ships.

## 3. Experiments
- An experiment is an `EXP-xxx` task with:
  - a hypothesis
  - the primary metric and success threshold (**written before running**)
  - the data window
- Runs are executed by `just exp run <config.yaml>` and tracked in **MLflow** (ADR-0021). Each run logs:
  - git SHA
  - config
  - data snapshot hash
  - feature list
  - seed
  - metrics
  - duration
- MLflow artefacts are stored in GCS.
- The report (`docs/evaluation/reports/EXP-xxx.md`) is generated from the manifest by a script, not by hand. Interpretation is added below the generated section.
- Negative results are reported and kept.

## 4. Reproducibility
- Fixed seeds, recorded.
- Deterministic data selection via `AsOfReader`.
- Pinned deps (`uv.lock`).
- A dataset is identified by (the raw-manifest hash over the window, the dbt project git SHA).

## 5. Features
- Every feature is a function of data observed at or before `as_of`, and feature views declare `as_of` semantics.
- A **leakage test per feature view** is mandatory: build at `t`, then assert that every input row has `observed_at <= t` (via instrumented reads) [R-60].
- Feature definitions live in code (`packages/features`), not in notebooks.
- There is no feature store; the feature views are the store (ADR-0014).

## 6. Models and registry
- Models are registered in the **MLflow model registry** (model file + model card + gate metrics).
- Promotion is **automatic on a gate PASS** (2026-09-24): the MLflow alias `champion`, an export to `gs://<prefix>-mlflow/promoted/<name>/<version>/`, a `predictions.model_promotions` record, and a Telegram note. `just model-rollback` reverts it.
- The model card template covers:
  - purpose
  - data
  - features
  - target
  - method and **grounding refs**
  - metrics vs baselines, with CIs
  - calibration
  - known failure modes
  - leakage review
  - retraining cadence

## 7. Training and retraining
- Scheduled retrain jobs produce *candidates*. Promotion always goes through `just eval-gate` (ml-and-decision-design §4).
- Hyperparameter search runs on inner walk-forward folds only. The final holdout season is touched only at release.

## 8. Monitoring
- The daily job logs predictions. Once outcomes are known, `predictions.prediction_errors` is populated.
- Dashboard: rolling MAE/Brier vs baseline, and calibration drift. An alert fires if the model is worse than the baseline for 7 consecutive days, which triggers an investigation task.

## 9. Compute
- Everything runs on the laptop's CPU. Anything that would need a GPU or more than 10 minutes of training needs an ADR.
