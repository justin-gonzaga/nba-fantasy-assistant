---
id: RSCH-010
title: "Spike: Identity Platform quotas, provider linking, token storage and revocation latency"
epic: EP-76 Identity and data protection
phase: 7
component: security
status: todo
ready: true
size: S
autonomy: review
gate: none
depends_on: []
areas: [docs/research/**, docs/standards/user-data-and-auth.md, tools/spikes/**]
standards: [security]
assignee:
created: 2026-10-04
completed:
---
# RSCH-010 — Settle the four unverified auth facts

## Objective
`docs/research/user-data-privacy-and-auth.md` could not verify four facts that decide APP-018, APP-027, INFRA-009, INFRA-010 and the
standard. Run each against a throwaway Firebase project in the **dev** account (no billing, no paid SMS: test numbers
only) and record the observed answer, replacing the `UNVERIFIED` marks in the note and the standard.

## Context to read (only these)
- `docs/research/user-data-privacy-and-auth.md` (sections 2 and 5, the Suggested spikes list)

## User stories and edge cases
Not applicable (research task).

## Acceptance criteria
- [ ] AC1: SPK-1: with no billing instrument, record the daily phone-SMS cap actually enforced (3,000 or 10), the
      default SMS-region policy, and whether the password policy and MFA need the Identity Platform upgrade.
      Verify: the note has a dated "Observed" paragraph for each, with the console or API output quoted
- [ ] AC2: SPK-2: create an unverified email+password account for an address the owner controls, then sign in with
      Google for the same address; record whether the password method survives and what the API sees in the token
      (`email_verified`, `firebase.sign_in_provider`).
      Verify: the note records the result and APP-018's takeover test is aligned to it
- [ ] AC3: SPK-3 and SPK-4: record where the Web SDK keeps tokens (IndexedDB or localStorage) and the p50/p95 latency of
      `verify_id_token(check_revoked=True)` versus `False` on the dev Cloud Run service.
      Verify: the note has the numbers; UDR-09 and UDR-12 are updated to match
- [ ] AC4: every `UNVERIFIED` mark in the research note is either resolved with an observation or left with a reason.
      Verify: `grep -c UNVERIFIED docs/research/user-data-privacy-and-auth.md` before and after is recorded in the task
- [ ] AC5: SPK-5: record whether `X-Content-Type-Options: nosniff` and a `Content-Disposition` can be set on objects
      in a public-read Cloud Storage bucket served from `storage.googleapis.com` (object metadata), so INFRA-010's header
      check can be written against fact.
      Verify: the note records the header output of a test object

## Test requirements
n/a

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified from the researcher's suggested spikes.

## Decisions
_None yet._

## Known issues
- The spike needs a Firebase project and the owner's Google account (a human action, so autonomy is `review`); the rest
  is scripted. Editing the standard is a Tier B change.

## Follow-ups
_None._
