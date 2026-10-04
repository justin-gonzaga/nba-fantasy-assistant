# ADR-0017: GitHub Actions CI/CD, trunk-based branching, CalVer releases

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-01 · **Standards**: S-18–S-23
- **Related**: `docs/standards/git-workflow.md`, `docs/standards/devops.md`

## Context
- Autonomous agents need fast, deterministic gates and a clean mapping from task to commit.
- Private repos on GitHub Free have no branch protection or environment reviewers (verified 2026-09-24).

## Decision
- Trunk-based development with squash-merged `task/<ID>-slug` branches and Conventional Commits.
- GitHub Actions: `ci`, `eval` (smoke), `build` (to GHCR), and `deploy`.
- CalVer release tags promote the same image digest, with automatic rollback.
- Protection is enforced by local hooks and the `just ship` script, with an optional upgrade to GitHub Pro (S-21).

## Consequences
- One commit per task gives a readable history and simple rollbacks.
- On GitHub Free, protection relies on hooks rather than server-side rules.

## Revisit triggers
An unreviewed or failing commit lands on `main` → GitHub Pro.

## Amendment (2026-09-24, before acceptance)
Public repo (G-01 C) → **server-side rulesets** on `main`. Merges to `main` auto-deploy to the **dev** project; CalVer tags deploy to prod. WIF auth (ADR-0019).
