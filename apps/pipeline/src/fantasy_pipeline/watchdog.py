"""INFRA-005 (G-27 A): a watchdog that notices what the daily job can't report about itself.

- `daily_checks` (09:00 Sydney): did today's 07:45 run happen at all? Is the PC's NBA data stale for
  two or more days? One Telegram message per problem per day.
- `uptime_checks` (every 15 min): is the website / API up? Alert when down on two checks in a row
  (so a deploy's restart never alerts), once, then "recovered".
State lives in the workspace (`ops/watchdog_state.json`), next to the run log.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fantasy_pipeline.workspace import Workspace

RUNS = "ops/job_runs.jsonl"
WEEK = "predictions/week_projection.parquet"
STATE = "ops/watchdog_state.json"
SYDNEY = ZoneInfo("Australia/Sydney")
STALE_GRACE_DAYS = 2
LABELS = {"site": "Site", "api": "API"}

Send = Callable[[str], None]


def _load(w: Workspace) -> dict[str, dict[str, str]]:
    if not w.exists(STATE):
        return {"alerted": {}, "down_since": {}, "down_alerted": {}}
    try:
        state: dict[str, dict[str, str]] = json.loads(w.read_text(STATE))
    except (ValueError, OSError):  # a truncated or corrupt state file must not stop the watchdog
        return {"alerted": {}, "down_since": {}, "down_alerted": {}}
    for key in ("alerted", "down_since", "down_alerted"):
        state.setdefault(key, {})
    return state


def _save(w: Workspace, state: dict[str, dict[str, str]]) -> None:
    w.write_text(STATE, json.dumps(state, sort_keys=True))


def _once_a_day(
    state: dict[str, dict[str, str]], kind: str, today: date, send: Send, text: str
) -> None:
    if state["alerted"].get(kind) == today.isoformat():
        return
    if _sent(send, text):  # a failed send is retried at the next check, not marked as done
        state["alerted"][kind] = today.isoformat()


def _sent(send: Send, text: str) -> bool:
    try:
        send(text)
    except Exception:
        return False
    return True


def _ran_today(w: Workspace, today: date) -> bool:
    if not w.exists(RUNS):
        return False
    for line in w.read_text(RUNS).splitlines():
        if not line.strip():
            continue
        started = datetime.fromisoformat(json.loads(line)["started_at"])
        if started.astimezone(SYDNEY).date() == today:
            return True
    return False


def _stale_since(w: Workspace) -> date | None:
    if not w.exists(WEEK):
        return None
    week = w.read_parquet(WEEK)
    if "stale_since" not in week.columns or week.height == 0:
        return None
    value = week["stale_since"].drop_nulls()
    return value[0] if len(value) else None


def daily_checks(w: Workspace, now: datetime, send: Send, *, muted: bool) -> None:
    if muted:
        return
    today = now.astimezone(SYDNEY).date()
    state = _load(w)
    if not _ran_today(w, today):
        _once_a_day(
            state,
            "no_run",
            today,
            send,
            "No daily run today (expected 07:45 Sydney). Check the Cloud Run job 'daily'.",
        )
    stale = _stale_since(w)
    if stale is not None and (today - stale).days >= STALE_GRACE_DAYS:
        day = f"{stale:%a} {stale.day} {stale:%b}"
        _once_a_day(
            state, "stale", today, send, f"NBA data stale since {day}: check the PC's 07:30 fetch."
        )
    _save(w, state)


def uptime_checks(
    w: Workspace, now: datetime, probe: Callable[[str], bool], send: Send, *, muted: bool
) -> None:
    state = _load(w)
    for name, label in LABELS.items():
        up = probe(name)
        since = state["down_since"].get(name)
        if up:
            # keep the "down" mark until the recovery message is delivered (retried otherwise)
            if name in state["down_alerted"] and (muted or _sent(send, f"{label} recovered.")):
                state["down_alerted"].pop(name)
            state["down_since"].pop(name, None)
            continue
        if since is None:
            state["down_since"][name] = now.isoformat()  # first failure: maybe a deploy blip
            continue
        if name not in state["down_alerted"] and now - datetime.fromisoformat(since) >= timedelta(
            minutes=10
        ):
            start = datetime.fromisoformat(since).astimezone(SYDNEY)
            if muted or _sent(send, f"{label} down since {start:%H:%M} Sydney."):
                state["down_alerted"][name] = now.isoformat()
    _save(w, state)


def http_probe(urls: Mapping[str, str], get_status: Callable[[str], int]) -> Callable[[str], bool]:
    """A probe from URLs and a status fetcher; any error or non-2xx/3xx counts as down."""

    def probe(name: str) -> bool:
        try:
            return 200 <= get_status(urls[name]) < 400  # noqa: PLR2004
        except Exception:
            return False

    return probe
