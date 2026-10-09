# Project Status

_Keep ≤ 60 lines. Updated at the end of every task/session. Session-start brief: `python tools/tasks.py status`._

**As of**: 2026-10-09 · **Draft**: Sun 18 Oct · **Tip-off**: Tue 20 Oct · **Site**: https://nbafa-hdfo-dev.web.app

## Project is going dormant (owner pivot, 2026-10-09)
Owner is pivoting full attention to a second, commercial project (`~/projects/kanji-trainer`, a JLPT kanji
trainer; see that repo's `docs/specification/project-spec.md`). No new NBA tasks are being started. APP-011
(draft settings API) is merging on green CI (Tier A); nothing else in this repo should be touched after that
without the owner asking.
**Known issue, unresolved**: `uv.lock` pins `gcsfs==2025.12.0`, which pins `fsspec==2025.12.0` exactly
(CVE-2026-104851, HIGH, fixed in `fsspec` 2026.6.0). Bumping `fsspec`'s floor alone fails to resolve: `gcsfs`
needs `>=2026.1.0` to take a newer `fsspec`, but the `warehouse` package's `dbt-bigquery` constraint and `gcsfs`
version compatibility conflict (full trace in PR #5 CI, `security`/`image` jobs). Needs a coordinated bump of
`gcsfs`/`dbt-bigquery` together, tested against the warehouse package — not attempted (not a quick fix; the
project is dormant). CI's `security` and `image` jobs will keep failing on this until it's done.

## Repo is public (SEC-001, G-36, 2026-10-04)
Fresh single-commit public repo `justin-gonzaga/nba-fantasy-assistant` (PolyForm Noncommercial 1.0.0); the old history is the
private `-archive` repo. Merged: phone fit (WEB-040), practice room ring clock + sounds + motion (DRAFT-020), reuse register
(GEN-009), per-user draft settings API (APP-011).
**Needs you**: (1) `terraform apply` in `infra/terraform/bootstrap` after merging PR 3 (INFRA-011: WIF pins the new repo id), then set
repo variables `CLOUD_RUN_ENABLED` and `FIREBASE_ENABLED` to `true` (until then no deploy from CI and the dbt PR job is skipped);
(2) set your git email to the GitHub noreply address (`git config --global user.email`), the global config still holds the
university address; (3) optionally close the old PRs 134-138 in the archive; (4) the fsspec/gcsfs conflict above.

## Earlier history (2026-09 – 2026-10-04), condensed
Season replay + saved sims (SIM-001…006), practice draft room with timers/undo/fast-forward/report (DRAFT-013…015),
design v2 (WEB-023…028), raise overrides (DATA-036), team/coach NO-GO study (ANL-010). Full detail in git history
and `docs/project/tasks/`. **Still owner-pending from that era**: Firestore `terraform apply` (saved sims reset on
API deploy until then) + webhook secret/setWebhook; DATA-034 needs a Yahoo login; a paid billing account before
25 Dec; Giannis/Lillard raise rows once a source clears them (runbook § Overrides).

## Key risks (while dormant)
- The PC must run the 07:30 NBA fetch (cloud IPs are blocked, D-63) for data to stay fresh; irrelevant while no
  one is relying on live data, but note before resuming.
- The guard refuses a values rebuild that moves > 20 % of rows or reshuffles the top 10 (runbook).
