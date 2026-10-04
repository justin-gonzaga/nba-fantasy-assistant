# fantasy-pipeline

**Responsibility:** Typer CLI; job DAG; partitioned idempotent jobs; change detection; scheduling entrypoints.

**Planned public interface:** `fantasy run <job>` CLI; `job(partition, ctx) -> JobResult`

**Allowed dependencies (app):** fantasy-core, fantasy-ingest, fantasy-features, fantasy-models, fantasy-decision, fantasy-evaluation. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
