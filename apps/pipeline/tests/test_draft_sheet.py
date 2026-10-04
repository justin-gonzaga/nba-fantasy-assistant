import re
import shutil
import subprocess
from pathlib import Path

import polars as pl
import pytest

from fantasy_pipeline import draft_sheet as ds

META = ds.SheetMeta(16, 200, 224, "H2H categories", "H1+aging+M1", "26 Sep 2026", 2026)
CATS = ["fg_pct", "ft_pct", "fg3m", "pts", "reb", "ast", "stl", "blk", "tov"]


def _values() -> pl.DataFrame:
    rows = []
    for variant in ("all", "punt_ft_pct"):
        for i in range(250):
            rows.append(
                {
                    "nba_player_id": i,
                    "player_name": f"Player {i}",
                    "nba_position": ["G", "F-C", "C", None][i % 4],
                    "variant": variant,
                    "overall_rank": i + 1,
                    "dollars": max(1.0, 60 - i * 0.3),
                    "tier": 1 + i // 40,
                    **{
                        f"s_{c}": (1.5 if c == "blk" else -1.2 if c == "ft_pct" else 0.1)
                        for c in CATS
                    },
                }
            )
    return pl.DataFrame(rows)


def _proj() -> pl.DataFrame:
    stats = [
        "pts",
        "reb",
        "ast",
        "stl",
        "blk",
        "fg3m",
        "tov",
        "fgm",
        "fga",
        "ftm",
        "fta",
        "games",
        "mpg",
    ]
    return pl.DataFrame(
        [
            {
                "nba_player_id": i,
                "stat": s,
                "mean": 5.0,
                "source": "rookie_prior" if i == 3 else "history",
                "method": "H1+aging+M1",
            }
            for i in range(250)
            for s in stats
        ]
    )


def _data() -> dict:  # type: ignore[type-arg]
    return ds.build_data(
        _values(),
        _proj(),
        pl.DataFrame({"nba_player_id": [1, 2], "p_breakout": [0.35, 0.05]}),
        pl.DataFrame(
            {
                "nba_player_id": list(range(250)),
                "nba_team_id": [7] * 250,
                "age_at_midseason": [24.0] * 250,
                "draft_year": [2026 if i == 3 else 2019 for i in range(250)],
            }
        ),
        pl.DataFrame({"nba_team_id": [7], "team_abbreviation": ["BOS"]}),
        META,
        {5: "Out until 2027-01-10 (news 2026-09-20)"},
    )


def test_board_has_top_200_per_variant_with_tiers() -> None:
    d = _data()
    assert [v["label"] for v in d["variants"]] == ["All 9 cats", "Punt FT%"]
    assert all(len(v["rows"]) == min(ds.TOP_N, 250) for v in d["variants"])
    assert d["variants"][0]["rows"][0][1] == 1
    assert d["players"]["1"]["bb"] == 0.35  # shown above the threshold
    assert d["players"]["2"]["bb"] is None
    assert d["players"]["3"]["rk"] is True
    assert d["players"]["0"]["t"] == "BOS"


def test_render_embeds_data_and_escapes_script_close() -> None:
    d = _data()
    d["players"]["0"]["n"] = "</script><b>x"
    html = ds.render_html(d)
    assert "<title>2026 Auction Board</title>" in html[:8000]
    assert "</script><b>" not in html
    assert "__DATA__" not in html


def test_csv_has_one_row_per_variant_player(tmp_path: Path) -> None:
    df = ds.to_csv(_data())
    assert df.height == 2 * min(ds.TOP_N, 250)
    assert {"variant", "rank", "player", "dollars", "tier", "z_BLK", "bounce_back"} <= set(
        df.columns
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_page_scripts_parse(tmp_path: Path) -> None:
    """The generated page's inline scripts parse as JavaScript."""
    html = ds.render_html(_data())
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    assert len(scripts) == 2
    for i, js in enumerate(scripts):
        f = tmp_path / f"s{i}.js"
        f.write_text(js, encoding="utf-8")
        subprocess.run(
            [shutil.which("node") or "node", "--check", str(f)], check=True, capture_output=True
        )


def test_override_tag_reaches_the_page() -> None:
    d = _data()
    assert d["players"]["5"]["out"].startswith("Out until 2027-01-10")
    assert d["players"]["0"]["out"] is None
