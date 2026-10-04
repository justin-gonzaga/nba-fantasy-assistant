# Project Status

_Keep ≤ 60 lines. Updated at the end of every task/session. Session-start brief: `python tools/tasks.py status`._

**As of**: 2026-10-04 (night) · **Draft**: Sun 18 Oct · **Tip-off**: Tue 20 Oct · **Site**: https://nbafa-hdfo-dev.web.app

## Repo is public (SEC-001, G-36, 2026-10-04)
Fresh single-commit public repo `justin-gonzaga/nba-fantasy-assistant` (PolyForm Noncommercial 1.0.0); the old history is the
private `-archive` repo. Actions are free there and CI runs again (security, lint-type, test-py, web, image, docs, web-e2e green).
Merged: phone fit (WEB-040), practice room ring clock + sounds + motion (DRAFT-020), reuse register (GEN-009).
**Needs you**: (1) `terraform apply` in `infra/terraform/bootstrap` after merging PR 3 (INFRA-011: WIF pins the new repo id), then set
repo variables `CLOUD_RUN_ENABLED` and `FIREBASE_ENABLED` to `true` (until then no deploy from CI and the dbt PR job is skipped);
(2) set your git email to the GitHub noreply address (`git config --global user.email`), the global config still holds the
university address; (3) optionally close the old PRs 134-138 in the archive.

## Specs ready (2026-10-04)
Still to build before 18 Oct: draft settings (APP-011 API, DRAFT-017 page; DRAFT-018/019/021 values, formats, snake) and
scale (PERF-001/002). Done: WEB-029, DRAFT-022, DRAFT-020 (AC9 listening pass is yours).

## Latest (2026-10-04)
**Season replay** (G-31, SIM-001…004): draft on 2023-24, 2024-25 or 2025-26 (pre-season values only), then play
that season week by week at /replay: schedule grid (games by player and NBA team; DNPs not revealed early),
daily lineups (auto + bench), 4 pickups a week, scored on real box scores, keep results into a season record.
Season files publish on the first daily run after SIM-001. **Past sims** at /sims (SIM-005/006): practice runs
and replay leagues kept with the account (30 full runs, 200 summaries, 10 pins, 5 leagues), compare/trend, reopen
a report, continue a season on any device (more kept weeks wins). APP-009 settings + Telegram webhook API merged.
**Owner**: Firestore apply (until then saved sims reset on an API deploy); webhook secret + setWebhook.

## Earlier (2026-10-03, evening)
**Live now**
- **Design v2** (design-language §9): desktop sidebar, Players stat table + right panel, redesigned player detail,
  landing page with "Explore with sample data", two-column Today (WEB-023…026); low-minute players sort last in
  category views (WEB-027); resizing across 840 px no longer resets a page (WEB-028).
- **Draft practice** at /draft (G-28 A,A,A): a calibrated simulated room (top-50 prices 1.02× value, 99.8 % spent;
  DRAFT-013), the practice page with timers, undo, fast-forward and resume (DRAFT-014); the post-draft report
  (category ranks vs the room, budget pace, lessons, history) is in review (DRAFT-015).
- **Raise overrides** (DATA-036): a cited `cleared` row raises games/minutes; the player shows **Adjusted**.
- **Team/coach research**: literature (RSCH-009), coach + pace history 2015-16 → 2025-26 (DATA-038), and the
  pre-registered study (ANL-010): **NO-GO**, the projection's errors don't line up with team or coach changes
  (< 0.4 % of variance), so EXP-004 isn't run.

**Needs you**
1. `terraform apply` (watchdog + Firestore), then `users_backend = "firestore"`; install the Firestore→BigQuery extension.
2. Draft week: pre-season backfill + dry run with me by Thu 15 Oct (DRAFT-006). Giannis raise row: add it when a
   source says he's cleared (runbook § Overrides).
3. DATA-034 needs a Yahoo login; before 25 Dec a paid billing account.

## In progress / open
- DRAFT-015 (practice report) in review; APP-009, WEB-014/015 (users, G-25 approved); ANL-009 (late-season
  availability, gated G-19); WEB-021 (compare).

## Key risks
- The PC must run the 07:30 NBA fetch (cloud IPs are blocked, D-63); without it data goes stale (the site says so).
- The guard refuses a values rebuild that moves > 20 % of rows or reshuffles the top 10: a deliberate method change
  needs a reviewed PR (runbook).

## Lessons tonight (ledger rows 35–38)
- `to_camel` turned `fg3m` into `fg3M`; typecheck against generated types caught it.
- Polars `rank()` is unsigned: rank differences wrapped and nearly triggered a model task; cast to signed first.
- Every new indicator was checked on real data before shipping: two calibrations were wrong and got fixed.
