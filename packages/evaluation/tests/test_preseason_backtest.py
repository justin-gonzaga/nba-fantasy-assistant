import numpy as np
import polars as pl
import pytest

from dikit.evaluate import bootstrap as bs
from dikit.evaluate import scoring as sc
from fantasy_evaluation import preseason_backtest as bt
from fantasy_evaluation.preseason_report import render_report
from fantasy_models.preseason.synthetic import make_league

SEASONS, DRAFT = make_league(seed=11, n_players=220)


def test_spearman_matches_definition_and_supports_batches() -> None:
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert sc.spearman(x, x) == pytest.approx(1.0)
    assert sc.spearman(x, -x) == pytest.approx(-1.0)
    batch = np.stack([x, -x])
    assert sc.spearman(batch, np.stack([x, x])).tolist() == pytest.approx([1.0, -1.0])


def test_value_score_rewards_good_shooting_volume() -> None:
    ref = pl.DataFrame(
        {
            s: [1.0, 1.0, 1.0]
            for s in ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "ftm", "fta")
        }
    ).with_columns(fgm=pl.Series([5.0, 5.0, 2.0]), fga=pl.Series([10.0, 10.0, 10.0]))
    v = bt.value_score(ref, ref)
    assert v[0] == pytest.approx(v[1])
    assert v[2] < v[0]


def test_bootstrap_ci_contains_the_mean() -> None:
    d = np.random.default_rng(0).normal(0.5, 1, 300)
    idx = bs.idx(len(d), 500, seed=1)
    lo, hi = bs.ci(d[idx].mean(axis=1))
    assert lo < d.mean() < hi


def test_run_fold_compares_all_methods_without_leakage() -> None:
    fold, aligned = bt.run_fold(SEASONS, DRAFT, "2025-26", n_boot=200)
    assert set(fold.mae.get_column("method")) == {"B0", "B1", "C1", "C1+aging", "H1", "H1+aging"}
    assert fold.n_players > 50
    assert {"C1 vs B0", "C1 vs B1", "B1 vs B0", "H1 vs B0", "H1 vs C1"} <= set(
        fold.rank_diff.get_column("comparison")
    )
    assert fold.n_rank >= fold.n_players  # totals ranking includes players under 20 games
    assert fold.rank_per_game.height == fold.rank_oracle_minutes.height == 6
    # every method is evaluated on the same players
    assert len({p.height for p in aligned.values()}) == 1
    # on synthetic data with known true rates, shrinkage beats last season on steals
    stl = fold.mae.filter(pl.col("stat") == "stl")
    by = dict(zip(stl.get_column("method"), stl.get_column("mae"), strict=True))
    assert by["C1"] < by["B0"]


def test_gate_and_report() -> None:
    sds = bt.fold_sds(SEASONS, DRAFT, "2024-25")
    fold, _ = bt.run_fold(SEASONS, DRAFT, "2025-26", n_boot=200, prior_sds=sds)
    decision = bt.gate(fold)
    assert decision.method in {"B0", "B1", "C1", "H1", "H1+aging"}
    assert 1 <= len(decision.reasons) <= 3
    assert fold.coverage80
    assert all(0 <= v <= 1 for v in fold.coverage80.values())
    md = render_report([fold], fold, decision, "2026-09-25T00:00Z")
    assert "ship **" in md
    assert "| pts |" in md
    assert "80 % interval coverage" in md


def test_gate_ships_first_candidate_that_beats_b0() -> None:
    fold, _ = bt.run_fold(SEASONS, DRAFT, "2025-26", n_boot=200)
    better_mae = fold.mae_diff.with_columns(pl.lit(-1.0).alias("diff"))
    worse_mae = fold.mae_diff.with_columns(pl.lit(1.0).alias("diff"))

    def rank_lo(lo_h1: float, lo_c1: float, lo_b1: float) -> pl.DataFrame:
        los = {"H1 vs B0": lo_h1, "C1 vs B0": lo_c1, "B1 vs B0": lo_b1}
        return fold.rank_diff.with_columns(
            pl.col("comparison")
            .replace_strict(los, default=None)
            .fill_null(pl.col("lo"))
            .alias("lo")
        )

    fold.mae_diff = better_mae
    fold.rank_diff = rank_lo(0.01, 0.01, 0.01)
    assert bt.gate(fold).method == "H1"
    fold.rank_diff = rank_lo(-0.01, 0.01, 0.01)
    assert bt.gate(fold).method == "C1"
    fold.rank_diff = rank_lo(-0.01, -0.01, 0.01)
    assert bt.gate(fold).method == "B1"
    fold.rank_diff = rank_lo(-0.01, -0.01, -0.01)
    assert bt.gate(fold).method == "B0"
    fold.mae_diff = worse_mae
    fold.rank_diff = rank_lo(0.01, 0.01, 0.01)
    decision = bt.gate(fold)
    assert decision.method == "B0"
    assert all("fail" in r for r in decision.reasons)


def test_gate_uses_pooled_folds_when_given() -> None:
    folds = [bt.run_fold(SEASONS, DRAFT, t, n_boot=200)[0] for t in ("2024-25", "2025-26")]
    primary = folds[-1]
    primary.mae_diff = primary.mae_diff.with_columns(pl.lit(-1.0).alias("diff"))
    pooled = bt.pooled_rank_diff(folds, "H1 vs B0")
    assert pooled["folds"] == 2
    assert pooled["lo"] <= pooled["diff"] <= pooled["hi"]
    # make every fold's H1 advantage clearly positive -> the pooled rule passes
    for f in folds:
        f.rank_diff_samples["H1 vs B0"] = f.rank_diff_samples["H1 vs B0"] * 0 + 0.05
        f.rank_diff = f.rank_diff.with_columns(
            pl.when(pl.col("comparison") == "H1 vs B0")
            .then(0.05)
            .otherwise(pl.col("diff"))
            .alias("diff")
        )
    decision = bt.gate(primary, folds)
    assert decision.method == "H1"
    assert "pooled over 2 folds" in decision.reasons[0]


def test_challenger_replaces_base_only_when_pre_registered_rule_passes() -> None:
    folds = [bt.run_fold(SEASONS, DRAFT, t, n_boot=200)[0] for t in ("2024-25", "2025-26")]
    primary = folds[-1]
    primary.mae_diff = primary.mae_diff.with_columns(pl.lit(-1.0).alias("diff"))

    def set_samples(comp: str, value: float) -> None:
        for f in folds:
            f.rank_diff_samples[comp] = f.rank_diff_samples[comp] * 0 + value
            f.rank_diff = f.rank_diff.with_columns(
                pl.when(pl.col("comparison") == comp)
                .then(value)
                .otherwise(pl.col("diff"))
                .alias("diff")
            )

    set_samples("H1 vs B0", 0.05)
    set_samples("H1+aging vs H1", 0.02)
    d = bt.gate(primary, folds)
    assert d.method == "H1+aging"
    assert "REPLACES H1" in d.reasons[-1]
    set_samples("H1+aging vs H1", -0.02)
    d = bt.gate(primary, folds)
    assert d.method == "H1"
    assert "H1 stays" in d.reasons[-1]
    table = bt.pooled_table(folds)
    assert {"H1 vs B0", "C1 vs B0", "B1 vs B0", "H1+aging vs H1"} <= set(
        table.get_column("comparison")
    )
