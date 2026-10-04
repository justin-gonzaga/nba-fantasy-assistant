# Runbook: the daily brief (MVP)

The morning chain runs `python -m fantasy_pipeline daily-run` at **07:30 Sydney** (about 4:30 PM
US Eastern, after the afternoon injury reports and before the first tip-off):

1. `nba-daily`: the schedule and yesterday's final box scores (cdn.nba.com), this season's game
   logs (stats.nba.com), and today's latest official injury report.
2. `week-projection`: rest-of-week projections (games left, availability from the measured
   injury-status rates, expected category totals) -> `data/predictions/week_projection.parquet`.
3. `brief`: lineup, matchup outlook and pickups -> `data/briefs/<date>.md`. Needs the league
   file; before the draft, the chain stops after step 2.
4. `send-brief`: the brief to the owner's Telegram chat.

It runs on the job runner (FND-011): a lock stops overlapping runs, missed game days are caught up
(up to 14), and every job's result goes to `data/ops/job_runs.jsonl`. A failing job skips what depends
on it, exits non-zero and sends a one-line Telegram alert. Output is appended to `data/logs/daily-run.log`.
Manual runs: `uv run fantasy run daily`, or `uv run fantasy run cdn-day --start 2026-10-20 --end 2026-10-22`.

## One-time setup

| Step | Who | Command |
|---|---|---|
| Bot token in `.env` (`TELEGRAM_BOT_TOKEN`) | owner | done 2026-09-27 |
| Send the bot any message on Telegram | owner | (in Telegram) |
| Save the chat id | Claude or owner | `uv run python -m fantasy_pipeline telegram-setup` |
| Test message | Claude or owner | `uv run python -m fantasy_pipeline send-brief --text "test"` |
| Scheduled task | done 2026-09-28 | `powershell -NoProfile -File tools\schedule_daily.ps1` |
| League file after the draft | Claude, from the owner's pasted rosters | `data/league/league.json` (format in `daily_brief.py`) |

## Weekly

- Monday: update the opponent in `data/league/league.json` (the matchup schedule isn't released yet).
- After each trade or add/drop: update `my_team` and `rostered`, or re-paste the rosters page.

## Checks

- `Get-ScheduledTask -TaskName "NBA Fantasy daily brief"` shows the task state.
- `Get-Content data\logs\daily-run.log -Tail 20` shows the last run.
- Dry run on a sample league: `uv run python -m fantasy_pipeline brief --sample --league data/league/sample_league.json --at 2026-10-21T14:00:00+00:00`.

## Switch-over to the cloud chain (INFRA-008, D-63)

The NBA's hosts block cloud IPs, so after the switch the PC only downloads (07:30, `run fetch`) and the
Cloud Run job `daily` does the rest at 07:45 (`run cloud`). If the PC is off, the brief still arrives,
built on the last data and starting with a "Stats are missing games since ..." warning.

| # | Step | Who | Command / place |
|---|---|---|---|
| 1 | Put the bot token into Secret Manager (it's in `.env`; Claude never reads that file) | owner | PowerShell (the token is masked as you type): `$s = Read-Host "Telegram bot token" -AsSecureString; [Net.NetworkCredential]::new('', $s).Password \| gcloud secrets versions add telegram-bot-token --project nbafa-hdfo-dev --data-file=-` |
| 2 | In `infra/terraform/envs/dev/owner.auto.tfvars`: `telegram_chat_id = "<chat_id from data/telegram_chat.json>"` (leave `daily_schedule_enabled = false` for now), then `terraform -chdir=infra/terraform/envs/dev apply` (6 to add) | owner | |
| 3 | Copy the existing raw history to the raw bucket (append-only; nothing is deleted) | owner or Claude | `gcloud storage rsync -r data/raw gs://nbafa-hdfo-dev-raw/raw` |
| 4 | Copy the chain's inputs to the serve bucket | owner or Claude | `gcloud storage cp data/predictions/preseason_projection.parquet gs://nbafa-hdfo-dev-serve/predictions/` (auction values, player history and breakout chances are published by the job's `draft-values` step since DATA-035; never copy them by hand); `gcloud storage cp data/samples/yahoo/league_settings.txt gs://nbafa-hdfo-dev-serve/samples/yahoo/`; after the draft also `data/league/league.json` -> `gs://nbafa-hdfo-dev-serve/league/` |
| 5 | Point the PC's downloads at the raw bucket: add `DATA_ROOT=gs://nbafa-hdfo-dev-raw` to `.env` | owner | |
| 6 | Make the PC task download-only | owner or Claude | `powershell -NoProfile -File tools\schedule_daily.ps1 -Mode fetch` |
| 7 | Test the cloud job once | Claude | `gcloud run jobs execute daily --region australia-southeast1 --project nbafa-hdfo-dev --wait` |
| 8 | Turn the schedule on: `daily_schedule_enabled = true` in owner.auto.tfvars, then apply (1 to change) | owner | |

From then on: league-file edits go to `gs://nbafa-hdfo-dev-serve/league/league.json` (the website shows the
same brief). Cloud logs: Cloud Run -> Jobs -> daily -> Logs.

## Limits

- Until the switch-over, the PC must be on (or asleep, not shut down) at 07:30 for anything to happen;
  after it, only for fresh NBA stats.
- The task runs whatever branch is checked out in the repo; keep `main` checked out when idle.

## Draft values step (DATA-035)
- `draft-values` runs in every chain (cloud and PC), independent of the brief and optional: if it fails, the brief
  still goes out and the run log shows `draft-values degraded` with the reason.
- It refuses to replace the live values when the rebuild looks wrong (a strategy missing, ranks not 1..n, the row
  count moving > 20 %, or fewer than 5 of the old top 10 left). To accept a deliberate big change (e.g. a new shipped
  method), change `SHIPPED_METHOD` in `draft_publish.py` in a reviewed PR; if the guard still refuses, move the old
  file aside in the bucket first (owner action).
- It needs `GCP_PROJECT` on the job (Terraform `daily.tf`; CI sets the same value). Without it, it skips (0 rows).
