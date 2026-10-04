"""Daily brief rules (MVP-003): lineup, matchup outlook, pickups. Baselines only, no new ML.

- Lineup: players with no game today or ruled Out go to the bench; the rest fill the active slots
  greedily by player value (the draft G-score total), scarcest eligible slot first, then Util.
  Questionable players are started but flagged for a check before tip-off.
- Matchup: each category's weekly total is roughly normal; counting categories use a Poisson
  variance (var = mean), percentages a binomial one (p(1-p)/attempts). P(win) = Phi(diff / sd).
  Turnovers are reversed.
- Pickups: each free agent with games left replaces my lowest-value player; the gain is the change
  in expected categories won this week (sum of P(win)). Without an opponent, weekly value.
Every number in the rendered text comes from these structures (explanations standard).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

import polars as pl

from fantasy_decision import explain as ex
from fantasy_decision import lineup as lu
from fantasy_models.distributions import MAKES_RHO, NB_SIZE

COUNTING = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov")
RATIOS = {"fg_pct": ("fgm", "fga"), "ft_pct": ("ftm", "fta")}
LOWER_IS_BETTER = frozenset({"tov"})
LABELS = {
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "fg3m": "3PM",
    "tov": "TO",
    "fg_pct": "FG%",
    "ft_pct": "FT%",
}
BENCH = "BN"
VAR_FLOOR = 1e-9  # e.g. a 100 % free-throw sample has zero binomial variance
HELP_THRESHOLD = 0.02  # a category counts as helped above +2 points of win chance


@dataclass(frozen=True)
class Slotting:
    player_id: int
    name: str
    slot: str
    reason: str


@dataclass(frozen=True)
class Pickup:
    add_id: int
    add_name: str
    drop_id: int
    drop_name: str
    games_left: int
    gain: float
    helps: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Brief:
    lineup: list[Slotting]
    injuries: list[tuple[str, str]]
    outlook: dict[str, float] | None
    pickups: list[Pickup]
    horizon: str = "this week"  # what a pickup's gain covers (DEC-010: + half of next week)


def mark(p: float) -> str:
    return "▲" if p >= 0.6 else "▼" if p <= 0.4 else "●"  # noqa: PLR2004


def _rows(week: pl.DataFrame, ids: Sequence[int]) -> pl.DataFrame:
    return week.filter(pl.col("nba_player_id").is_in(list(ids)))


def team_totals(week: pl.DataFrame, ids: Sequence[int]) -> dict[str, tuple[float, float]]:
    """(mean, variance) of each category's weekly total for these players.

    Counting stats: negative-binomial variance per player, m + m^2 / (games * r) (DEC-002 shipped
    NB over Poisson). Percentages: beta-binomial inflation of the binomial variance."""
    t = _rows(week, ids)
    games = t["exp_games"].clip(lower_bound=1.0)
    out = {}
    for c in COUNTING:
        m = t[c]
        var = (m + m**2 / (games * NB_SIZE[c])).sum()
        out[c] = (float(m.sum()), max(float(var), VAR_FLOOR))
    for cat, (mk, a) in RATIOS.items():
        makes, att = float(t[mk].sum()), float(t[a].sum())
        p = makes / att if att else 0.0
        per_player_att = att / max(t.height, 1)
        inflation = 1 + max(per_player_att - 1, 0.0) * MAKES_RHO[cat]
        out[cat] = (p, p * (1 - p) / att * inflation if att else 1.0)
    return out


def win_probs(
    mine: Mapping[str, tuple[float, float]], theirs: Mapping[str, tuple[float, float]]
) -> dict[str, float]:
    probs = {}
    for cat, (m, v) in mine.items():
        om, ov = theirs[cat]
        diff = (om - m) if cat in LOWER_IS_BETTER else (m - om)
        sd = math.sqrt(2 * max(v + ov, VAR_FLOOR))
        probs[cat] = 0.5 * (1 + math.erf(diff / sd))
    return probs


def lineup(
    week: pl.DataFrame,
    mine: Sequence[int],
    positions: Mapping[int, tuple[str, ...]],
    value: Mapping[int, float],
    slots: Mapping[str, int],
) -> list[Slotting]:
    """Today's lineup from the integer program (DEC-007 shipped over greedy): most players with a
    game active, then the most value. No game or Out -> bench; Questionable/Doubtful are flagged."""
    rows = sorted(
        _rows(week, mine).iter_rows(named=True), key=lambda r: -value.get(r["nba_player_id"], 0.0)
    )
    cands = [
        lu.Candidate(
            r["nba_player_id"],
            value.get(r["nba_player_id"], 0.0),
            positions.get(r["nba_player_id"], ()),
            bool(r["plays_today"]) and r["status_today"] != "Out",
        )
        for r in rows
    ]
    assign = lu.optimise(cands, slots)
    out: list[Slotting] = []
    for r in rows:
        pid, name, status = r["nba_player_id"], r["player_name"], r["status_today"]
        if not r["plays_today"]:
            out.append(Slotting(pid, name, BENCH, "no game today"))
        elif status == "Out":
            out.append(Slotting(pid, name, BENCH, "Out on today's injury report"))
        elif pid not in assign:
            out.append(Slotting(pid, name, BENCH, "active slots full"))
        elif status in {"Questionable", "Doubtful"}:
            out.append(
                Slotting(pid, name, assign[pid], f"{status}: check the last report before tip-off")
            )
        else:
            out.append(Slotting(pid, name, assign[pid], "plays today"))
    return out


def pickups(  # noqa: PLR0913 - the pickup question has these inputs
    week: pl.DataFrame,
    mine: Sequence[int],
    opponent: Sequence[int] | None,
    *,
    rostered: set[int],
    value: Mapping[int, float],
    n: int = 5,
) -> list[Pickup]:
    ids = week["nba_player_id"].to_list()
    names = dict(zip(ids, week["player_name"].to_list(), strict=True))
    exp = dict(zip(ids, week["exp_games"].to_list(), strict=True))
    left = dict(zip(ids, week["games_left"].to_list(), strict=True))
    drop = min(mine, key=lambda p: value.get(p, 0.0))
    kept = [p for p in mine if p != drop]
    theirs = team_totals(week, opponent) if opponent else None
    before = win_probs(team_totals(week, mine), theirs) if theirs else {}
    picks = []
    for fa in (p for p in ids if p not in rostered and left.get(p, 0) > 0):
        if theirs is not None:
            after = win_probs(team_totals(week, [*kept, fa]), theirs)
            gain = sum(after.values()) - sum(before.values())
            ranked = sorted(after, key=lambda c: after[c] - before[c], reverse=True)
            helps = [c for c in ranked if after[c] - before[c] > HELP_THRESHOLD][:3]
        else:
            gain = value.get(fa, 0.0) * exp[fa] - value.get(drop, 0.0) * exp[drop]
            helps = []
        picks.append(Pickup(fa, names[fa], drop, names[drop], int(left[fa]), gain, helps))
    return sorted(picks, key=lambda p: -p.gain)[:n]


def build(  # noqa: PLR0913 - the brief's inputs, all explicit
    week: pl.DataFrame,
    mine: Sequence[int],
    opponent: Sequence[int] | None,
    *,
    rostered: set[int],
    positions: Mapping[int, tuple[str, ...]],
    value: Mapping[int, float],
    slots: Mapping[str, int],
) -> Brief:
    my = _rows(week, mine)
    injuries = [
        (r["player_name"], r["status_today"])
        for r in my.iter_rows(named=True)
        if r["status_today"] not in (None, "Available")
    ]
    outlook = win_probs(team_totals(week, mine), team_totals(week, opponent)) if opponent else None
    return Brief(
        lineup(week, mine, positions, value, slots),
        injuries,
        outlook,
        pickups(week, mine, opponent, rostered=rostered, value=value),
    )


def explained(b: Brief, *, day: str, opponent: str | None) -> list[ex.Explanation]:
    """The brief line by line, each filled only from structured evidence (ADR-0016)."""
    out = [
        ex.render("*{day}* · vs {opponent}", day=day, opponent=opponent)
        if opponent
        else ex.render("*{day}*", day=day)
    ]
    blank = ex.render("")
    if b.outlook:
        out += [
            blank,
            ex.render(
                "*Matchup*: {wins:.1f} of {n} categories expected",
                wins=sum(b.outlook.values()),
                n=len(b.outlook),
            ),
            ex.render(
                "{cats}", cats=" ".join(f"{LABELS[c]} {mark(p)}" for c, p in b.outlook.items())
            ),
        ]
    out += [blank, ex.render("*Lineup today*")]
    out += [
        ex.render(
            "{slot}: {name} ({reason})",
            slot="BN" if s.slot == BENCH else s.slot,
            name=s.name,
            reason=s.reason,
        )
        for s in b.lineup
    ]
    if b.injuries:
        out += [blank, ex.render("*Injury report*")]
        out += [ex.render("{name}: {status}", name=n, status=st) for n, st in b.injuries]
    if b.pickups:
        out += [blank, ex.render("*Pickups* (add / drop, gain {horizon})", horizon=b.horizon)]
        for p in b.pickups:
            helps = f", helps {', '.join(LABELS[h] for h in p.helps)}" if p.helps else ""
            out.append(
                ex.render(
                    "+{add} / -{drop}: {gain:+.2f} {unit}, {games} games{helps}",
                    add=p.add_name,
                    drop=p.drop_name,
                    gain=p.gain,
                    unit="cat. wins" if b.outlook else "value",
                    games=p.games_left,
                    helps=helps,
                )
            )
    return out


def render(b: Brief, *, day: str, opponent: str | None) -> str:
    return "\n".join(e.text for e in explained(b, day=day, opponent=opponent))
