# ADR-0010: Yahoo integration — OAuth2, read-only scope, own client

- **Status**: Accepted · **Date**: 2026-09-24 · **Gates**: G-03 (scope), G-04 (retention)
- **Related**: research §1, security standard §2, spikes DISC-001/002

## Context
- The official Yahoo Fantasy API uses OAuth2. NBA stat IDs and resource shapes are undocumented.
- The Yahoo API Terms of Use contain a 24-hour deletion clause for "user data" unless the docs say it may be stored, and it is unclear whether league statistics count.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. Own client (httpx, `format=json`), OAuth2 auth-code with a stored refresh token, Read scope** | Raw payloads kept; minimal permissions | Must handle token refresh ourselves |
| B. yfpy as the runtime client | Mature | Parsed objects; raw capture is harder |
| C. Read/Write scope for automated moves | Could auto-set lineups | Higher risk; a separate product decision |

## Decision
- Option A. The owner performs the one-time consent.
- Retention follows G-04. The recommended default: keep raw league snapshots for personal, non-commercial analysis, with a retention job ready to purge on request.

## Consequences
- The token manager must alert on refresh failure.
- Write scope needs a new ADR and gate.

## Revisit triggers
Yahoo changes its auth or terms, or the owner wants automated lineup setting.

## Amendment (2026-09-24, before acceptance)
Per-user OAuth tokens (ADR-0024), stored in Secret Manager; retention per G-04 A2 (pseudonymise + purge switch).
