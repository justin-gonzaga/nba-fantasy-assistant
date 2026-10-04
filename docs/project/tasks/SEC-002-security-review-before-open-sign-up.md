---
id: SEC-002
title: "Security review and abuse drill before OPEN_SIGNUP is switched on"
epic: EP-76 Identity and data protection
phase: 7
component: security
status: todo
ready: true
size: M
autonomy: gated
gate: G-35
depends_on: [APP-017, APP-018, APP-020, APP-024, APP-025, APP-027, INFRA-009, INFRA-010, SEC-003, WEB-038, WEB-036]
areas: [docs/security/**, docs/runbooks/**, tools/security/**, tools/tests/test_udr_compliance.py]
standards: [security, testing]
assignee:
created: 2026-10-04
completed:
---
# SEC-002 — Gate for opening sign-up

## Objective
The `OPEN_SIGNUP` flag stays off until an independent review and a drill show that the account and league surface is
safe. The review is performed by the `reviewer` subagent against the standard and the threat model, plus a scripted
abuse run against dev (sign-up flood, enumeration, IDOR across leagues, invite brute force, upload bombs, log scan for
personal data). The owner flips the flag; Claude never does.

## Context to read (only these)
- `docs/standards/user-data-and-auth.md`, `docs/security/threat-model-courtside.md`, `docs/security/data-inventory.md`
- the merged code for the tasks listed in `depends_on`

## User stories and edge cases
Not applicable (review task).

## Acceptance criteria
- [ ] AC1: every UDR rule in the standard has a row with the test, config or document that proves it and its status;
      no rule is `untested`.
      Verify: `uv run python tools/security/udr_compliance.py` writes `docs/security/udr-compliance.md` with zero
      `untested` rows; `uv run pytest -q tools/tests/test_udr_compliance.py`
- [ ] AC2: the scripted abuse run in dev passes: enumeration oracles absent, cross-league access returns 404, invite
      brute force is throttled, oversized and malformed uploads are rejected, a request body over 16 KB gets 413.
      Verify: `tools/security/abuse_drill.py` output saved to `docs/security/drill-<date>.md`
- [ ] AC3: a scan of dev logs and the export for the test accounts finds no email, phone number, token or raw IP.
      Verify: `tools/security/log_scan.py` reports zero hits
- [ ] AC4: reviewer subagent PASS recorded, with every finding fixed or accepted by the owner in G-35.
      Verify: the review is linked in Evidence
- [ ] AC5: the flag-flip procedure and the rollback (flag off, revoke tokens, disable a method) are in the runbook and
      rehearsed once in dev.
      Verify: the runbook section exists and the rehearsal is logged
- [ ] AC6: the SMS and email controls the API cannot enforce are measured with test numbers in dev: the real
      per-number and per-IP throttle is recorded, the usage alert and billing budget fire in a dry run, and setting
      `AUTH_METHODS` without phone removes phone sign-in (UDR-19).
      Verify: the drill report has the measured numbers and the alert evidence

## Test requirements
n/a (the drill is the test)

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified. Not ready until its dependencies are merged and G-35 is approved.

## Decisions
_None yet._

## Known issues
_None._

## Follow-ups
- The owner flips `OPEN_SIGNUP` in dev, then prod via CI.
