"""DRAFT-004: the auction board (phone-first HTML + CSV) from the latest predictions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from fantasy_pipeline.warehouse import Warehouse

TOP_N = 260  # the board shows 200; the live helper needs the whole draftable pool + margin
BOUNCE_BACK_SHOW = 0.2
CAT_LABELS = {
    "fg_pct": "FG%",
    "ft_pct": "FT%",
    "fg3m": "3PM",
    "pts": "PTS",
    "reb": "REB",
    "ast": "AST",
    "stl": "STL",
    "blk": "BLK",
    "tov": "TO",
}
LINE_STATS = ("pts", "reb", "ast", "stl", "blk", "fg3m", "tov")

VALUES_SQL = "select * from predictions.auction_values"
PROJ_SQL = "select nba_player_id, stat, mean, source, method from predictions.preseason_projection"
_BOUNCE_COLS = "select nba_player_id, p_breakout from predictions.breakout_probability"
BOUNCE_SQL = _BOUNCE_COLS + " where kind = 'bounce_back'"
_PROFILE_COLS = "select nba_player_id, player_name, nba_team_id, age_at_midseason, draft_year"
PROFILE_SQL = _PROFILE_COLS + " from intermediate.int_player_profile"
TEAMS_SQL = (
    "select distinct nba_team_id, team_abbreviation from staging.stg_nba_stats__team_game "
    "where season = (select max(season) from staging.stg_nba_stats__team_game)"
)


@dataclass(frozen=True)
class SheetMeta:
    teams: int
    budget: int
    pool: int
    scoring: str
    method: str
    generated: str
    draft_year: int
    slots: int = 14


def build_data(  # noqa: PLR0913, PLR0917 - one frame per source
    values: pl.DataFrame,
    proj: pl.DataFrame,
    bounce: pl.DataFrame,
    profile: pl.DataFrame,
    teams: pl.DataFrame,
    meta: SheetMeta,
    out_tags: dict[int, str] | None = None,
) -> dict[str, Any]:
    """Compact JSON for the page: player facts once, then per-variant ranked rows."""
    out_tags = out_tags or {}
    line = proj.pivot(on="stat", index="nba_player_id", values="mean")
    src = proj.group_by("nba_player_id").agg(pl.col("source").first())
    fac = (
        values.filter(pl.col("variant") == "all")
        .select("nba_player_id", "player_name", "nba_position")
        .join(line, on="nba_player_id", how="left")
        .join(src, on="nba_player_id", how="left")
        .join(bounce, on="nba_player_id", how="left")
        .join(profile, on="nba_player_id", how="left")
        .join(teams, on="nba_team_id", how="left")
    )
    players = {}
    for r in fac.iter_rows(named=True):
        fg = r["fgm"] / r["fga"] if r.get("fga") else None
        ft = r["ftm"] / r["fta"] if r.get("fta") else None
        players[str(r["nba_player_id"])] = {
            "n": r["player_name"],
            "p": r["nba_position"] or "",
            "t": r["team_abbreviation"] or "",
            "a": round(r["age_at_midseason"], 1) if r["age_at_midseason"] else None,
            "g": round(r["games"]) if r.get("games") else None,
            "l": [round(r[s], 1) if r.get(s) is not None else None for s in LINE_STATS],
            "fg": round(fg, 3) if fg else None,
            "ft": round(ft, 3) if ft else None,
            "bb": round(r["p_breakout"], 2)
            if r["p_breakout"] and r["p_breakout"] >= BOUNCE_BACK_SHOW
            else None,
            "rk": bool(r["source"] == "rookie_prior" and r["draft_year"] == meta.draft_year),
            "out": out_tags.get(r["nba_player_id"]),
        }
    cats = [c for c in CAT_LABELS if f"s_{c}" in values.columns]
    variants = []
    for name in values.get_column("variant").unique(maintain_order=True).to_list():
        v = values.filter(pl.col("variant") == name).sort("overall_rank").head(TOP_N)
        rows = [
            [
                str(r["nba_player_id"]),
                r["overall_rank"],
                round(r["dollars"]) if r["dollars"] is not None else None,
                r["tier"],
                [round(r[f"s_{c}"], 2) for c in cats],
            ]
            for r in v.iter_rows(named=True)
        ]
        variants.append({"key": name, "label": _variant_label(name), "rows": rows})
    return {
        "meta": meta.__dict__,
        "cats": [CAT_LABELS[c] for c in cats],
        "catKeys": cats,
        "lineLabels": [CAT_LABELS.get(s, s.upper()) for s in LINE_STATS],
        "players": players,
        "variants": variants,
    }


def _variant_label(name: str) -> str:
    if name == "all":
        return "All 9 cats"
    code = name.removeprefix("punt_")
    return f"Punt {CAT_LABELS.get(code, code)}"


def to_csv(data: dict[str, Any]) -> pl.DataFrame:
    rows = []
    for v in data["variants"]:
        for pid, rank, dollars, tier, scores in v["rows"]:
            p = data["players"][pid]
            rows.append(
                {
                    "variant": v["label"],
                    "rank": rank,
                    "player": p["n"],
                    "pos": p["p"],
                    "team": p["t"],
                    "dollars": dollars,
                    "tier": tier,
                    **{f"z_{c}": s for c, s in zip(data["cats"], scores, strict=True)},
                    "bounce_back": p["bb"],
                    "rookie": p["rk"],
                }
            )
    return pl.DataFrame(rows)


def override_tags(wh: Warehouse) -> dict[int, str]:
    """Board tags for owner-reviewed absences (D-47 Q2): status + return + source date."""
    from fantasy_pipeline import overrides  # noqa: PLC0415 - optional input
    from fantasy_pipeline.draft_projection import DRAFT_AS_OF  # noqa: PLC0415

    rows = overrides.load(overrides.DEFAULT_PATH, DRAFT_AS_OF)
    if rows.height == 0:
        return {}
    prof = wh.read(PROFILE_SQL).select(
        pl.col("nba_player_id").cast(pl.Int64), pl.col("player_name")
    )
    res = overrides.resolve(rows, prof.rename({"player_name": "player_name"}))
    tags = {}
    for r in res.iter_rows(named=True):
        label = {
            "out_until_date": "Out until",
            "suspended": "Suspended",
            "holdout": "Holdout",
            "questionable_start": "Questionable start",
            "out_indefinitely": "Out indefinitely",
        }[r["status"]]
        when = (
            f" {r['expected_return']}"
            if r["status"] == "out_until_date" and r["expected_return"]
            else ""
        )
        tags[int(r["nba_player_id"])] = f"{label}{when} (news {r['source_date']})"
    return tags


def load(wh: Warehouse, meta: SheetMeta) -> dict[str, Any]:
    proj = wh.read(PROJ_SQL)
    latest = proj.get_column("method").mode().first() if proj.height else None
    return build_data(
        wh.read(VALUES_SQL),
        proj.filter(pl.col("method") == latest) if latest else proj,
        wh.read(BOUNCE_SQL),
        wh.read(PROFILE_SQL),
        wh.read(TEAMS_SQL),
        meta,
        override_tags(wh),
    )


def render_html(data: dict[str, Any]) -> str:
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    live = (Path(__file__).with_name("draft_live.js")).read_text(encoding="utf-8")
    return TEMPLATE.replace("__LIVE_JS__", live).replace("__DATA__", payload)


TEMPLATE = (Path(__file__).with_name("draft_sheet.html")).read_text(encoding="utf-8")
