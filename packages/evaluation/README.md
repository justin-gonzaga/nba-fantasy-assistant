# fantasy-evaluation

**Responsibility:** Walk-forward backtests, historical replay, outcome scoring, calibration, promotion gate.

**Planned public interface:** `Backtest.run(spec) -> Report`

**Allowed dependencies (library):** fantasy-core, fantasy-features, fantasy-models, fantasy-decision. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
