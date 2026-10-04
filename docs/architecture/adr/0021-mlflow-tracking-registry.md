# ADR-0021: MLflow for experiment tracking and model registry (laptop server, GCS artefacts)

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: S-15 B, D-37 A · **Supersedes**: ADR-0014
- **Related**: ADR-0012, ml standard §3–6

## Context
The owner chose MLflow partly for CV value. Hosted options cost ~$8–10/mo.

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
- Run **MLflow locally** (the laptop), with artefacts in GCS.
- Promoted models are exported to a GCS path that the Cloud Run jobs load.
- Markdown evaluation reports are generated from MLflow runs, for phone reading.

## Consequences
- $0; an industry-standard tool.
- Weekly retraining happens when the laptop is on (it isn't time-critical).

## Revisit triggers
Retraining needs to run unattended in the cloud → Cloud Run + Cloud SQL (~$8–10/mo).
