"""BigQuery access for pipeline jobs: read warehouse tables as Polars, write prediction tables."""

from __future__ import annotations

import io
from typing import Protocol

import polars as pl


class Warehouse(Protocol):
    def read(self, sql: str) -> pl.DataFrame: ...

    def write(self, df: pl.DataFrame, table: str) -> None: ...


class BigQueryWarehouse:  # pragma: no cover - needs GCP; exercised by the live runs in DRAFT-002
    def __init__(self, project: str) -> None:
        from google.cloud import bigquery  # noqa: PLC0415 - heavy import only when used

        self._bq = bigquery
        self._client = bigquery.Client(project=project)
        self.project = project

    def read(self, sql: str) -> pl.DataFrame:
        table = self._client.query(sql).result().to_arrow(create_bqstorage_client=False)
        return pl.from_arrow(table)  # type: ignore[return-value]

    def write(self, df: pl.DataFrame, table: str) -> None:
        buf = io.BytesIO()
        df.write_parquet(buf)
        buf.seek(0)
        job = self._client.load_table_from_file(
            buf,
            f"{self.project}.{table}",
            job_config=self._bq.LoadJobConfig(
                source_format=self._bq.SourceFormat.PARQUET,
                write_disposition=self._bq.WriteDisposition.WRITE_TRUNCATE,
            ),
        )
        job.result()


PRESEASON_SQL = (
    "select season, nba_player_id, pre_games, pre_mpg, pre_team_minutes_share, pre_start_share"
    " from intermediate.int_preseason_role"
)
SEASONS_SQL = "select * from intermediate.int_player_season"
DRAFT_SQL = "select nba_player_id, draft_year, overall_pick from staging.stg_nba_stats__draft_pick"
PROFILE_SQL = (
    "select nba_player_id, player_name, nba_team_id, overall_pick, age_at_midseason"
    " from intermediate.int_player_profile"
)
