"""WEB-020: decision indicators for a player, each built only from stored numbers with a plain why.

Range (calibrated 80 % intervals, DRAFT-002), Certainty (spread of games + minutes), Role change
(projected vs last season's minutes), Punt fit (rank gain under the chosen punt), Consistency
(last season's week-to-week swings) and Age. Missing inputs drop their indicators, never error.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import polars as pl

from fantasy_api.schemas import Indicator

Tone = Literal["neutral", "accent", "win", "lose", "warn"]

# Thresholds (pinned by a test: changing one is a reviewed decision).
Z80 = 1.2816  # half-width of a central 80 % normal interval, in sds
ROLE_MPG = 3.0  # minutes per game change that counts as a role change
PUNT_GAIN = 20  # places gained under a punt that make a "fit"
STEADY_PCT = 1 / 3  # weekly-swing percentile at or below which a player is "Steady"
VOLATILE_PCT = 2 / 3  # at or above which he is "Volatile"
NO_AGE = "Age appears after the next daily run"
NO_CONSISTENCY = "Steady / Volatile appears after the next daily run"
VACATED_MIN = 500  # team minutes freed up worth naming in the role why line
SIGNAL_PRIORITY = ("role", "punt_fit", "consistency")
EN_DASH, MINUS = (
    chr(0x2013),
    chr(0x2212),
)  # typography for ranges and negatives (design language §6)
_CAT_LABEL = {
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "fg3m": "3PM",
    "fg_pct": "FG%",
    "ft_pct": "FT%",
    "tov": "TOV",
}


@dataclass
class IndicatorInputs:
    variant: str
    mean: dict[int, dict[str, float]] = field(default_factory=dict)
    sd: dict[int, dict[str, float]] = field(default_factory=dict)
    certainty: dict[int, str] = field(default_factory=dict)
    spread: dict[int, float] = field(default_factory=dict)
    last_mpg: dict[int, float] = field(default_factory=dict)
    age: dict[int, float] = field(default_factory=dict)
    swings: dict[int, tuple[float, float]] = field(default_factory=dict)  # rel sd, percentile
    median_swing: float | None = None
    rank: dict[str, dict[int, int]] = field(default_factory=dict)  # variant -> player -> rank
    notes: list[str] = field(default_factory=list)  # sources not published yet (WEB-022)
    changed_team: set[int] = field(default_factory=set)
    vacated: dict[int, float] = field(default_factory=dict)


def _terciles(spread: dict[int, float], pool: set[int]) -> dict[int, str]:
    """Cut points from the expected draft pool (fringe players' huge spreads would otherwise make
    every regular look certain); every player is then classified by those cut points."""
    ref = sorted(v for p, v in spread.items() if p in pool) or sorted(spread.values())
    if not ref:
        return {}
    lo, hi = ref[len(ref) // 3], ref[(2 * len(ref)) // 3]
    return {p: "high" if v < lo else ("medium" if v < hi else "low") for p, v in spread.items()}


def load_inputs(
    values: pl.DataFrame,
    variant: str,
    proj: pl.DataFrame | None,
    history: pl.DataFrame | None,
    consistency: pl.DataFrame | None,
) -> IndicatorInputs:
    i = IndicatorInputs(variant)
    for (v,), g in values.group_by("variant"):
        i.rank[str(v)] = dict(
            zip(g["nba_player_id"].to_list(), g["overall_rank"].to_list(), strict=True)
        )
    pool: set[int] = set()
    if "drafted" in values.columns:
        pool = set(
            values.filter((pl.col("variant") == "all") & pl.col("drafted"))[
                "nba_player_id"
            ].to_list()
        )
    if proj is not None and "sd" in proj.columns:
        _load_projection(i, proj, pool)
    if history is not None and {"season", "games_played", "minutes"} <= set(history.columns):
        _load_history(i, history)
        if "age" not in history.columns:
            i.notes.append(NO_AGE)
    if consistency is None or "rel_sd" not in consistency.columns:
        i.notes.append(NO_CONSISTENCY)
    if consistency is not None and consistency.height and "rel_sd" in consistency.columns:
        for r in consistency.select("nba_player_id", "rel_sd", "pct").iter_rows():
            i.swings[int(r[0])] = (float(r[1]), float(r[2]))
        i.median_swing = float(consistency["rel_sd"].median())  # type: ignore[arg-type]
    return i


def _load_projection(i: IndicatorInputs, proj: pl.DataFrame, pool: set[int]) -> None:
    latest = proj.filter(pl.col("season") == proj["season"].max())
    for pid, stat, mean, sd in latest.select("nba_player_id", "stat", "mean", "sd").iter_rows():
        if mean is not None:
            i.mean.setdefault(int(pid), {})[str(stat)] = float(mean)
        if sd is not None:
            i.sd.setdefault(int(pid), {})[str(stat)] = float(sd)
    spread = {
        pid: i.sd[pid]["games"] / m["games"] + i.sd[pid]["mpg"] / m["mpg"]
        for pid, m in i.mean.items()
        if m.get("games") and m.get("mpg") and {"games", "mpg"} <= set(i.sd.get(pid, {}))
    }
    i.spread = spread
    i.certainty = _terciles(spread, pool)


def _load_history(i: IndicatorInputs, history: pl.DataFrame) -> None:
    seasons = history.filter(pl.col("season").is_not_null())
    if not seasons.height:
        return
    last = seasons.filter(pl.col("season") == seasons["season"].max())
    cols = ["nba_player_id", "games_played", "minutes"]
    has_age = "age" in last.columns
    for row in last.select(*cols, *(["age"] if has_age else [])).iter_rows():
        pid, games, minutes = row[0], row[1], row[2]
        age = row[3] if has_age else None
        if games and minutes is not None:
            i.last_mpg[int(pid)] = float(minutes) / float(games)
        if age is not None:
            i.age[int(pid)] = float(age)


def add_role_context(i: IndicatorInputs, role: pl.DataFrame | None) -> None:
    """The minutes model's role drivers (published by the pipeline), for the role why line."""
    if role is None or not {"changed_team", "vacated_min"} <= set(role.columns):
        return
    for pid, changed, vacated in role.select(
        "nba_player_id", "changed_team", "vacated_min"
    ).iter_rows():
        if changed:
            i.changed_team.add(int(pid))
        if vacated is not None:
            i.vacated[int(pid)] = float(vacated)


