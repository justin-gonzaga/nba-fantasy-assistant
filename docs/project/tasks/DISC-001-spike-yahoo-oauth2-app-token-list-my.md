---
id: DISC-001
title: "Spike: Yahoo OAuth2 app + token + list my leagues"
epic: EP-01 Discovery
phase: 0
component: ingest
status: done
ready: true
size: S
autonomy: gated
gate: G-03
depends_on: []
areas: [docs/research/**, spike code (not merged)]
standards: [security]
assignee:
created: 2026-09-24
completed: 2026-09-24
---
# DISC-001 — Spike: Yahoo OAuth2 app + token + list my leagues

## Objective
Prove we can authenticate to Yahoo Fantasy (read scope), refresh tokens, and list the owner's NBA leagues.

## Context to read (only these)
- `docs/research/2026-09-initial-research.md §1`
- `docs/standards/security.md §2`

## Acceptance criteria
- [x] AC1: Step-by-step owner instructions for app registration exist (redirect URI requirements verified).
      Verify: docs/runbooks/owner-setup.md step 3 (redirect `https://localhost:8080`, Confidential Client)
- [x] AC2: The owner completes consent once, and the refresh-token flow is demonstrated (token lifetime measured).
      Verify: `python tools/yahoo_login.py` → token saved; `--check` → refresh OK, lifetime 3600 s
- [ ] AC3: The owner's NBA leagues for the current + prior seasons are listed. **Not achievable: the Yahoo Fantasy API returns 403 for all existing apps since 2026-07-22 (external policy change; ADR-0025).**
      Verify: diagnosis: all 5 fantasy endpoints → 403 "This application is not authorized to perform this action"
- [x] AC4: Findings are in docs/research/yahoo-api.md, including rate-limit observations (n/a: blocked before any data).
      Verify: docs/research/yahoo-api.md
- [x] AC5: No secrets are written anywhere except .env / secrets/.
      Verify: the script prints no tokens; the token lives in gitignored secrets/; the pre-commit secret scan found nothing

## Test requirements
Spike: manual verification recorded in the research note.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | doc | docs/runbooks/owner-setup.md §3 | app registered by the owner (App ID s6GZFZED) |
| AC2 | command | owner ran `python tools/yahoo_login.py`; Claude ran `--check` | token saved; refresh OK; lifetime 3600 s |
| AC3 | command | scratchpad diagnosis script (metadata only) | **not met**: 403 on game/nba, games, users, users/games, users/games/leagues; external cause confirmed (yfpy #84; the new approval programme) |
| AC4 | report | docs/research/yahoo-api.md | written |
| AC5 | command | code review of tools/yahoo_login.py; token file in the gitignored secrets/ | no secrets printed or committed |

## Implementation history
### 2026-09-25
- Built tools/yahoo_login.py (stdlib; consent + refresh + league-list check; prints Yahoo error text, never tokens; sends a User-Agent).
- The owner consented (twice). The token and refresh work, but every fantasy endpoint is 403 "application not authorized". The permission is confirmed granted in the app console (owner screenshot).
- Research: the Yahoo Fantasy API has been closed to existing apps since 2026-07-22; new access is via an approval programme.
- Owner decisions (panel): apply + assisted-import fallback (D-43, ADR-0025); quick pick entry for the draft (D-44); rotate the secret when new access arrives.
- **Security note:** the owner's screenshot exposed the client secret in chat, so it's tracked for rotation (YAHOO-001).
- Closed as a spike: AC3 is not met, with the external cause documented.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
