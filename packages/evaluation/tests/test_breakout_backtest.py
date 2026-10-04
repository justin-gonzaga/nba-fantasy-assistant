from fantasy_evaluation import breakout_backtest as bb
from fantasy_evaluation.breakout_report import render
from fantasy_models.preseason.synthetic import make_league

SEASONS, DRAFT = make_league(seed=4, n_players=260)


def test_minutes_backtest_selects_on_early_folds_and_judges_on_holdout() -> None:
    res = bb.minutes_backtest(SEASONS, DRAFT, n_boot=50)
    assert res.winner in {"ridge", "gbm"}
    assert set(res.fold_mae["target"]) == set(bb.SELECT_FOLDS) | set(bb.HOLDOUT_FOLDS)
    assert res.rank_diff["folds"] == len(bb.HOLDOUT_FOLDS)
    assert len(res.reasons) == 3
    assert res.ships == (res.mae_diff[2] < 0 and res.rank_diff["lo"] > 0)


def test_breakout_backtest_metrics_and_report() -> None:
    brk = bb.breakout_backtest(SEASONS, n_boot=50)
    assert brk.folds.height == len(bb.SELECT_FOLDS) + len(bb.HOLDOUT_FOLDS)
    assert brk.folds["base_rate"].is_between(0, 1).all()
    assert set(brk.sensitivity["jump"]) == {30, 50, 80}
    assert brk.hindsight.height >= 20
    assert brk.ships == (brk.lift20[1] > 0 and brk.brier[0] < brk.brier[1])
    assert brk.model is not None
    mins = bb.minutes_backtest(SEASONS, DRAFT, n_boot=20)
    md = render(mins, brk, {}, "2026-09-26")
    assert "## Hindsight 2025-26" in md
    assert "## M1 minutes model" in md