def _range(pid: int, i: IndicatorInputs) -> list[Indicator]:
    m, s = i.mean.get(pid, {}), i.sd.get(pid, {})
    parts = []
    for stat, unit, cap in (("pts", "pts", None), ("games", "games", 82.0)):
        if stat in m and stat in s:
            lo = max(0.0, m[stat] - Z80 * s[stat])
            hi = m[stat] + Z80 * s[stat]
            if cap is not None:
                hi = min(cap, hi)
            parts.append(f"{lo:.0f}{EN_DASH}{hi:.0f} {unit}")
    if not parts:
        return []
    return [
        Indicator(
            code="range", label="80 % range", tone="neutral", why=f"80 % range: {', '.join(parts)}"
        )
    ]


def _certainty(pid: int, i: IndicatorInputs) -> list[Indicator]:
    level = i.certainty.get(pid)
    if level is None:
        return []
    tone: Tone = {"high": "win", "medium": "neutral", "low": "warn"}[level]  # type: ignore[assignment]
    why = {
        "high": "Games and minutes among the most predictable third of the draft pool",
        "medium": "Games and minutes about as predictable as most of the draft pool",
        "low": "Games and minutes among the least predictable third of the draft pool",
    }[level]
    return [
        Indicator(
            code="certainty",
            label=f"{level.capitalize()} certainty",
            tone=tone,
            why=why,
            value=round(i.spread[pid], 4),
        )
    ]


def _role(pid: int, i: IndicatorInputs) -> list[Indicator]:
    proj = i.mean.get(pid, {}).get("mpg")
    last = i.last_mpg.get(pid)
    if proj is None or last is None or abs(proj - last) < ROLE_MPG:
        return []
    up = proj > last
    sign = "+" if up else MINUS
    return [
        Indicator(
            code="role",
            label=f"{'Bigger' if up else 'Smaller'} role {sign}{abs(proj - last):.1f} min",
            tone="win" if up else "lose",
            why=_role_why(pid, proj, last, i),
            signal=True,
            value=round(proj - last, 2),
        )
    ]


def _role_why(pid: int, proj: float, last: float, i: IndicatorInputs) -> str:
    parts = [f"Projected {proj:.1f} min vs {last:.1f} last season"]
    if pid in i.changed_team:
        parts.append("new team")
    if i.vacated.get(pid, 0.0) >= VACATED_MIN:
        parts.append(f"{i.vacated[pid]:,.0f} team minutes freed up")
    return "; ".join(parts)


def _punt_fit(pid: int, i: IndicatorInputs) -> list[Indicator]:
    if i.variant == "all":
        return []
    overall = i.rank.get("all", {}).get(pid)
    here = i.rank.get(i.variant, {}).get(pid)
    if overall is None or here is None or overall - here < PUNT_GAIN:
        return []
    cat = i.variant.removeprefix("punt_")
    label = _CAT_LABEL.get(cat, cat.upper())
    return [
        Indicator(
            code="punt_fit",
            label=f"Fits punt {label}",
            tone="accent",
            why=f"#{overall} overall, #{here} when punting {label}",
            signal=True,
        )
    ]


def _consistency(pid: int, i: IndicatorInputs) -> list[Indicator]:
    swing = i.swings.get(pid)
    if swing is None or i.median_swing is None:
        return []
    sd, pct = swing
    why = (
        f"Weekly value swung ±{sd:.0%} of his level last season "
        f"(draft-pool median ±{i.median_swing:.0%})"
    )
    if pct <= STEADY_PCT:
        return [Indicator(code="consistency", label="Steady", tone="win", why=why)]
    if pct >= VOLATILE_PCT:
        return [Indicator(code="consistency", label="Volatile", tone="warn", why=why, signal=True)]
    return []


def _age(pid: int, i: IndicatorInputs) -> list[Indicator]:
    age = i.age.get(pid)
    if age is None:
        return []
    now = round(age) + 1
    return [Indicator(code="age", label=f"Age {now}", tone="neutral", why=f"{now} this season")]


def indicators_for(pid: int, i: IndicatorInputs) -> list[Indicator]:
    return [
        *_range(pid, i),
        *_certainty(pid, i),
        *_role(pid, i),
        *_punt_fit(pid, i),
        *_consistency(pid, i),
        *_age(pid, i),
    ]


def signal(items: Sequence[Indicator]) -> Indicator | None:
    """The one indicator a row shows: role change > punt fit > volatile."""
    flagged = [x for x in items if x.signal]
    flagged.sort(key=lambda x: SIGNAL_PRIORITY.index(x.code) if x.code in SIGNAL_PRIORITY else 99)
    return flagged[0] if flagged else None
