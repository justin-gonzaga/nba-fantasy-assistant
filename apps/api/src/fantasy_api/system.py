"""`/system`: health and data freshness."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Request

import fantasy_api
from fantasy_api.auth import current_user
from fantasy_api.schemas import Health, JobFreshness, Product, SystemFreshness
from fantasy_api.store import DataStore

router = APIRouter(prefix="/system", tags=["system"])


def store_of(request: Request) -> DataStore:
    store: DataStore = request.app.state.store
    return store


@router.get("/health")
def health() -> Health:
    return Health(status="ok", version=fantasy_api.__version__)


@router.get("/freshness", dependencies=[Depends(current_user)])
def freshness(request: Request) -> SystemFreshness:
    store = store_of(request)
    briefs = store.brief_days()
    products = [
        Product(name="week_projection", as_of=store.week_projection_as_of()),
        Product(name="brief", as_of=briefs[-1] if briefs else None),
    ]
    latest: dict[str, JobFreshness] = {}
    runs = [(datetime.fromisoformat(r["started_at"]), r) for r in store.job_runs()]
    for at, run in sorted(runs, key=lambda x: x[0]):  # by instant, whatever the offset
        prev = latest.get(run["job"])
        ok = run["status"] == "success"
        latest[run["job"]] = JobFreshness(
            job=run["job"],
            last_status=run["status"],
            last_run=at,
            last_success=at if ok else (prev.last_success if prev else None),
        )
    return SystemFreshness(products=products, jobs=sorted(latest.values(), key=lambda j: j.job))
