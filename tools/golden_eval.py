"""Golden capture of evaluation outputs on fixed inputs and seeds (GEN-006..008 refactors).

Run it before and after a refactor (twice before, to see what is already nondeterministic):
    uv run python tools/golden_eval.py OUT.pkl
    uv run python tools/golden_eval.py --compare BEFORE.pkl AFTER.pkl
"""

import importlib.util
import pickle
import sys
from dataclasses import is_dataclass
from datetime import date, timedelta
from pathlib import Path
from types import ModuleType
from typing import Any

import numpy as np
import polars as pl

from fantasy_evaluation import availability as av
from fantasy_evaluation import breakout_backtest as bb
from fantasy_evaluation import distribution_backtest as db
from fantasy_evaluation import draft_replay as dr
from fantasy_evaluation import inseason_backtest as ib
from fantasy_evaluation import moves_replay as mr
from fantasy_evaluation import preseason_backtest as bt
from fantasy_evaluation import simulation_backtest as sb
from fantasy_models.preseason.synthetic import make_league

T = Path("packages/evaluation/tests")


def mod(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, T / f"{name}.py")
    assert spec is not None  # noqa: S101 - a dev tool
    assert spec.loader is not None  # noqa: S101
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(x: Any) -> Any:
    if isinstance(x, pl.DataFrame):
        return ("df", x.columns, sorted((tuple(norm(v) for v in r) for r in x.rows()), key=repr))
    if isinstance(x, np.ndarray):
        return ("arr", x.tolist())
    if is_dataclass(x) and not isinstance(x, type):
        return {k: norm(v) for k, v in vars(x).items()}
    if isinstance(x, dict):
        return {str(k): norm(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [norm(v) for v in x]
    if isinstance(x, float):
        return round(x, 10)
    return x


def capture() -> dict[str, Any]:
    out: dict[str, Any] = {}
    tsb = mod("test_simulation_backtest")
    out["sim"] = norm(sb.run(tsb._logs(), n_boot=100, matchups=5))
    tdb = mod("test_distribution_backtest")
    out["dist"] = norm(db.run(tdb._logs(size=2.0), n_boot=200))
    tib = mod("test_inseason_backtest")
    logs, priors = tib._data()
    out["inseason"] = norm(ib.run(logs, priors, n_boot=200))
    tmr = mod("test_moves_replay")
    logs, priors = tmr._logs_priors()
    weeks = {m: mr.week_inputs(logs, priors, m) for m in mr.weeks_of(logs)}
    squads = [list(range(t * 5, t * 5 + 5)) for t in range(4)]
    value = dict.fromkeys(range(60), 1.0) | {59: 5.0}
    out["moves"] = norm(mr.run(squads, weeks, value, draws=300, n_boot=100))

    rng = np.random.default_rng(1)
    players = list(range(300))
    skill = {p: float(rng.uniform(0.2, 2.0)) for p in players}
    elig = {p: ("G", "F", "C")[p % 3 : p % 3 + 1] for p in players}
    days: dict[date, dict[int, list[float]]] = {}
    for i in range(0, 42, 2):
        days[date(2025, 10, 20) + timedelta(days=i)] = {
            p: [10 * skill[p]] * 6 + [1.0] + [4 * skill[p], 8.0, 2.0, 3.0] for p in players
        }
    out["draft"] = norm(
        dr.run(
            {"smart": skill, "reverse": {p: -s for p, s in skill.items()}},
            elig,
            days,
            drafts=4,
            n_boot=200,
        )
    )

    r = np.random.default_rng(7)
    rows = pl.DataFrame(
        {
            "status": r.choice(["Available", "Questionable", "Doubtful", "Out"], 800).tolist(),
            "game_date": [
                date(2026, 1, 1) + timedelta(days=int(d)) for d in r.integers(0, 40, 800)
            ],
            "played": r.random(800) < 0.6,
        }
    ).sort("game_date", "status", "played")
    out["avail"] = norm(av.rates(rows, n_boot=300, seed=1).sort("status"))

    seasons, draft = make_league(seed=4, n_players=260)
    fold, _ = bt.run_fold(seasons, draft, "2025-26", n_boot=200)
    out["preseason_fold"] = norm(fold)
    out["preseason_gate"] = norm(bt.gate(fold))
    out["minutes"] = norm(bb.minutes_backtest(seasons, draft, n_boot=50))
    out["breakout"] = norm(bb.breakout_backtest(seasons, n_boot=50))
    return out


if __name__ == "__main__":
    if sys.argv[1] == "--compare":
        a, b = (pickle.loads(Path(p).read_bytes()) for p in sys.argv[2:4])  # noqa: S301 - our own files
        for k in a:
            print(k, "SAME" if a[k] == b.get(k) else "DIFFERENT")
        sys.exit(0 if a == b else 1)
    Path(sys.argv[1]).write_bytes(pickle.dumps(capture()))
    print("captured")
