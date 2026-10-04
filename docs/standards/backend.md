# Backend Standard (`apps/api`)

Status: **Accepted** (owner selections recorded in `docs/project/standards-decisions.md`, 2026-09-24).

- **FastAPI + Pydantic v2**. Response models are explicit, and domain objects are never returned directly. The API layer maps them to `schemas/`.
- **Read-mostly**: the API reads BigQuery through the `api` service account (data viewer + job user). All writes happen in pipeline jobs. Where a job must be triggered on demand, the API calls into the pipeline job functions (in-process, locked), and never runs SQL writes itself.
- Routes are grouped by decision area:
  - `/today`
  - `/matchup`
  - `/players`
  - `/waivers`
  - `/trades` (POST evaluates a proposed trade; this is computation, not a write)
  - `/recommendations`
  - `/evaluation`
  - `/system/health`
  - `/system/freshness`
- Every response that depends on data includes `as_of` and `data_freshness`.
- **OpenAPI is the contract**. `just api-client` generates the TypeScript client, and CI fails if the generated client differs from the committed one.
- Errors: RFC 9457 problem+json, with a stable `type` URI per error class. No stack traces in responses.
- Caching: in-process TTL cache keyed by (route, params, data version). The data version bumps after every pipeline run.
- Auth (D-27): verify the Firebase/Identity Platform ID token and the email allowlist on every request, server-side. Rate limits apply per user. **Demo mode** (D-38) is a separate router on the anonymised demo dataset, with a capped chat.
- **NL question agent** (D-36): `/ask` runs Claude API tool use over vetted functions. Every number in an answer must come from a tool result (tested). Per-user and global caps apply, and everything goes to `recs.qa_log`.
- **Telegram webhook** (D-34): `/telegram/webhook` verifies Telegram's secret token and reuses the same service layer as the dashboard.
- Tests:
  - route tests with `httpx.AsyncClient` against an ephemeral BigQuery CI dataset built by `dbt build` on fixtures; pure service-layer tests use in-memory fakes
  - contract snapshot of the OpenAPI schema
- Performance: p95 < 1 s for cached views, measured by a simple benchmark test on the fixture DB.
