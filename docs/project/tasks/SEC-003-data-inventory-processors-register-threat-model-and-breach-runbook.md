---
id: SEC-003
title: "Data inventory, processors register, threat model, breach runbook and legal text"
epic: EP-76 Identity and data protection
phase: 7
component: security
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [RSCH-010, APP-026]
areas: [docs/security/**, docs/runbooks/breach-response.md, docs/standards/user-data-and-auth.md, docs/legal/**, tools/data_inventory_check.py, tools/tests/test_data_inventory.py]
standards: [security, documentation]
assignee:
created: 2026-10-04
completed:
---
# SEC-003 — The paperwork that proves the ruleset

## Objective
Turn the standard into artefacts a reviewer can check: a data inventory (every personal field with purpose, lawful
basis, retention and owner), a processors register, a short threat model for the new surface (sign-up, leagues, uploads,
invites), a breach runbook with a kill-switch drill, and draft terms and privacy text for the owner to approve. This
research is not legal advice; the task ends with the owner's decision on legal review.

## Context to read (only these)
- `docs/standards/user-data-and-auth.md`; `docs/research/user-data-privacy-and-auth.md` (section 3, open questions)
- `docs/specification/leagues-and-accounts.md` §4, §9

## User stories and edge cases
Not applicable (documentation task). Edge cases: fields collected by a later feature must be added to the inventory in
the same PR (checked by HYG-001's trace check for the registry).

## Acceptance criteria
- [ ] AC1: `docs/security/data-inventory.md` lists every field in the user store, leagues, teams, media and logs with
      purpose, lawful basis, retention and the registry entry from APP-026; a test compares it to `USER_DATA_OWNERS`.
      Verify: `uv run pytest -q tools/tests/test_data_inventory.py`
- [ ] AC2: `docs/security/processors.md` lists each third party (Google/Firebase and reCAPTCHA, any email sender, the
      k-anonymity breach-list service the sign-up page calls (UDR-03), Apple if enabled, NBA/Yahoo data suppliers where
      personal data is involved) with the data shared, region and contract basis.
      Verify: the file has a row per processor and each row cites its terms page
- [ ] AC3: `docs/security/threat-model-courtside.md` covers sign-up abuse, account takeover, invite-link leakage, IDOR on
      leagues, upload attacks, SMS pumping, scraping of public leagues and insider access, each with a control and the
      task that implements it.
      Verify: every threat row names an AC id that exists (checked by the trace test)
- [ ] AC4: `docs/runbooks/breach-response.md` defines roles, a 72-hour clock, user notice, a takedown page for
      child-safety material or threats (hide at once, preserve the record, the legal reporting duty listed for the owner
      in G-35, never view it again), and the kill-switch (revoke all tokens, disable a provider, rotate secrets) with a
      dry run recorded in the task.
      Verify: the runbook lists each command; the dry run is logged in Evidence
- [ ] AC5: draft terms, privacy notice (including backup retention and the 16+ rule) and cookie statement exist in
      `docs/legal/` marked DRAFT; the task records the owner's choice on lawyer review and the open items (age in the
      EU, fantasy prizes, GDPR scope).
      Verify: the files exist; the decision is recorded in G-35
- [ ] AC6: the user-data standard keeps the status line PROPOSAL until G-35 shows it APPROVED; this task changes the
      status line only after that.
      Verify: `grep -n "Status" docs/standards/user-data-and-auth.md` shows PROPOSAL before approval and APPROVED with the
      gate date after

## Test requirements
The inventory/registry comparison test; link checks.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
_None yet._

## Known issues
- Legal conclusions are out of scope: the research flagged GDPR scope, minimum age, fantasy-sports law and US breach law
  as lawyer questions.

## Follow-ups
- SEC-002 consumes these before sign-up opens.
