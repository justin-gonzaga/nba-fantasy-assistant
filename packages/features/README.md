# fantasy-features

**Responsibility:** Point-in-time feature views over the warehouse via `AsOfReader(t)`; leakage harness.

**Planned public interface:** `AsOfReader`, `FeatureView.build(as_of, entities)`

**Allowed dependencies (library):** fantasy-core. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
