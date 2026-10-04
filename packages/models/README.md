# fantasy-models

**Responsibility:** Baselines, cold-start priors, minutes/rate/availability models; MLflow tracking; inference. Produces predictions only.

**Planned public interface:** `Projector.predict(as_of, player_games) -> Projections`

**Allowed dependencies (library):** fantasy-core, fantasy-features. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
