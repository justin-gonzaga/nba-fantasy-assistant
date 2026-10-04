# fantasy-api

The read-only web API (FastAPI) over what the pipeline publishes under the data root (D-62).

- Run locally: `uv run fantasy-api`, then open http://127.0.0.1:8000/docs.
- Contract: `openapi.json`. Regenerate with `uv run fantasy-api --write-openapi` when a change is intended;
  `tests/test_openapi.py` fails on unintended drift.
- Standard: `docs/standards/backend.md`.
