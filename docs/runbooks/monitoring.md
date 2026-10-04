# Monitoring and alerts (INFRA-005, G-27 A)

The daily job already messages you on Telegram when a step fails inside a run. The **watchdog** catches the rest.
It is the same image as the daily job, on two schedules:

| Schedule | Checks | Message | What to do |
|---|---|---|---|
| 09:00 Sydney | Did today's 07:45 run happen? | "No daily run today (expected 07:45 Sydney)…" | Cloud Run → Jobs → `daily` → Executions: read the failed execution's logs; re-run it with "Execute" once fixed |
| 09:00 Sydney | Is the NBA data 2+ days stale? | "NBA data stale since Thu 1 Oct: check the PC's 07:30 fetch." | On the PC: is it on, is the scheduled task enabled, does `uv run fantasy run fetch` work? (cloud IPs are blocked, D-63) |
| every 15 min | Site / API up? | "Site down since 11:00 Sydney." then "Site recovered." | Firebase Hosting / Cloud Run → `api` → Logs; a deploy's restart never alerts (two failed checks in a row are needed) |
| billing | 50 / 90 / 100 % of the monthly budget | email from Google Cloud Billing (the bootstrap budget, `infra/terraform/bootstrap/budget.tf`, INFRA-001: all three projects) | Billing → Reports; anything unexpected → pause the schedulers and tell Claude |

Each daily problem alerts once a day. State lives in `gs://…-serve/ops/watchdog_state.json` (safe to delete: the
next check starts fresh).

## Owner steps
1. `terraform -chdir=infra/terraform/envs/dev plan` → adds the `watchdog` job, its CI deploy binding and the
   `watchdog-daily` / `watchdog-uptime` schedules; `apply`. CI then deploys the image on the next merge.
2. Budget: nothing to do: the bootstrap budget (INFRA-001) already emails at 50/90/100 %.
3. Drill (2 minutes): Cloud Run → Jobs → `watchdog` → Execute with args `fantasy watchdog --mode daily` on a day
   without a run, or pause `daily-brief` for a day, and check the Telegram message arrives.

## Mute (off-season)
`watchdog_muted = true` in `owner.auto.tfvars` and `apply` (or pause both watchdog schedules in Cloud Scheduler).
