# dikit

The decision-intelligence kit: the domain-neutral kernel that any decision product in this
repo builds on (D-58, D-60). It must never import a domain package, and it must not mention
any domain (import-linter contract + `tests/test_neutral.py`).

| Module | What |
|---|---|
| `dikit.store.snapshot` | immutable raw snapshot store (write-once, manifest, latest by key) |
| `dikit.store.http` | paced, retrying HTTP client (headers are the caller's) |
| `dikit.time.clock` | injectable clocks and `AsOf` (aware UTC only) |
| `dikit.time.calendar` | a time zone's calendar date of an instant; a local day's UTC bounds (DST-safe) |
| `dikit.jobs` | job registry, runner, run log, lock, catch-up of missed partitions |
| `dikit.settings` | `BaseAppSettings` (env + env file) and `load(cls)`; products subclass it |
| `dikit.errors`, `dikit.logging` | the error hierarchy and structured logging |
| `dikit.evaluate.bootstrap` | resampling indices, percentile CIs, mean / ratio / clustered (block) bootstraps [R-55] |
| `dikit.evaluate.scoring` | exact and sample CRPS [R-41], randomized PIT [R-43, R-44], Spearman |
| `dikit.methods.counts` | negative-binomial and beta-binomial fits by moments, CDFs, sampling [R-30, R-31] |
| `dikit.methods.shrinkage` | Gamma-Poisson / Beta-Binomial priors [R-11], prior-data blend and choosing k [R-12] |
| `dikit.methods.regression` | closed-form ridge, class-weighted L2 logistic [R-89] |
| `dikit.decide.assign` | exact slot assignment (MILP, HiGHS) with an optional flex slot [R-04] |
| `dikit.decide.simulate` | Monte Carlo head-to-head over a category spec, common random numbers [R-61] |

A product binds these to its domain in thin modules (for this repo: `fantasy_decision.lineup`,
`fantasy_decision.simulate`, `fantasy_core.settings`, `fantasy_core.gamedate`).
