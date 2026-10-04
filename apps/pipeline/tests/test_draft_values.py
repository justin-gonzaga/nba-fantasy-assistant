from pathlib import Path

import numpy as np
import polars as pl
import pytest
from polars.testing import assert_frame_equal
from typer.testing import CliRunner

from fantasy_core.league import LeagueRules
from fantasy_ingest.yahoo_import import parse_league_settings
from fantasy_models.preseason.synthetic import make_league
from fantasy_pipeline import cli, draft_values
from fantasy_pipeline.draft_projection import ROSTER_SQL
from fantasy_pipeline.warehouse import DRAFT_SQL, SEASONS_SQL

FIX = Path(__file__).parents[3] / "packages" / "ingest" / "tests" / "fixtures" / "yahoo_import"
FORMAT_FIXTURES = sorted(p.name for p in FIX.glob("league_settings_*.txt"))


class FakeWarehouse:
    def __init__(self) -> None:
        seasons, draft = make_league(seed=9, n_players=400, last=2025)
        last = seasons.filter(pl.col("season") == "2025-26")
        rng = np.random.default_rng(0)
        weeks = []
        for w in range(20):  # split last season into 20 noisy weeks
            share = rng.uniform(0.02, 0.08, last.height)
            weeks.append(
                last.select(
                    "nba_player_id",
                    pl.lit(w).alias("week"),
                    *[
                        (pl.col(c) * pl.Series(share)).alias(c)
                        for c in (
                            "minutes",
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
                        )
                    ],
                )
            )
        positions = ["G", "F", "C", "G-F", "F-C", None]
        self.tables = {
            SEASONS_SQL: seasons,
            DRAFT_SQL: draft,
            draft_values.WEEKLY_SQL.format(season="2025-26"): pl.concat(weeks),
            draft_values.POSITIONS_SQL: last.select(
                "nba_player_id",
                pl.format("P{}", pl.col("nba_player_id")).alias("player_name"),
                pl.Series("nba_position", [positions[i % 6] for i in range(last.height)]),
            ),
        }
        self.tables[ROSTER_SQL] = last.select(
            "nba_player_id", pl.col("last_nba_team_id").alias("team")
        )
        self.written: dict[str, pl.DataFrame] = {}

    def read(self, sql: str) -> pl.DataFrame:
        return self.tables[sql]

    def write(self, df: pl.DataFrame, table: str) -> None:
        self.written[table] = df


@pytest.mark.parametrize("fixture", FORMAT_FIXTURES)
def test_valuation_formats(fixture: str) -> None:
    """AC1: the pasted settings of each of the 5 formats drive a complete valuation."""
    assert len(FORMAT_FIXTURES) == 5
    rules = parse_league_settings((FIX / fixture).read_text(encoding="utf-8"))
    values = draft_values.build_values(FakeWarehouse(), rules, "2026-27", "H1+aging")
    allv = values.filter(pl.col("variant") == "all")
    assert allv.filter(pl.col("drafted")).height == rules.pool_size
    if rules.auction_budget:
        assert allv.filter(pl.col("drafted")).get_column("dollars").sum() == pytest.approx(
            rules.teams * rules.auction_budget
        )
    else:
        assert allv.get_column("dollars").null_count() == allv.height


def test_within_week_variance_is_positive_per_category() -> None:
    wh = FakeWarehouse()
    rules = parse_league_settings(
        (FIX / "league_settings_h2h9cat_auction.txt").read_text(encoding="utf-8")
    )
    var = draft_values.within_week_variance(
        wh.tables[draft_values.WEEKLY_SQL.format(season="2025-26")], rules, 224
    )
    assert set(var) == {c.code for c in rules.categories}
    assert all(v > 0 for v in var.values())


def test_cli_draft_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    wh = FakeWarehouse()
    monkeypatch.setattr(cli, "make_warehouse", lambda _project: wh)
    out = tmp_path / "values.parquet"
    r = CliRunner().invoke(
        cli.app,
        [
            "draft-values",
            "--settings",
            str(FIX / "league_settings_h2h9cat_auction.txt"),
            "--parquet",
            str(out),
        ],
    )
    assert r.exit_code == 0, r.output
    assert "format=h2h_categories teams=16 pool=224" in r.output
    assert "predictions.auction_values" in wh.written
    assert out.exists()


def test_preseason_method_needs_the_target_preseason() -> None:
    """DRAFT-008: H1+aging+M1pre refuses to guess when the target's pre-season isn't ingested."""
    from fantasy_pipeline import draft_projection as dp  # noqa: PLC0415
    from fantasy_pipeline.warehouse import PRESEASON_SQL  # noqa: PLC0415

    wh = FakeWarehouse()
    wh.tables[PRESEASON_SQL] = pl.DataFrame(
        {
            "season": ["2025-26"],
            "nba_player_id": [1],
            "pre_games": [3],
            "pre_mpg": [20.0],
            "pre_team_minutes_share": [0.1],
            "pre_start_share": [0.5],
        }
    )
    seasons, _ = dp._inputs(wh)
    with pytest.raises(ValueError, match="pre-season"):
        dp.resolve_method(wh, seasons, dp.M1_PRE_METHOD, "2026-27")
    last = seasons.filter(pl.col("season") == "2025-26")
    wh.tables[PRESEASON_SQL] = last.select(
        pl.lit("2026-27").alias("season"),
        "nba_player_id",
        pl.lit(4).alias("pre_games"),
        pl.lit(24.0).alias("pre_mpg"),
        pl.lit(0.1).alias("pre_team_minutes_share"),
        pl.lit(0.5).alias("pre_start_share"),
    )
    fn = dp.resolve_method(wh, seasons, dp.M1_PRE_METHOD, "2026-27")
    out = fn(seasons, "2026-27")
    assert out.height > 0


def _auction_rules() -> LeagueRules:
    for f in FORMAT_FIXTURES:
        rules = parse_league_settings((FIX / f).read_text(encoding="utf-8"))
        if rules.auction_budget and rules.scoring.uses_categories:
            return rules
    raise AssertionError


def test_healthy_rank_values_everyone_at_the_same_games() -> None:
    rules = _auction_rules()
    values = draft_values.build_values(FakeWarehouse(), rules, "2026-27", "H1+aging")
    assert {"healthy_rank", "healthy_dollars"} <= set(values.columns)
    for variant, grp in values.group_by("variant"):
        ranks = grp.get_column("healthy_rank").sort().to_list()
        assert ranks == list(range(1, grp.height + 1)), variant  # a full ranking per variant
    assert values.get_column("healthy_dollars").min() >= 0  # type: ignore[operator]


def test_healthy_rank_ignores_projected_games() -> None:
    rules = _auction_rules()
    proj = draft_values.project(FakeWarehouse(), rules, "2026-27", "H1+aging")
    star = proj.sort("pts", descending=True).get_column("nba_player_id")[0]
    hurt = proj.with_columns(
        pl.when(pl.col("nba_player_id") == star)
        .then(10.0)
        .otherwise(pl.col("games"))
        .alias("games")
    )
    pos = FakeWarehouse().read(draft_values.POSITIONS_SQL)
    a = draft_values.healthy_ranks(proj, pos, rules, {})
    b = draft_values.healthy_ranks(hurt, pos, rules, {})
    # DATA-037: group-by row and float summation order vary, so compare by key with a tolerance.
    assert_frame_equal(a, b, check_row_order=False, rel_tol=1e-9, abs_tol=1e-9)
