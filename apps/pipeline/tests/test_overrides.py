from datetime import date
from pathlib import Path

import polars as pl
import pytest

from dikit.errors import ContractViolation
from fantasy_pipeline import overrides as ov

HEADER = (
    "player_name,team,status,expected_return,est_games_missed,source_url,source_date,quote,note\n"
)
PROFILE = pl.DataFrame(
    {"nba_player_id": [1, 2, 3], "player_name": ["Nikola Jokić", "Jayson Tatum", "Kyrie Irving"]}
)


def _csv(tmp_path: Path, rows: str) -> Path:
    p = tmp_path / "o.csv"
    p.write_text(HEADER + rows, encoding="utf-8")
    return p


def test_caps_from_estimate_or_return_date(tmp_path: Path) -> None:
    p = _csv(
        tmp_path,
        'Jayson Tatum,BOS,out_until_date,2027-01-10,,https://x,2026-09-20,"out until January",\n'
        "Kyrie Irving,DAL,out_indefinitely,,20,https://y,2026-09-01,q,\n"
        "Nikola Jokic,DEN,out_indefinitely,,,https://z,2026-09-10,q,\n",
    )
    o = ov.resolve(ov.load(p, date(2026, 10, 18)), PROFILE)
    caps = dict(zip(o["nba_player_id"].to_list(), o["games_cap"].to_list(), strict=True))
    assert caps[3] == 62  # 82 - 20
    assert 30 < caps[2] < 45  # ~ half the season left after 10 Jan
    assert caps[1] is None  # no estimate: no numeric change (accent-insensitive match worked)
    proj = pl.DataFrame({"nba_player_id": [1, 2, 3], "games": [70.0, 70.0, 70.0]})
    out = dict(
        zip(
            *ov.apply(proj, o).select("nba_player_id", "games").to_dict(as_series=False).values(),
            strict=True,
        )
    )
    assert out[1] == 70
    assert out[3] == 62
    assert out[2] == caps[2]


def test_rejects_future_sources_unknown_status_and_unmatched_names(tmp_path: Path) -> None:
    with pytest.raises(ContractViolation, match="after the draft"):
        ov.load(
            _csv(tmp_path, "Jayson Tatum,BOS,out_until_date,2027-01-10,,u,2026-10-19,q,\n"),
            date(2026, 10, 18),
        )
    with pytest.raises(ContractViolation, match="status"):
        ov.load(_csv(tmp_path, "Jayson Tatum,BOS,hurt,,,u,2026-09-01,q,\n"), date(2026, 10, 18))
    o = ov.load(
        _csv(tmp_path, "Nobody Here,BOS,suspended,,5,u,2026-09-01,q,\n"), date(2026, 10, 18)
    )
    with pytest.raises(ContractViolation, match="Nobody Here"):
        ov.resolve(o, PROFILE)


def test_missing_file_means_no_overrides(tmp_path: Path) -> None:
    assert ov.load(tmp_path / "none.csv", date(2026, 10, 18)).height == 0


# ------------------------------------------------------------------ DATA-036: raises
RAISE_HEADER = HEADER.rstrip("\n") + ",expected_games,expected_mpg\n"


def _raise_csv(tmp_path: Path, rows: str) -> Path:
    p = tmp_path / "r.csv"
    p.write_text(RAISE_HEADER + rows, encoding="utf-8")
    return p


def _proj() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nba_player_id": [1, 2],
            "games": [45.0, 70.0],
            "mpg": [27.8, 30.0],
            "pts": [23.9, 20.0],
            "fga": [15.0, 14.0],
            "fgm": [9.0, 7.0],
            "fg_pct": [0.6, 0.5],
        }
    )


def test_cleared_raises_games_and_scales_stats_with_minutes(tmp_path: Path) -> None:
    p = _raise_csv(
        tmp_path,
        'Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,"no minutes restriction",,68,33\n',
    )
    o = ov.resolve(ov.load(p, date(2026, 10, 18)), PROFILE)
    out = ov.apply(_proj(), o).sort("nba_player_id")
    j = out.row(0, named=True)
    assert j["games"] == 68.0  # raised
    assert j["mpg"] == 33.0
    assert j["pts"] == pytest.approx(23.9 * 33 / 27.8)  # per-minute rate kept
    assert j["fga"] == pytest.approx(15.0 * 33 / 27.8)
    assert j["fg_pct"] == 0.6  # percentages unchanged
    assert out.row(1, named=True)["games"] == 70.0  # others untouched


def test_cleared_never_lowers_games(tmp_path: Path) -> None:
    p = _raise_csv(tmp_path, "Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,q,,40,\n")
    o = ov.resolve(ov.load(p, date(2026, 10, 18)), PROFILE)
    assert ov.apply(_proj(), o).sort("nba_player_id")["games"][0] == 45.0


@pytest.mark.parametrize(
    ("row", "match"),
    [
        ("Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,q,,90,\n", "implausible"),
        ("Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,q,,,44\n", "implausible"),
        ("Nikola Jokic,DEN,cleared,,,,2026-10-10,q,,68,\n", "evidence"),
        ("Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,,,68,\n", "evidence"),
        (
            "Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,q,,,\n",
            "expected_games or expected_mpg",
        ),
        (
            "Nikola Jokic,DEN,cleared,,,https://n,2026-10-10,q,,68,\n"
            "Nikola Jokic,DEN,out_indefinitely,,10,https://m,2026-10-09,q,,,\n",
            "contradictory",
        ),
        ("Nikola Jokic,DEN,cleared,,,https://n,2026-10-30,q,,68,\n", "after the draft"),
        ("Nikola Jokic,DEN,cleared,,10,https://n,2026-10-10,q,,68,\n", "cap fields"),
        ("Nikola Jokic,DEN,cleared,2026-11-01,,https://n,2026-10-10,q,,68,\n", "cap fields"),
    ],
)
def test_rejects_bad_raises(tmp_path: Path, row: str, match: str) -> None:
    with pytest.raises(ContractViolation, match=match):
        ov.load(_raise_csv(tmp_path, row), date(2026, 10, 18))


def test_old_files_without_raise_columns_still_load(tmp_path: Path) -> None:
    p = _csv(tmp_path, "Kyrie Irving,DAL,out_indefinitely,,20,https://y,2026-09-01,q,\n")
    assert ov.load(p, date(2026, 10, 18))["games_cap"].to_list() == [62.0]
