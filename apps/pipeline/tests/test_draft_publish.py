from pathlib import Path

import numpy as np
import polars as pl
import pytest

from fantasy_core.league import LeagueRules
from fantasy_ingest.yahoo_import import parse_league_settings
from fantasy_pipeline import draft_publish as dp
from fantasy_pipeline.workspace import Workspace

from .test_draft_values import FIX, FORMAT_FIXTURES, FakeWarehouse

TARGET = "2026-27"


def _rules() -> LeagueRules:
    for f in FORMAT_FIXTURES:
        rules = parse_league_settings((FIX / f).read_text(encoding="utf-8"))
        if rules.auction_budget and rules.scoring.uses_categories:
            return rules
    raise AssertionError


class BreakoutWarehouse(FakeWarehouse):
    def __init__(self, with_breakouts: bool = True) -> None:
        super().__init__()
        draft = self.tables[dp.DRAFT_SQL]
        rookie = draft.head(1).with_columns(
            pl.lit(999_001).cast(draft["nba_player_id"].dtype).alias("nba_player_id"),
            pl.lit(2026).cast(draft["draft_year"].dtype).alias("draft_year"),
            pl.lit(3).cast(draft["overall_pick"].dtype).alias("overall_pick"),
        )
        self.tables[dp.DRAFT_SQL] = pl.concat([draft, rookie])
        ids = self.tables[dp.SEASONS_SQL]["nba_player_id"].unique().head(20).to_list()
        self.tables[dp.BREAKOUT_SQL.format(season=TARGET)] = (
            pl.DataFrame(
                {
                    "nba_player_id": ids,
                    "kind": ["bounce_back"] * len(ids),
                    "p_breakout": [i / 40 for i in range(len(ids))],
                    "season": [TARGET] * len(ids),
                }
            )
            if with_breakouts
            else pl.DataFrame(
                schema={
                    "nba_player_id": pl.Int64,
                    "kind": pl.String,
                    "p_breakout": pl.Float64,
                    "season": pl.String,
                }
            )
        )


@pytest.fixture
def tables() -> dict[str, pl.DataFrame]:
    return dp.build(BreakoutWarehouse(), _rules(), TARGET, "H1+aging")


def test_build_returns_the_three_tables_with_the_contract_columns(
    tables: dict[str, pl.DataFrame],
) -> None:
    assert set(tables) == {dp.VALUES, dp.HISTORY, dp.BREAKOUTS, dp.CONSISTENCY, dp.ROLE}
    assert {"healthy_rank", "healthy_dollars", "overall_rank", "variant"} <= set(
        tables[dp.VALUES].columns
    )
    assert tables[dp.HISTORY].columns == [
        "nba_player_id",
        "season",
        "games_played",
        "season_team_games",
        "minutes",
        "age",
        "draft_year",
        "overall_pick",
    ]
    assert set(tables[dp.HISTORY]["season"].unique().to_list()) <= {
        "2023-24",
        "2024-25",
        "2025-26",
        None,  # rookies: a draft-only row
    }
    assert tables[dp.BREAKOUTS].columns == ["nba_player_id", "kind", "p_breakout", "season"]


def test_build_skips_an_empty_breakout_table() -> None:
    out = dp.build(BreakoutWarehouse(with_breakouts=False), _rules(), TARGET, "H1+aging")
    assert dp.BREAKOUTS not in out


def test_check_passes_a_healthy_rebuild_and_a_first_run(tables: dict[str, pl.DataFrame]) -> None:
    values = tables[dp.VALUES]
    assert dp.check(values, values) == []
    assert dp.check(values, None) == []


def test_check_tolerates_one_raised_player_jumping_to_first(
    tables: dict[str, pl.DataFrame],
) -> None:
    # DATA-036: a raise override moves one player up; the guard must not block the publish.
    values = tables[dp.VALUES]
    raised = values.with_columns(
        pl.when(pl.col("overall_rank") == pl.col("overall_rank").max().over("variant"))
        .then(0)
        .otherwise(pl.col("overall_rank"))
        .alias("overall_rank")
    ).with_columns(
        pl.col("overall_rank").rank("ordinal").over("variant").cast(values["overall_rank"].dtype)
    )
    assert dp.check(raised, values) == []


def test_check_names_each_failing_guard(tables: dict[str, pl.DataFrame]) -> None:
    values = tables[dp.VALUES]
    no_punt = values.filter(pl.col("variant") != "punt_ast")
    assert any("missing variants" in r for r in dp.check(no_punt, values))
    dup = values.with_columns(pl.lit(1).alias("overall_rank"))
    assert any("ranks are not 1..n" in r for r in dp.check(dup, None))
    small = values.group_by("variant").head(10)
    assert any("row count" in r for r in dp.check(small, values))
    flipped = values.with_columns(
        (pl.len().over("variant") + 1 - pl.col("overall_rank")).alias("overall_rank")
    )
    assert any("top 10" in r for r in dp.check(flipped, values))


def test_job_writes_only_when_the_checks_pass(tmp_path: Path) -> None:
    w = Workspace(str(tmp_path))
    n = dp.run_job(w, BreakoutWarehouse(), _rules(), TARGET, "H1+aging")
    assert n > 0
    for rel in (dp.VALUES, dp.HISTORY, dp.BREAKOUTS):
        assert w.exists(rel)
    # a broken rebuild must never replace a good live file
    good = w.read_parquet(dp.VALUES)

    class Broken(BreakoutWarehouse):
        pass

    def broken_build(*_: object, **__: object) -> dict[str, pl.DataFrame]:
        return {dp.VALUES: good.filter(pl.col("variant") == "all")}

    with pytest.raises(dp.PublishRefused, match="missing variants"):
        dp.run_job(w, Broken(), _rules(), TARGET, "H1+aging", build=broken_build)
    assert w.read_parquet(dp.VALUES).equals(good)


