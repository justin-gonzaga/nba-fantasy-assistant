# Software Engineering Standard

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

1. **Layering is law.** Respect the import rules in `system-architecture.md` §3; `import-linter` enforces them in CI. If you need an upward import, the design is wrong. Raise it in the task file instead.
2. **Functional core, imperative shell.** Pure functions compute (features, simulation, valuation, explanations), and thin shells do I/O (clients, DB, API). Pure code gets fast unit tests; shells get integration tests.
3. **Depend on protocols at boundaries.** Examples:
   - `Source`, `SnapshotStore`, `Projector`, `ScoringObjective`, `Clock`
   - Concrete classes are injected, and there are no module-level singletons (except `get_settings()`, which is cached).
4. **Time is an input.** Never call `datetime.now()` in domain code; take a `Clock` or an `as_of`. All stored timestamps are timezone-aware UTC, and the NBA game date is a separate `date` field (US/Eastern).
5. **Types everywhere.**
   - Pydantic models at I/O boundaries; frozen `dataclass`es or Pydantic for domain values
   - No `dict[str, Any]` crossing module boundaries
6. **Errors**:
   - Raise specific exceptions from `core.errors` (`SourceUnavailable`, `ContractViolation`, `LeakageError`, `ConfigError`).
   - Retries live only in the ingest shell (tenacity).
   - Never swallow exceptions; log with context and re-raise, or convert them into a `JobResult` failure.
7. **Logging**: `structlog` JSON logs with `run_id`, `task`, `job`, and `partition`. No `print` outside the CLI's presentation layer. Logs never contain secrets or tokens.
8. **Configuration**:
   - `pydantic-settings`: env vars → `.env` → defaults
   - one `Settings` object per app
   - Config is data. No logic branches on the environment name except in the composition root.
9. **Idempotency**: every job and CLI command can safely be re-run with the same arguments.
10. **Small modules**: target < 300 lines per module and < 40 lines per function. Complexity is checked by ruff (`C901` max 10).
11. **No premature abstraction**: an interface needs ≥ 2 implementations or a test double to justify it. The day-one abstractions listed in the architecture §10 are the exceptions.
12. **Observability**: every job emits a `JobResult` (status, rows in/out, duration, warnings) to `ops.job_runs` (BigQuery).
