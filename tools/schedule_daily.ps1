# Registers the morning run at 07:30 local time (Sydney), ~4:30 PM US Eastern: after the afternoon
# injury reports, before tip-off. The PC wakes for it if asleep; a missed run starts as soon as possible.
#   -Mode daily (default): the whole chain on this PC (MVP-005).
#   -Mode fetch: only the NBA download (D-63, INFRA-008): the NBA blocks cloud IPs, so the PC fetches
#                and the Cloud Run job "daily" does the rest at 07:45. Needs DATA_ROOT=gs://<prefix>-dev-raw.
# Usage (once):   powershell -NoProfile -File tools\schedule_daily.ps1 [-Mode fetch]
# Remove:         Unregister-ScheduledTask -TaskName "NBA Fantasy daily brief" -Confirm:$false
param([string]$At = "07:30", [ValidateSet("daily", "fetch")][string]$Mode = "daily")

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$uv = (Get-Command uv).Source
New-Item -ItemType Directory -Force -Path (Join-Path $repo "data\logs") | Out-Null
$log = Join-Path $repo "data\logs\daily-run.log"
$run = if ($Mode -eq "fetch") { "run fetch" } else { "daily-run" }
$cmd = "Set-Location '$repo'; & '$uv' run python -m fantasy_pipeline $run *>> '$log'"

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -Command `"$cmd`""
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$settings = New-ScheduledTaskSettingsSet -WakeToRun -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
$what = if ($Mode -eq "fetch") { "INFRA-008: the NBA download for the cloud chain" } else { "MVP-005: the whole morning chain" }
Register-ScheduledTask -TaskName "NBA Fantasy daily brief" -Action $action -Trigger $trigger -Settings $settings -Description $what -Force | Out-Null
Get-ScheduledTask -TaskName "NBA Fantasy daily brief" | Select-Object TaskName, State
