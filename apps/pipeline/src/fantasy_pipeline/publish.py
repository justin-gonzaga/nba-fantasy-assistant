"""Publish the day's outputs to the serve root the API reads (D-62, INFRA-004).

When the chain's workspace is local (the owner's PC), this copies the files the API needs to
`gs://<prefix>-<env>-serve`, keeping the same layout. The cloud job's workspace is the serve bucket
itself, so nothing needs copying there (INFRA-006).
"""

from __future__ import annotations

from datetime import date

from fantasy_pipeline.workspace import Workspace


def files_for(day: date) -> list[str]:
    return [
        f"briefs/{day.isoformat()}.json",
        f"briefs/{day.isoformat()}.md",
        "predictions/week_projection.parquet",
        "predictions/auction_values.parquet",  # DATA-035: draft values + badge inputs
        "predictions/player_history.parquet",
        "predictions/breakout_probability.parquet",
        "predictions/player_consistency.parquet",  # WEB-020
        "predictions/role_context.parquet",
        "ops/job_runs.jsonl",
    ]


def publish(source: Workspace, serve_root: str, day: date) -> int:
    """Copy the day's published files; returns how many were copied (missing ones are skipped)."""
    target = Workspace(serve_root)
    copied = 0
    for rel in files_for(day):
        if not source.exists(rel):
            continue
        data = bytes(source.fs.cat_file(source.url(rel)))
        target.fs.makedirs(target.url(rel).rsplit("/", 1)[0], exist_ok=True)
        target.fs.pipe_file(target.url(rel), data)
        copied += 1
    return copied
