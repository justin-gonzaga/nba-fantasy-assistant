# ADR-0025: Yahoo Fantasy API closed: apply to the new programme + assisted-import fallback

- **Status**: Accepted · **Date**: 2026-09-25 · **Deciders**: owner (panel), Claude
- **Decision refs**: D-43, D-44 · **Supersedes (in part)**: ADR-0010 (the runtime Yahoo API client)
- **Related**: docs/research/yahoo-api.md, ADR-0005, ADR-0022

## Context
Since 2026-07-22 the self-serve Yahoo Fantasy API returns 403 for all existing apps. New access requires an approved application, with unknown eligibility and timing. The league is with friends on Yahoo, so switching platforms isn't realistic.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| **A. Apply to the programme + assisted import (chosen)** | ToS-safe; works now; keeps the API path open | A few manual taps per week; no ownership %/FA ranks |
| B. Browser helper script | Less typing | Grey area under the "no automated means" terms; brittle |
| C. Server-side scraping with a session | Automatic | Likely breaches the ToS; account risk |
| D. Apply and wait | No extra build | Could miss the draft and the season |

## Decision
Option A. Yahoo data enters through an `OwnerImport` source: a screenshot or paste from Telegram or the dashboard → parser/LLM extraction → owner confirmation → a raw snapshot (with `observed_at`, pseudonymised). This is the same bronze contract as an API source, so an approved API client can replace it later without affecting anything downstream. Draft picks come in by quick entry.

## Consequences
- The Yahoo data cadence is owner-driven (after moves, and a weekly reminder).
- Ownership % and Yahoo FA ranks are unavailable. The FA pool and matchup totals are derived from NBA data + league rules.
- Evaluation of waiver decisions uses the derived FA pool (documented limitation).

## Revisit triggers
Yahoo approves our application (→ restore the API client behind the same Source interface), or Yahoo publishes new self-serve access.
