"""Job runner (FND-011): a registry of jobs with dependencies, run in order, with results
recorded, a single-writer lock and catch-up of missed daily partitions (architecture §4.4).

- A job is `fn(partition) -> rows`. Partitioned jobs run once per partition (a game date);
  the others run once, after every partition of their dependencies.
- A failing job skips everything downstream of it; a failing *optional* job is marked `degraded`
  and its dependents still run.
- Every run records one JobResult per job run (run_id, job, partition, status, rows, duration).
- Catch-up: the partitions since the job's last success, up to a cap, oldest first.
Domain-agnostic: each product registers its own jobs in its app.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Literal, Protocol

import fsspec

from dikit.time.clock import Clock

Status = Literal["success", "failed", "degraded", "skipped"]
JobFn = Callable[[date | None], int]


@dataclass(frozen=True)
class Job:
    name: str
    fn: JobFn
    deps: tuple[str, ...] = ()
    partitioned: bool = False
    optional: bool = False


@dataclass(frozen=True)
class JobResult:
    run_id: str
    job: str
    partition: date | None
    status: Status
    rows: int
    seconds: float
    started_at: datetime
    error: str | None = None


class Sink(Protocol):
    def write(self, result: JobResult) -> None: ...
    def history(self) -> list[JobResult]: ...


@dataclass
class MemorySink:
    rows: list[JobResult] = field(default_factory=list)

    def write(self, result: JobResult) -> None:
        self.rows.append(result)

    def history(self) -> list[JobResult]:
        return list(self.rows)


class JsonlSink:
    """Local run log (one JSON object per line). The BigQuery `ops.job_runs` sink follows with
    the ops dataset (INFRA follow-up); both implement Sink."""

    def __init__(self, path: Path | str) -> None:
        """`path`: a local path or any fsspec URL (e.g. gs://bucket/ops/job_runs.jsonl)."""
        self.path = path
        self._fs, self._target = fsspec.core.url_to_fs(str(path))

    def write(self, result: JobResult) -> None:
        row = asdict(result)
        row["partition"] = result.partition.isoformat() if result.partition else None
        row["started_at"] = result.started_at.isoformat()
        line = json.dumps(row) + "\n"
        parent = self._target.rsplit("/", 1)[0] if "/" in self._target else ""
        if parent:
            self._fs.makedirs(parent, exist_ok=True)
        try:
            with self._fs.open(self._target, "a", encoding="utf-8") as f:
                f.write(line)
        except (
            NotImplementedError,
            ValueError,
            FileNotFoundError,
        ):  # object stores can't append: rewrite
            old = (
                self._fs.cat_file(self._target).decode("utf-8")
                if self._fs.exists(self._target)
                else ""
            )
            self._fs.pipe_file(self._target, (old + line).encode("utf-8"))

    def history(self) -> list[JobResult]:
        if not self._fs.exists(self._target):
            return []
        out = []
        for line in self._fs.cat_file(self._target).decode("utf-8").splitlines():
            r = json.loads(line)
            r["partition"] = date.fromisoformat(r["partition"]) if r["partition"] else None
            r["started_at"] = datetime.fromisoformat(r["started_at"])
            out.append(JobResult(**r))
        return out


class Registry:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}

    def add(self, job: Job) -> None:
        self._jobs[job.name] = job

    def get(self, name: str) -> Job:
        return self._jobs[name]

    def order(self, targets: Iterable[str]) -> list[Job]:
        """The targets and everything they depend on, dependencies first."""
        done: list[str] = []
        visiting: set[str] = set()

        def visit(name: str) -> None:
            if name in done:
                return
            if name in visiting:
                msg = f"dependency cycle through {name!r}"
                raise ValueError(msg)
            visiting.add(name)
            for dep in self._jobs[name].deps:
                visit(dep)
            visiting.discard(name)
            done.append(name)

        for t in targets:
            visit(t)
        return [self._jobs[n] for n in done]


def overall(results: Sequence[JobResult]) -> Status:
    """failed if anything failed or was skipped, else degraded if anything was, else success."""
    statuses = {r.status for r in results}
    if statuses & {"failed", "skipped"}:
        return "failed"
    return "degraded" if "degraded" in statuses else "success"


class Runner:
    def __init__(self, registry: Registry, sink: Sink, clock: Clock) -> None:
        self.registry = registry
        self.sink = sink
        self.clock = clock

    def _one(self, run_id: str, job: Job, partition: date | None) -> JobResult:
        started, t0 = self.clock.now(), time.perf_counter()
        try:
            rows = job.fn(partition)
            status: Status = "success"
            error = None
        except Exception as err:  # a job failure is recorded, never propagated
            rows, error = 0, f"{type(err).__name__}: {err}"
            status = "degraded" if job.optional else "failed"
        return JobResult(
            run_id, job.name, partition, status, rows, time.perf_counter() - t0, started, error
        )

    def run(self, targets: Sequence[str], *, partitions: Sequence[date]) -> list[JobResult]:
        run_id = uuid.uuid4().hex[:12]
        blocked: set[str] = set()
        results: list[JobResult] = []
        for job in self.registry.order(targets):
            parts: list[date | None] = list(partitions) if job.partitioned else [None]
            if any(d in blocked for d in job.deps):
                job_results = [
                    JobResult(
                        run_id, job.name, p, "skipped", 0, 0.0, self.clock.now(), "upstream failed"
                    )
                    for p in parts
                ]
            else:
                job_results = [self._one(run_id, job, p) for p in parts]
            if any(r.status in {"failed", "skipped"} for r in job_results):
                blocked.add(job.name)
            for r in job_results:
                self.sink.write(r)
            results += job_results
        return results


def missing_partitions(sink: Sink, job: str, *, through: date, max_days: int) -> list[date]:
    """Days after the job's last successful partition, up to `through`, oldest first, at most
    `max_days` (the most recent ones). With no history: just `through`."""
    done = [
        r.partition
        for r in sink.history()
        if r.job == job and r.status == "success" and r.partition
    ]
    if not done:
        return [through]
    start = max(done) + timedelta(days=1)
    days = [start + timedelta(days=i) for i in range((through - start).days + 1)]
    return days[-max_days:]


class LockHeldError(RuntimeError):
    pass


class RunLock:
    """Single-writer lock file. A lock older than `stale_after_hours` (a crashed run) is
    taken over."""

    def __init__(self, path: Path, clock: Clock, *, stale_after_hours: float = 2.0) -> None:
        self.path, self.clock, self.stale = path, clock, timedelta(hours=stale_after_hours)

    def __enter__(self) -> RunLock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            held_since = datetime.fromisoformat(self.path.read_text(encoding="utf-8").strip())
            if self.clock.now() - held_since < self.stale:
                msg = f"another run holds {self.path} since {held_since.isoformat()}"
                raise LockHeldError(msg)
            self.path.unlink()
        with self.path.open("x", encoding="utf-8") as f:  # fails if another process just took it
            f.write(self.clock.now().isoformat())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.path.unlink(missing_ok=True)
