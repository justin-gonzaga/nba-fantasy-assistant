---
id: DATA-028
title: "Laptop bookmarklet: one-click send of the Yahoo page being viewed (D-45)"
epic: EP-20 Ingestion
phase: 2
component: ingest
status: todo
ready: true
size: M
autonomy: review
gate: none
depends_on: [DATA-026]
areas: [apps/web/**, apps/api/**, tools/**, docs/runbooks/**]
standards: [security, testing, frontend]
assignee:
created: 2026-09-25
completed:
---
# DATA-028 — Laptop bookmarklet for Yahoo pages

## Objective
An optional one-click extra (D-45). While viewing a Yahoo League → Rosters or Transactions page (logged in), clicking a bookmark reads the visible table and sends it to the owner's system via the OwnerImport path. It only runs on the owner's click and only reads the visible page. **Priority: after the draft (M0.5).**

## Context to read (only these)
- docs/project/architecture-decisions.md D-45
- docs/architecture/adr/0025-yahoo-api-closed-assisted-import.md

## Acceptance criteria
- [ ] AC1: A spike determines whether Yahoo's Content-Security-Policy allows sending to our endpoint from the page. If it doesn't, the clipboard fallback (copy → one paste) is implemented instead.
      Verify: spike notes in docs/research/yahoo-api.md §bookmarklet
- [ ] AC2: The Rosters and Transactions pages parse into validated OwnerImport payloads (tested against saved, scrubbed page HTML fixtures).
      Verify: tools/tests (or apps) test_bookmarklet_parsers with fixtures
- [ ] AC3: The endpoint requires a personal token (never embedded in a public repo; configured per user). Payloads are pseudonymised on ingest, and a confirmation toast shows what was received.
      Verify: test_bookmarklet_auth_required + manual demo screenshot
- [ ] AC4: A runbook explains how to install the bookmarklet (laptop; phone notes) and what it does and doesn't read.
      Verify: docs/runbooks/yahoo-bookmarklet.md

## Test requirements
Parser unit tests on saved HTML fixtures; auth test on the endpoint.

## Evaluation requirements
n/a

## Evidence
_Filled at completion: one row per AC._

## Implementation history
_None yet._

## Decisions
_None yet._

## Known issues
The owner provides one saved copy of each page (Save Page As → HTML) for the fixtures, after the draft.

## Follow-ups
_None._
