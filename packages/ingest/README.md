# fantasy-ingest

**Responsibility:** Source clients (Yahoo, NBA CDN, NBA stats, injury PDFs), rate limits/retries, data contracts, pseudonymiser, raw snapshot store + manifest, quarantine.

**Planned public interface:** `Source` protocol (`fetch(request) -> RawPayload`), `SnapshotStore.write(payload)`

**Allowed dependencies (library):** fantasy-core. These are enforced by import-linter (`just check`; architecture §3).

Status: stub (FND-010).
