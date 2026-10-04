# ADR-0013: FastAPI + React SPA; markdown reports first

- **Status**: Accepted · **Date**: 2026-09-24 · **Gate**: G-07 · **Standards**: S-24–S-26
- **Related**: `technology-evaluation.md` §8–9

## Context
The dashboard is used mostly on a phone. It must be decision-first and testable. The value must arrive before the dashboard exists.

## Options considered
See S-24:
- **A.** React SPA (★)
- **B.** Streamlit
- **C.** HTMX
- **D.** Evidence

## Decision
- Phases 3–6 deliver recommendations as **generated markdown reports**, which are readable via Claude Code on the phone.
- Phase 7 builds a FastAPI read API plus a React/Vite/TypeScript SPA. The SPA is served by the API container and reached via Tailscale.

## Consequences
- The UI is built once, against stable APIs.
- More frontend code than Streamlit would need.

## Revisit triggers
The owner prefers a quick internal tool over a polished mobile UI → Streamlit.

## Amendment (2026-09-24, before acceptance)
Access is **app-level login** (ADR-0024), not network-only. A chat panel for NL questions (ADR-0023). shadcn/ui + Tailwind; 'Today: actions first' home; action cards (U2–U4). A clickable prototype is approved before the build (U8). A public demo mode (D-38).
