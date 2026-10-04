# ADR-0014: Lightweight experiment tracking; file-based registry; no feature store

- **Status**: Superseded by ADR-0021 · **Date**: 2026-09-24 · **Standards**: S-15
- **Related**: ML standard §3–6

## Decision
- Experiment runs write `manifest.json` + a `gold.ml_runs` row. The markdown reports are generated from these.
- Model artefacts go in `DATA_ROOT/models/<name>/<version>/`, and the promoted versions are listed in `models/registry.yaml` in git.
- Feature views in code are the feature "store".

## Alternatives
- MLflow (a local server, UI, and registry)
- W&B (SaaS)
- Feast (a feature store)

They are rejected for now: their overhead isn't needed with one user and one model family, and markdown reports read well on a phone.

## Revisit triggers
More than 3 concurrent experiment lines needing interactive comparison → MLflow (local).