def test_history_carries_one_draft_only_row_per_rookie(tables: dict[str, pl.DataFrame]) -> None:
    hist = tables[dp.HISTORY]
    rookies = hist.filter(pl.col("season").is_null())
    assert rookies.height > 0  # the synthetic league drafts a 2026 class
    assert rookies["draft_year"].unique().to_list() == [2026]
    assert rookies["games_played"].null_count() == rookies.height
    assert rookies["nba_player_id"].is_unique().all()
    veterans = hist.filter(pl.col("season").is_not_null())
    assert not set(rookies["nba_player_id"]) & set(veterans["nba_player_id"])


def test_a_failed_write_leaves_the_live_values_untouched(tmp_path: Path) -> None:
    w = Workspace(str(tmp_path))
    dp.run_job(w, BreakoutWarehouse(), _rules(), TARGET, "H1+aging")
    before = w.read_parquet(dp.VALUES)

    class FailingHistory(Workspace):
        def write_parquet(self, rel: str, df: pl.DataFrame) -> None:
            if rel == dp.HISTORY:
                raise OSError("bucket unavailable")
            super().write_parquet(rel, df)

    shifted = before.with_columns(pl.col("dollars") + 1)  # a valid, different rebuild

    def rebuild(*_: object, **__: object) -> dict[str, pl.DataFrame]:
        return {dp.VALUES: shifted, dp.HISTORY: pl.DataFrame({"x": [1]})}

    with pytest.raises(OSError, match="bucket unavailable"):
        dp.run_job(
            FailingHistory(str(tmp_path)),
            BreakoutWarehouse(),
            _rules(),
            TARGET,
            "H1+aging",
            build=rebuild,
        )
    assert w.read_parquet(dp.VALUES).equals(before)


# ------------------------------------------------------------------ WEB-020 indicator inputs
def test_history_carries_age(tables: dict[str, pl.DataFrame]) -> None:
    hist = tables[dp.HISTORY].filter(pl.col("season").is_not_null())
    assert "age" in hist.columns
    assert hist["age"].null_count() == 0


def test_consistency_measures_week_to_week_swings(tables: dict[str, pl.DataFrame]) -> None:
    c = tables[dp.CONSISTENCY]
    assert c.columns == [
        "nba_player_id",
        "season",
        "weeks",
        "weekly_sd",
        "weekly_mean",
        "rel_sd",
        "pct",
    ]
    assert c["weekly_mean"].min() > 0  # type: ignore[operator]
    assert c["weeks"].min() >= dp.MIN_CONSISTENCY_WEEKS  # type: ignore[operator]
    assert c["pct"].min() >= 0  # type: ignore[operator]
    assert c["pct"].max() <= 1  # type: ignore[operator]
    assert c["nba_player_id"].is_unique().all()


def test_a_steadier_player_has_a_lower_weekly_sd() -> None:
    weeks = []
    for w in range(20):
        for pid, swing in ((1, 0.0), (2, 1.0)):
            scale = 2 * (1 + swing * (1 if w % 2 else -0.9))  # above the pool: positive mean
            weeks.append(
                {
                    "nba_player_id": pid,
                    "week": w,
                    "minutes": 100.0 * scale,
                    **dict.fromkeys(
                        (
                            "fgm",
                            "fga",
                            "fg3m",
                            "fg3a",
                            "ftm",
                            "fta",
                            "reb",
                            "ast",
                            "stl",
                            "blk",
                            "tov",
                            "pts",
                        ),
                        10.0 * scale,
                    ),
                }
            )
    others = [
        {
            "nba_player_id": 10 + i,
            "week": w,
            "minutes": 90.0,
            **dict.fromkeys(
                (
                    "fgm",
                    "fga",
                    "fg3m",
                    "fg3a",
                    "ftm",
                    "fta",
                    "reb",
                    "ast",
                    "stl",
                    "blk",
                    "tov",
                    "pts",
                ),
                8.0 + i,
            ),
        }
        for i in range(5)
        for w in range(20)
    ]
    c = dp.consistency(pl.DataFrame(weeks + others), "2025-26")
    rel = dict(zip(c["nba_player_id"].to_list(), c["rel_sd"].to_list(), strict=True))
    assert rel[1] < rel[2]


def test_relative_swing_is_sd_over_level_for_positive_contributors() -> None:
    stats = ("fgm", "fga", "fg3m", "fg3a", "ftm", "fta", "reb", "ast", "stl", "blk", "tov", "pts")
    rng = np.random.default_rng(3)
    rows = [
        {
            "nba_player_id": pid,
            "week": w,
            "minutes": 100.0,
            **{st: float(level * rng.uniform(0.6, 1.4)) for st in stats},
        }
        for w in range(20)
        for pid, level in enumerate((2.0, 5.0, 10.0, 20.0, 40.0), start=1)
    ]
    c = dp.consistency(pl.DataFrame(rows), "2025-26")
    assert c["weekly_mean"].min() > 0  # type: ignore[operator]
    assert (
        c.select(
            (pl.col("rel_sd") - pl.col("weekly_sd") / pl.col("weekly_mean")).abs().max()
        ).item()
        < 1e-12
    )
    assert len(c) < 5  # the below-average contributors (mean <= 0) are left out


def test_role_context_carries_the_minutes_models_drivers(tables: dict[str, pl.DataFrame]) -> None:
    role = tables[dp.ROLE]
    assert role.columns == ["nba_player_id", "changed_team", "vacated_min"]
    assert role["nba_player_id"].is_unique().all()
    assert set(role["changed_team"].unique().to_list()) <= {True, False}
