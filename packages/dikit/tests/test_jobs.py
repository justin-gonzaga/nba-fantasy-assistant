from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from dikit import jobs
from dikit.time.clock import FrozenClock

NOW = datetime(2026, 10, 25, 20, tzinfo=UTC)


def _registry(log: list[str], fail: set[str] | None = None) -> jobs.Registry:
    fail = fail or set()

    def make(name: str) -> jobs.JobFn:
        def run(partition: date | None) -> int:
            log.append(f"{name}:{partition}")
            if name in fail:
                raise RuntimeError(f"{name} broke")
            return 3

        return run

    reg = jobs.Registry()
    reg.add(jobs.Job("fetch", make("fetch"), partitioned=True))
    reg.add(jobs.Job("project", make("project"), deps=("fetch",)))
    reg.add(jobs.Job("brief", make("brief"), deps=("project",)))
    reg.add(jobs.Job("extra", make("extra"), deps=("fetch",), optional=True))
    return reg


def test_jobs_run_in_dependency_order_and_results_are_recorded() -> None:
    log: list[str] = []
    sink = jobs.MemorySink()
    runner = jobs.Runner(_registry(log), sink, FrozenClock(NOW))
    results = runner.run(["brief", "extra"], partitions=[date(2026, 10, 24)])
    assert log == ["fetch:2026-10-24", "project:None", "brief:None", "extra:None"]
    assert {r.job for r in results} == {"fetch", "project", "brief", "extra"}
    assert all(r.status == "success" for r in results)
    assert all(r.rows == 3 for r in results)
    assert len(sink.rows) == 4
    assert len({r.run_id for r in results}) == 1


def test_a_failure_skips_dependents_but_optional_failures_only_degrade() -> None:
    log: list[str] = []
    runner = jobs.Runner(_registry(log, fail={"extra"}), jobs.MemorySink(), FrozenClock(NOW))
    by_job = {
        r.job: r.status for r in runner.run(["brief", "extra"], partitions=[date(2026, 10, 24)])
    }
    assert by_job["extra"] == "degraded"
    assert by_job["brief"] == "success"

    log2: list[str] = []
    runner2 = jobs.Runner(_registry(log2, fail={"fetch"}), jobs.MemorySink(), FrozenClock(NOW))
    by_job2 = {r.job: r for r in runner2.run(["brief"], partitions=[date(2026, 10, 24)])}
    assert by_job2["fetch"].status == "failed"
    assert "fetch broke" in (by_job2["fetch"].error or "")
    assert by_job2["project"].status == "skipped"
    assert by_job2["brief"].status == "skipped"
    assert jobs.overall([*by_job2.values()]) == "failed"


def test_unknown_jobs_and_cycles_are_rejected() -> None:
    reg = jobs.Registry()
    reg.add(jobs.Job("a", lambda _p: 0, deps=("b",)))
    reg.add(jobs.Job("b", lambda _p: 0, deps=("a",)))
    with pytest.raises(ValueError, match="cycle"):
        reg.order(["a"])
    with pytest.raises(KeyError):
        reg.order(["nope"])


def test_catch_up_covers_every_missing_day_since_the_last_success() -> None:
    sink = jobs.MemorySink()
    runner = jobs.Runner(_registry([]), sink, FrozenClock(NOW))
    runner.run(["fetch"], partitions=[date(2026, 10, 21)])
    missing = jobs.missing_partitions(sink, "fetch", through=date(2026, 10, 24), max_days=14)
    assert missing == [date(2026, 10, 22), date(2026, 10, 23), date(2026, 10, 24)]


def test_catch_up_with_no_history_starts_at_the_latest_day_only() -> None:
    assert jobs.missing_partitions(
        jobs.MemorySink(), "fetch", through=date(2026, 10, 24), max_days=14
    ) == [date(2026, 10, 24)]


def test_catch_up_is_capped() -> None:
    sink = jobs.MemorySink()
    jobs.Runner(_registry([]), sink, FrozenClock(NOW)).run(["fetch"], partitions=[date(2026, 9, 1)])
    missing = jobs.missing_partitions(sink, "fetch", through=date(2026, 10, 24), max_days=5)
    assert missing == [date(2026, 10, 20 + i) for i in range(5)]


def test_the_lock_prevents_a_second_concurrent_run(tmp_path: Path) -> None:
    lock = tmp_path / "run.lock"
    with jobs.RunLock(lock, FrozenClock(NOW)), pytest.raises(jobs.LockHeldError):
        jobs.RunLock(lock, FrozenClock(NOW)).__enter__()
    with jobs.RunLock(lock, FrozenClock(NOW)):  # released afterwards
        pass


def test_a_stale_lock_is_taken_over(tmp_path: Path) -> None:
    lock = tmp_path / "run.lock"
    lock.write_text("2026-10-25T10:00:00+00:00", encoding="utf-8")  # 10 hours before NOW
    with jobs.RunLock(lock, FrozenClock(NOW), stale_after_hours=2):
        assert lock.exists()
    assert not lock.exists()


def test_jsonl_sink_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "ops" / "job_runs.jsonl"
    sink = jobs.JsonlSink(path)
    jobs.Runner(_registry([]), sink, FrozenClock(NOW)).run(
        ["fetch"], partitions=[date(2026, 10, 24)]
    )
    again = jobs.JsonlSink(path)
    assert [r.job for r in again.history()] == ["fetch"]
    assert again.history()[0].partition == date(2026, 10, 24)
