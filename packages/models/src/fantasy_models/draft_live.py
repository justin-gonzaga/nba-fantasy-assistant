"""Live auction helper arithmetic (DRAFT-005; ml-methodology-plan §3, G-21).

Pure functions over plain dicts so the page's JavaScript can mirror them exactly
(a parity test runs both on the same pick sequence).
- Max bid: budget left - $1 x (open slots - 1). A rule of the game.
- Inflation: (league $ left - $1 x slots left) / (sum over the best remaining players, one per
  open slot, of their $ above the $1 floor). A practitioner method (U1).
- Team fit: in the spirit of H-scoring [R-02], which covers snake drafts; the auction adaptation is
  ours (U2). Categories the roster is already strong in get less weight, weak ones more; the fit
  multiplier is capped at +/-25 %.
- Nomination hints: expensive players that fit my build poorly (others will pay; budgets drain)
  [R-80, R-81].
"""

from __future__ import annotations

from typing import Any

FIT_CAP = 0.25
FIT_ALPHA = 0.5
WEIGHT_BOUNDS = (0.5, 1.5)
HINT_POOL = 60
HINT_FIT_BELOW = 0.95


def team_state(
    picks: list[dict[str, Any]], teams: list[str], budget: int, slots: int
) -> dict[str, dict[str, float]]:
    out = {t: {"spent": 0.0, "count": 0.0} for t in teams}
    for p in picks:
        out[p["team"]]["spent"] += p["price"]
        out[p["team"]]["count"] += 1
    for s in out.values():
        s["left"] = budget - s["spent"]
        s["open"] = slots - s["count"]
        s["max_bid"] = max(0.0, s["left"] - max(0.0, s["open"] - 1)) if s["open"] > 0 else 0.0
    return out


def inflation(
    players: list[dict[str, Any]], taken: set[str], state: dict[str, dict[str, float]]
) -> float:
    # Only teams that can still buy count: a full roster's leftover cash is dead money (review).
    money = sum(s["left"] for s in state.values() if s["open"] > 0)
    open_slots = int(sum(s["open"] for s in state.values()))
    left = sorted((float(p["usd"]) for p in players if p["id"] not in taken), reverse=True)[
        :open_slots
    ]
    above_floor = sum(max(0.0, u - 1) for u in left)
    if open_slots <= 0 or above_floor <= 0:
        return 1.0
    return max(0.0, money - open_slots) / above_floor


def category_weights(
    players_by_id: dict[str, dict[str, Any]], mine: list[str], punted: set[int]
) -> list[float]:
    n = len(next(iter(players_by_id.values()))["z"])
    if not mine:
        return [0.0 if i in punted else 1.0 for i in range(n)]
    prof = [sum(players_by_id[p]["z"][i] for p in mine) / len(mine) for i in range(n)]
    lo, hi = WEIGHT_BOUNDS
    return [0.0 if i in punted else min(hi, max(lo, 1 - FIT_ALPHA * prof[i])) for i in range(n)]


def fit_multiplier(z: list[float], weights: list[float], punted: set[int]) -> float:
    base = sum(v for i, v in enumerate(z) if i not in punted)
    fit = sum(w * v for w, v in zip(weights, z, strict=True))
    if base <= 0:
        return 1.0
    return min(1 + FIT_CAP, max(1 - FIT_CAP, fit / base))


def advise(  # noqa: PLR0913, PLR0917 - mirrors the JS signature exactly
    players: list[dict[str, Any]],
    picks: list[dict[str, Any]],
    teams: list[str],
    me: str,
    budget: int,
    slots: int,
    punted: set[int] | None = None,
) -> dict[str, Any]:
    """Everything the page shows after a pick: my max bid, per-player ceilings, targets, hints."""
    punted = punted or set()
    by_id = {p["id"]: p for p in players}
    taken = {p["pid"] for p in picks}
    state = team_state(picks, teams, budget, slots)
    infl = inflation(players, taken, state)
    mine = [p["pid"] for p in picks if p["team"] == me]
    weights = category_weights(by_id, mine, punted)
    my_max = state[me]["max_bid"]
    rows = []
    for p in players:
        if p["id"] in taken:
            continue
        adj = 1 + (p["usd"] - 1) * infl
        fit = fit_multiplier(p["z"], weights, punted)
        ceiling = float(int(min(my_max, adj * fit))) if my_max >= 1 else 0.0
        rows.append({"id": p["id"], "adj": adj, "fit": fit, "ceiling": ceiling})
    targets = sorted(rows, key=lambda r: (-r["adj"] * r["fit"], r["id"]))[:10]
    top = sorted(rows, key=lambda r: (-r["adj"], r["id"]))[:HINT_POOL]
    hints = sorted(
        (r for r in top if r["fit"] < HINT_FIT_BELOW),
        key=lambda r: (-r["adj"] * (1 - r["fit"]), r["id"]),
    )[:5]
    return {
        "inflation": infl,
        "weights": weights,
        "my_max_bid": my_max,
        "teams": state,
        "players": {r["id"]: r for r in rows},
        "targets": [r["id"] for r in targets],
        "hints": [r["id"] for r in hints],
    }
