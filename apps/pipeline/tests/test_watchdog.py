import json
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from fantasy_pipeline import watchdog as wd
from fantasy_pipeline.workspace import Workspace

# 09:00 Sydney on Sat 3 Oct 2026 = 23:00 UTC on Fri 2 Oct
MORNING = datetime(2026, 10, 2, 23, 0, tzinfo=UTC)


def _work(tmp_path: Path, runs: list[dict[str, object]] | None = None) -> Workspace:
    w = Workspace(str(tmp_path))
    if runs is not None:
        w.write_text(wd.RUNS, "".join(json.dumps(r) + "\n" for r in runs))
    return w


def _run(started: str, job: str = "brief", status: str = "success") -> dict[str, object]:
    return {"job": job, "status": status, "started_at": started, "rows": 1}


class Sent:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, text: str) -> None:
        self.messages.append(text)


def test_no_run_today_alerts_once(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-01T21:45:30+00:00")])  # yesterday's 07:45 run only
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert sent.messages == [
        "No daily run today (expected 07:45 Sydney). Check the Cloud Run job 'daily'."
    ]
    wd.daily_checks(w, MORNING, sent, muted=False)  # a second check the same day
    assert len(sent.messages) == 1


def test_todays_run_means_no_alert(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-02T21:45:30+00:00")])  # 07:45 Sydney today
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert sent.messages == []


def test_muted_never_alerts(tmp_path: Path) -> None:
    sent = Sent()
    wd.daily_checks(_work(tmp_path, []), MORNING, sent, muted=True)
    assert sent.messages == []


def test_stale_nba_data_alerts_after_two_days(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-02T21:45:30+00:00")])
    w.write_parquet(
        wd.WEEK,
        pl.DataFrame({"nba_player_id": [1], "stale_since": [date(2026, 10, 1)]}),
    )
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert sent.messages == ["NBA data stale since Thu 1 Oct: check the PC's 07:30 fetch."]


def test_stale_without_games_or_recent_does_not_alert(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-02T21:45:30+00:00")])
    w.write_parquet(
        wd.WEEK, pl.DataFrame({"nba_player_id": [1], "stale_since": [date(2026, 10, 2)]})
    )
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)  # only yesterday: within the 2-day grace
    w.write_parquet(
        wd.WEEK,
        pl.DataFrame({"nba_player_id": [1], "stale_since": pl.Series([None], dtype=pl.Date)}),
    )
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert sent.messages == []


def test_uptime_alerts_after_ten_minutes_and_on_recovery(tmp_path: Path) -> None:
    w = _work(tmp_path)
    sent = Sent()
    down = {"site": False, "api": True}

    def probe(name: str) -> bool:
        return down[name]

    t0 = datetime(2026, 10, 3, 1, 0, tzinfo=UTC)
    wd.uptime_checks(w, t0, probe, sent, muted=False)  # first failure: wait (a deploy blip?)
    assert sent.messages == []
    wd.uptime_checks(w, t0.replace(minute=15), probe, sent, muted=False)
    assert sent.messages == ["Site down since 11:00 Sydney."]
    wd.uptime_checks(w, t0.replace(minute=30), probe, sent, muted=False)  # still down: no repeat
    assert len(sent.messages) == 1
    down["site"] = True
    wd.uptime_checks(w, t0.replace(minute=45), probe, sent, muted=False)
    assert sent.messages[-1] == "Site recovered."


def test_a_blip_never_alerts(tmp_path: Path) -> None:
    w = _work(tmp_path)
    sent = Sent()
    state = {"api": False}
    t0 = datetime(2026, 10, 3, 1, 0, tzinfo=UTC)
    wd.uptime_checks(w, t0, lambda n: n != "api" or state["api"], sent, muted=False)
    state["api"] = True
    wd.uptime_checks(w, t0.replace(minute=15), lambda n: True, sent, muted=False)
    assert sent.messages == []


def test_probe_treats_errors_as_down() -> None:
    def boom(url: str) -> int:
        raise OSError("timeout")

    assert wd.http_probe({"site": "https://x"}, boom)("site") is False
    assert wd.http_probe({"site": "https://x"}, lambda u: 200)("site") is True
    assert wd.http_probe({"site": "https://x"}, lambda u: 503)("site") is False


def test_a_corrupt_state_file_starts_fresh(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-01T21:45:30+00:00")])
    w.write_text(wd.STATE, "{not json")
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert len(sent.messages) == 1


def test_a_failed_send_is_retried_next_time(tmp_path: Path) -> None:
    w = _work(tmp_path, [_run("2026-10-01T21:45:30+00:00")])

    def down(_text: str) -> None:
        raise OSError("telegram down")

    wd.daily_checks(w, MORNING, down, muted=False)
    sent = Sent()
    wd.daily_checks(w, MORNING, sent, muted=False)
    assert len(sent.messages) == 1  # not marked as sent the first time


def test_a_failed_recovery_message_is_retried(tmp_path: Path) -> None:
    w = _work(tmp_path)
    sent = Sent()
    up = {"site": False}
    t0 = datetime(2026, 10, 3, 1, 0, tzinfo=UTC)
    wd.uptime_checks(w, t0, lambda n: n != "site" or up["site"], sent, muted=False)
    wd.uptime_checks(
        w, t0.replace(minute=15), lambda n: n != "site" or up["site"], sent, muted=False
    )
    up["site"] = True

    def down(_text: str) -> None:
        raise OSError("telegram down")

    wd.uptime_checks(w, t0.replace(minute=30), lambda n: True, down, muted=False)
    wd.uptime_checks(w, t0.replace(minute=45), lambda n: True, sent, muted=False)
    assert sent.messages[-1] == "Site recovered."
