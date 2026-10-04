---
id: INFRA-005
title: "Monitoring, error alerts and budget alerts to Telegram"
epic: EP-11 Infrastructure
phase: 1
component: infra
status: in_progress
ready: true
size: M
autonomy: review
gate: G-27
depends_on: [INFRA-004, INFRA-008]
areas: [infra/terraform/**, docs/runbooks/**, .github/workflows/**, apps/pipeline/**, packages/core/src/fantasy_core/settings.py]
standards: [devops, security]
assignee: claude
created: 2026-09-24
completed:
---
# INFRA-005 — Monitoring, error alerts and budget alerts to Telegram

## Objective
The daily chain now runs in the cloud (INFRA-008, first scheduled run succeeded 2026-10-03). The job already sends
"Daily run failed (…)" to Telegram when a step fails *inside* a run, but nothing tells the owner when the run never
starts (scheduler broken, image crash, auth), when the PC's NBA fetch stops (data goes stale), when the website or API
is down, or when spending approaches the budget (the free trial ends before 25 Dec; G-08 ceiling US$10/month).

## Context to read (only these)
- `docs/runbooks/daily-brief.md`, `docs/runbooks/api-hosting.md`; `infra/terraform/modules/env/daily.tf`
- `apps/pipeline/src/fantasy_pipeline/cli.py` (`_alert`), D-63

## User stories and edge cases
| Situation | The owner should get | Edge cases |
|---|---|---|
| The 07:45 job didn't run at all | Telegram by ~09:00: "No daily run today" | scheduler paused on purpose (off-season) → a documented mute switch |
| The job crashed before logging (bad image, missing secret) | Telegram with the execution name and the log link | repeated failures → one message a day, not one per retry |
| The PC fetch hasn't written new NBA data for 2+ game days | Telegram: "NBA data stale since Tue 20 Oct: check the PC" | no games scheduled (All-Star break, off-season) → no alert |
| Website or API down for 10+ minutes | Telegram: "Site down" / "API down", and "recovered" | a deploy's few seconds of restart → no alert |
| Spend reaches 50 % / 90 % / 100 % of the monthly budget | Telegram (and email) | the trial credit hides real cost → budget on actual + forecast |
| Telegram itself fails | Email fallback for budget alerts (Google's default) | — |

## Decision needed (gate G-27, menu in D-66)
How alerts reach Telegram:
- **(A ★) A tiny watchdog job** (Cloud Scheduler 09:00 → a Cloud Run job from the same image): reads `ops/job_runs.jsonl`,
  checks raw-data freshness against the schedule, pings the site and the API health endpoint, and sends Telegram with
  the existing bot secret. Uptime: a second schedule every 15 min for the site/API check only. **Cost** ~US$0 (free
  tiers). Pro: one code path, tested in Python, reuses the secret. Con: it can't see a failure of Cloud Scheduler itself.
- **(B) Cloud Monitoring alert policies + uptime checks** with a webhook notification channel to Telegram's API. Pro:
  Google-native, sees platform failures. Con: the bot token sits in the channel config/Terraform state; alert logic in
  MQL rather than tested code. Cost ~US$0 at this size.
- **(C) A + B's uptime checks only** (site/API uptime via Cloud Monitoring to email; everything else via the watchdog).
Budget alerts need the **billing account** (owner): a `google_billing_budget` with 50/90/100 % thresholds to email,
and Pub/Sub → watchdog → Telegram if A/C.

## Acceptance criteria
- [x] AC1: a missed or crashed daily run produces one Telegram alert by 09:00 Sydney with the execution and log link.
      Verify: `apps/pipeline/tests/test_watchdog.py` (no run today, a failed run, a muted day)
- [x] AC2: stale NBA data (no new box scores for ≥ 2 scheduled game days) alerts once a day; no alert without games.
      Verify: `test_watchdog.py::test_stale_*` (schedule-aware)
- [x] AC3: site and API down ≥ 10 min alert and a "recovered" message follows; deploy blips don't alert.
      Verify: `test_watchdog.py::test_uptime_*`; a manual drill documented in the runbook
- [x] AC4: Terraform for the scheduler(s), the job and the budget (budget behind a variable the owner sets); plan shown.
      Verify: `terraform -chdir=infra/terraform/modules/env test`; dev plan output
- [x] AC5: runbook: what each alert means and what to do; the mute switch.
      Verify: `docs/runbooks/monitoring.md`

## Test requirements
Pure functions with a frozen clock and fake HTTP/Telegram; Terraform tests for the new resources.

## Evaluation requirements
n/a

## Evidence
| AC | Type | Reference | Result |
|---|---|---|---|
| AC1 | test | apps/pipeline/tests/test_watchdog.py::test_no_run_today_alerts_once, ::test_todays_run_means_no_alert, ::test_muted_never_alerts | pass |
| AC2 | test | test_watchdog.py::test_stale_nba_data_alerts_after_two_days, ::test_stale_without_games_or_recent_does_not_alert (staleness from the week table's schedule-aware `stale_since`) | pass |
| AC3 | test | test_watchdog.py::test_uptime_alerts_after_ten_minutes_and_on_recovery, ::test_a_blip_never_alerts, ::test_probe_treats_errors_as_down; drill in docs/runbooks/monitoring.md | pass (drill after the owner's apply) |
| AC4 | terraform test + validate | env.tftest.hcl › watchdog_checks_daily_and_uptime; `terraform validate` of envs/dev and envs/prod (watchdog_muted wired from root); budget: the existing bootstrap budget (INFRA-001) covers it | pass |
| AC5 | runbook | docs/runbooks/monitoring.md | written |

## Implementation history
- 2026-10-03 — Refined overnight (owner asleep): spec + decision menu; implementation waits for G-27 and the
  owner's billing-account and `terraform apply` steps.
- 2026-10-03 — G-27 = A. Built TDD: `watchdog.py` (daily + uptime checks, once-a-day/debounced state), CLI
  `fantasy watchdog --mode`, settings (SITE_URL, API_URL, WATCHDOG_MUTED), Terraform job + 2 schedules + optional
  budget, CI image update, runbook. Budget alerts go by email for now (Telegram via Pub/Sub is a follow-up).

## Decisions
- Re-review: `packages/core/.../settings.py` is in scope (three settings the watchdog reads: SITE_URL, API_URL,
  WATCHDOG_MUTED; settings live in core by design); prod wires `watchdog_muted` too; a failed "recovered" send is
  retried (tested).
- Review (FAIL → fixed): no per-env budget (the bootstrap budget, INFRA-001, already alerts at 50/90/100 % for all
  projects); `watchdog_muted` wired from the env roots; a corrupt state file starts fresh; a failed Telegram send is
  retried at the next check.
- G-27 = A (owner, 2026-10-03): a watchdog job (daily checks at 09:00 Sydney; uptime every 15 min), reusing the
  bot secret. Budget alerts: a `google_billing_budget` (email) behind a `billing_account` variable the owner sets;
  Telegram for budgets is a follow-up (Pub/Sub → watchdog).

## Known issues
_None._

## Follow-ups
_None._
