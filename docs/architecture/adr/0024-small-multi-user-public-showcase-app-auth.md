# ADR-0024: Small multi-user readiness, app-level login, public repo and showcase

- **Status**: Accepted · **Date**: 2026-09-24 · **Deciders**: owner (via decision panels), Claude (proposal)
- **Decision refs**: D-31, D-27, D-38, G-01 C, D-39
- **Related**: ADR-0010, security standard

## Context
The owner wants friends to be able to use it and recruiters to view it (public demo, case study and code), with an iOS app later.

## Options considered
See the linked decision items in `docs/project/architecture-decisions.md`: each has a Learn primer, options with pros and cons, and the owner's selection.

## Decision
- Keying by league and user.
- Per-user Yahoo OAuth tokens.
- **App-level login** (Firebase Auth / Identity Platform, Google sign-in, email allowlist, server-side verification).
- A **public repo** after the SEC-001 audit.
- A **public showcase**: a case study + a read-only demo on anonymised data + a capped demo chat, launching with the dashboard.
- A native SwiftUI app later over the same OpenAPI contract.

## Consequences
- More security surface (APP-005 review).
- Live Yahoo data is never shown publicly.
- iOS builds need macOS (G-18).

## Revisit triggers
Abuse or cost from public traffic, or a Yahoo ToU concern.
