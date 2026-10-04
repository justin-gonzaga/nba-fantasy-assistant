---
id: APP-020
title: "Security events, audit trail and PII-free logging"
epic: EP-76 Identity and data protection
phase: 7
component: api
status: todo
ready: true
size: M
autonomy: review
gate: G-35
depends_on: [APP-008, APP-026]
areas: [apps/api/src/fantasy_api/security_events/**, apps/api/src/fantasy_api/logging*.py, apps/api/tests/test_security_events*.py, apps/api/tests/test_logging*.py]
standards: [backend, security, testing]
assignee:
created: 2026-10-04
completed:
---
# APP-020 — Security events and safe logs

## Objective
We must be able to answer "what happened to this account?" without putting personal data in logs. This task adds a
typed security-event stream (sign-in method used, onboarding, linking, step-up failures, role changes, moderation,
export, deletion, flag changes), a redaction layer so logs never contain emails, phone numbers, tokens, IPs in clear or
request bodies, and the alert rules that tell the owner when something looks wrong.

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Logging, Incident response)
- `apps/api/src/fantasy_api/main.py` (request logging), `docs/runbooks/` (alerting)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner investigating | "was this account compromised?" | events per account keyed by a **pseudonymous account id** (HMAC-SHA256 of the uid with a secret pepper, INFRA-010; the raw uid is never in a log or event): kind, time, method, coarse country, result; kept 180 days |
| Developer reading Cloud Logging | "safe by default" | one redaction filter on every log record and on exceptions: emails, phone numbers, bearer tokens, invite tokens, cookies, Authorization, query strings and request bodies; a deny-by-default field allow-list for structured logs |
| Attack in progress | "tell me" | alerts (to the existing Telegram channel, INFRA-005) on: > N failed sign-ins per account/IP, spike in sign-ups, role change on the owner account, admin action, token-forgery attempts |
| IP addresses | minimal | stored only as a salted daily hash (salt derived from the IP-hash seed secret, INFRA-010) for abuse correlation, retained 30 days; raw IPs only in Cloud Run's request log at its default retention |
| A new field is logged by mistake | caught | a test fails when a log call includes a key outside the allow-list |
| Privacy request | consistent | the events about a user are in the export and removed or anonymised on deletion (registry from APP-026) |

## Acceptance criteria
- [ ] AC1: `record_event(kind, actor, target, outcome)` writes a typed event (enumerated kinds) with the pseudonymous
      account id (HMAC of the uid), no email, phone, token or raw IP; unknown kinds are rejected at import time.
      Verify: `uv run pytest -q apps/api/tests/test_security_events.py`
- [ ] AC2: the redaction filter removes the patterns above from messages, args, exceptions and structured payloads;
      a property test feeds random emails/phones/tokens and asserts none survive.
      Verify: `uv run pytest -q apps/api/tests/test_logging_redaction.py`
- [ ] AC3: the request logger records method, route template (not the raw path), status, latency and a request id; query
      strings and request bodies are never logged (invite tokens travel only in POST bodies).
      Verify: `uv run pytest -q apps/api/tests/test_logging_redaction.py -k "request"`
- [ ] AC4: alert rules exist as code (thresholds in one table) and each fires in a unit test with synthetic events;
      delivery uses the existing Telegram path.
      Verify: `uv run pytest -q apps/api/tests/test_security_events.py -k "alert"`
- [ ] AC5: events are registered in `USER_DATA_OWNERS` (APP-026: exported, and anonymised on deletion) and carry a
      180-day TTL field.
      Verify: `uv run pytest -q apps/api/tests/test_security_events.py -k "registry or ttl"`
- [ ] AC6: no existing module logs a forbidden field: a grep-based test over `apps/` and `packages/` for `logger`
      calls with `email`, `phone`, `token`, `authorization` arguments passes.
      Verify: `uv run pytest -q apps/api/tests/test_logging_redaction.py -k "static"`

## Test requirements
Property tests for redaction; unit tests for alert thresholds; no network.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified.

## Decisions
- Allow-list over block-list for log fields: forgetting a field is safe, not a leak.

## Known issues
_None._

## Follow-ups
_None._
