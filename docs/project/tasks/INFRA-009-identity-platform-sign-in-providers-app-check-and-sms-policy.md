---
id: INFRA-009
title: "Identity Platform, sign-in providers, App Check, SMS region policy and budget alerts"
epic: EP-76 Identity and data protection
phase: 7
component: infra
status: todo
ready: true
size: M
autonomy: gated
gate: G-35
depends_on: [APP-008, RSCH-010]
areas: [infra/terraform/**, docs/runbooks/identity-platform.md]
standards: [devops, security]
assignee:
created: 2026-10-04
completed:
---
# INFRA-009 — Cloud settings for sign-in

## Objective
Provision, in **dev first**, what the sign-in features need: Identity Platform with the allowed providers, the password
policy, TOTP MFA, email-enumeration protection, App Check, the reCAPTCHA SMS defence, the SMS region allow-list and
budget alerts that cover SMS. Storage, secrets, TTL and indexes are INFRA-010 (split so each task stays one reviewable
change). It costs money (a billing account, per-SMS charges), so it cannot start until G-35 is approved. Prod changes
happen only through CI (merge to dev, CalVer tag to prod).

## Context to read (only these)
- `docs/standards/user-data-and-auth.md` (Authentication, Phone/SMS)
- `docs/research/user-data-privacy-and-auth.md` (sections 2, 4, 5); RSCH-010 results
- `infra/terraform/*`, `docs/runbooks/` (alerting from INFRA-005)

## User stories and edge cases
| Persona / situation | Story | Edge cases the change must handle |
|---|---|---|
| Owner | "no surprise bill" | a budget alert at 50/80/100 % that includes SMS and the Identity Platform product; a billing cap documented; a log-based metric counting SMS sends with an alert at 80 % of a daily budget (the client SDK sends SMS directly, so the API cannot count them: UDR-19) |
| Attacker pumping SMS | "cannot" | the SMS region policy is an allow-list (US and AU); reCAPTCHA SMS defence in AUDIT before ENFORCE; test numbers only in dev |
| Dev vs prod | "no cross-over" | every resource exists in both with variables; applies run only in CI; nothing in prod from this session |
| Rollback | "turn it off" | each provider is a toggle in code and in config; disabling phone is a one-line change (with `AUTH_METHODS` in APP-018) |
| Console-only settings | "documented, not remembered" | settings the provider exposes only in the console are listed in the runbook with value, owner and how to check |

## Acceptance criteria
- [ ] AC1: Terraform declares Identity Platform config (providers by variable, password policy, MFA TOTP, email
      enumeration protection on, authorised domains) and `terraform validate` plus `plan` for dev show only intended
      changes.
      Verify: `terraform -chdir=infra/terraform/envs/dev validate`; the plan summary is recorded in the task
- [ ] AC2: SMS region allow-list (US) and reCAPTCHA SMS defence are declared or scripted, with a runbook step for the
      parts the provider only exposes in the console, each marked with who does it.
      Verify: `docs/runbooks/identity-platform.md` lists each setting, its value and how to check it
- [ ] AC3: budget alerts include SMS and the Identity Platform product and reach the existing Telegram channel
      (INFRA-005); a log-based metric and alert policy count phone-auth sends against a daily budget.
      Verify: the plan shows the budget, metric and notification resources; a test alert is recorded in the task
- [ ] AC4: nothing is applied to prod; the apply path for dev is documented and every resource has an owner label.
      Verify: `git diff --stat` shows no prod tfvars change; the runbook states the CI-only rule

## Test requirements
`terraform fmt -check`, `validate` and `plan` for dev; policy checks from the existing CI.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|

## Implementation history
- 2026-10-04 — Specified; split into this task and INFRA-010 after review. Gated by G-35 (spending).

## Decisions
_None yet._

## Known issues
- Pricing and quota facts are in conflict across Google pages; RSCH-010 resolves them first.

## Follow-ups
- Prod rollout is a separate CalVer-tag release after SEC-002 passes.
