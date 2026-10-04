from pathlib import Path

import polars as pl
import pytest
from typer.testing import CliRunner

from fantasy_models.preseason.schema import PER_GAME_STATS
from fantasy_models.preseason.synthetic import make_league
from fantasy_pipeline import cli, draft_projection
from fantasy_pipeline.warehouse import DRAFT_SQL, PROFILE_SQL, SEASONS_SQL


class FakeWarehouse:
    def __init__(self) -> None:
        seasons, draft = make_league(seed=5, n_players=200, last=2025)
        self.tables = {
            SEASONS_SQL: seasons,
            DRAFT_SQL: draft,
            # the 2026-27 pool: everyone who played 2025-26 plus two unseen rookies
            PROFILE_SQL: pl.concat(
                [
                    seasons.filter(pl.col("season") == "2025-26").select(
                        "nba_player_id", pl.lit(None, pl.Int64).alias("overall_pick")
                    ),
                    pl.DataFrame(
                        {"nba_player_id": [9001, 9002], "overall_pick": [3, None]},
                        schema={"nba_player_id": pl.Int64, "overall_pick": pl.Int64},
                    ),
                ]
            ),
        }
        self.written: dict[str, pl.DataFrame] = {}

    def read(self, sql: str) -> pl.DataFrame:
        return self.tables[sql]

    def write(self, df: pl.DataFrame, table: str) -> None:
        self.written[table] = df


def test_backtest_runs_rolling_folds_and_decides() -> None:
    md, decision, folds = draft_projection.run_backtest(
        FakeWarehouse(), "2023-24", "2025-26", n_boot=100
    )
    assert [f.target for f in folds] == ["2023-24", "2024-25", "2025-26"]
    assert decision.method in {"B0", "B1", "C1", "H1"}
    assert "## Decision (primary fold 2025-26)" in md


def test_projections_cover_the_pool_with_mean_and_sd() -> None:
    wh = FakeWarehouse()
    long, coverage = draft_projection.build_projections(wh, "2026-27", "H1")
    pool = wh.tables[PROFILE_SQL].get_column("nba_player_id").n_unique()
    assert coverage == (pool, pool)
    assert long.get_column("nba_player_id").n_unique() == pool
    assert set(long.get_column("stat")) == {"mpg", "games", *PER_GAME_STATS}
    assert long.filter(pl.col("sd").is_null() | pl.col("mean").is_null()).height == 0
    assert set(long.get_column("method")) == {"H1"}
    assert long.get_column("season").unique().to_list() == ["2026-27"]
    rookies = long.filter(pl.col("nba_player_id").is_in([9001, 9002]))
    assert set(rookies.get_column("source")) == {"rookie_prior"}


def test_unknown_method_rejected() -> None:
    with pytest.raises(ValueError, match="method"):
        draft_projection.build_projections(FakeWarehouse(), "2026-27", "XGB")


def test_cli_backtest_and_projections(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wh = FakeWarehouse()
    monkeypatch.setattr(cli, "make_warehouse", lambda _project: wh)
    report = tmp_path / "report.md"
    runner = CliRunner()
    r = runner.invoke(
        cli.app,
        [
            "draft-backtest",
            "--first-target",
            "2024-25",
            "--last-target",
            "2025-26",
            "--n-boot",
            "100",
            "--out",
            str(report),
        ],
    )
    assert r.exit_code == 0, r.output
    assert report.exists()
    assert "decision=" in r.output
    out = tmp_path / "proj.parquet"
    r = runner.invoke(cli.app, ["draft-projections", "--method", "B1", "--parquet", str(out)])
    assert r.exit_code == 0, r.output
    assert "coverage=100.0%" in r.output
    assert "predictions.preseason_projection" in wh.written
    assert pl.read_parquet(out).height == wh.written["predictions.preseason_projection"].height
