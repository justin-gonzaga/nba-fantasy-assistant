# fantasy-decision

**Responsibility:** Simulator, per-format `ScoringObjective`, lineup MILP, valuation, rules, evidence + explanations, recommendation log.

**Planned public interface:** `DecisionEngine.recommend(context) -> list[Recommendation]`

**Allowed dependencies (library):** fantasy-core, fantasy-features, fantasy-models. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
