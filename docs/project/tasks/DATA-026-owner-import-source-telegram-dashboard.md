---
id: DATA-026
title: "OwnerImport source: screenshot/paste → extract → confirm → raw snapshot"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: M
autonomy: auto
gate: none
depends_on: [DISC-011, DATA-001]
areas: [docs/**, packages/ingest/**, apps/**]
standards: [data-engineering, security]
assignee:
created: 2026-09-25
completed:
---
# DATA-026 — OwnerImport source: screenshot/paste → extract → confirm → raw snapshot

## Objective
Implement the assisted-import Source (ADR-0025): intake via Telegram/dashboard, extraction, an owner confirmation step, and a pseudonymised raw snapshot with `observed_at`. The contract matches a future API client.

## Context to read (only these)
- docs/research/yahoo-api.md
- docs/architecture/adr/0025-yahoo-api-closed-assisted-import.md

## Acceptance criteria
- [ ] AC1: A league settings import produces a validated LeagueRules input
      Verify: integration test with sample fixtures
- [ ] AC2: A roster import maps 100 % of players to NBA IDs, or asks the owner to resolve the unmatched ones
      Verify: test_roster_import_crosswalk
- [ ] AC3: Nothing is stored before owner confirmation; confirmed imports land in raw with observed_at + pseudonymisation
- [ ] AC4: **Low-touch mode (D-45)**: post-draft rosters are seeded from the entered draft picks; Telegram [Done]/[Skipped] buttons and plain-English move messages update the owner's roster as timestamped events
      Verify: test_roster_events_from_buttons_and_text
- [ ] AC5: Free-agent suggestions carry an "if available" flag and ≥ 2 ranked backups; close matchups trigger an optional opponent-move check prompt
      Verify: test_fa_suggestions_have_backups + test_opponent_check_prompt
      Verify: test_confirmation_gate + test_pseudonymised_raw

## Test requirements
Per the testing standard.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
_None._
