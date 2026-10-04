from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl
from fastapi.testclient import TestClient

from fantasy_api import badges as badge_rules
from fantasy_api.errors import PROBLEM_BASE

Client = Callable[[Path], TestClient]
CATS = ("fg_pct", "ft_pct", "fg3m", "pts", "reb", "ast", "stl", "blk", "tov")


def _values(variants: tuple[str, ...] = ("all", "punt_ast")) -> pl.DataFrame:
    rows = []
    for variant in variants:
        for i, (pid, name, pos) in enumerate(
            [
                (1, "Nikola Jokić", "C"),
                (2, "Shai Gilgeous-Alexander", "G"),
                (3, "No Position", None),
            ]
        ):
            rows.append(
                {
                    "nba_player_id": pid,
                    "player_name": name,
                    "nba_position": pos,
                    "value": 6.0 - i,
                    "dollars": 60.0 - 25 * i,
                    "overall_rank": i + 1 if variant == "all" else 3 - i,
                    "tier": i + 1,
                    "drafted": i < 2,
                    "variant": variant,
                    "league_teams": 1,  # a one-team "first round": only rank 1 is first-round value
                    **{f"s_{c}": 1.0 - i for c in CATS},
                }
            )
    return pl.DataFrame(rows)


def _projections() -> pl.DataFrame:
    per_game = {
        "pts": 26.0,
        "reb": 12.0,
        "ast": 9.0,
        "stl": 1.4,
        "blk": 0.8,
        "fg3m": 1.1,
        "tov": 3.0,
        "fgm": 10.0,
        "fga": 17.0,
        "ftm": 5.0,
        "fta": 6.0,
        "mpg": 34.0,
        "games": 70.0,
    }
    created = datetime(2026, 9, 26, 8, 0, tzinfo=UTC)
    return pl.DataFrame(
        [
            {"season": "2026-27", "nba_player_id": pid, "stat": s, "mean": m, "created_at": created}
            for pid in (1, 2)
            for s, m in per_game.items()
        ]
    )


def _week() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "nba_player_id": [1, 2],
            "team": ["DEN", "OKC"],
            "status_today": ["Questionable", None],
            "as_of_day": [date(2026, 10, 21)] * 2,
        }
    )


def seed(root: Path, *, week: bool = True) -> Path:
    (root / "predictions").mkdir(parents=True, exist_ok=True)
    _values().write_parquet(root / "predictions" / "auction_values.parquet")
    _projections().write_parquet(root / "predictions" / "preseason_projection.parquet")
    if week:
        _week().write_parquet(root / "predictions" / "week_projection.parquet")
    return root


def test_players_are_ranked_with_values_projections_and_context(
    client_for: Client, tmp_path: Path
) -> None:
    body = client_for(seed(tmp_path)).get("/players").json()
    assert body["variant"] == "all"
    assert body["variants"] == ["all", "punt_ast"]
    jokic, sga, nopos = body["players"]
    assert (jokic["rank"], jokic["name"], jokic["team"], jokic["positions"]) == (
        1,
        "Nikola Jokić",
        "DEN",
        "C",
    )
    assert jokic["status"] == "Questionable"
    assert jokic["dollars"] == 60.0
    assert jokic["projection"]["pts"] == 26.0
    assert jokic["projection"]["fg3m"] == 1.1  # the stat code, not to_camel's "fg3M"
    assert jokic["projection"]["fgPct"] == round(10 / 17, 3)
    assert jokic["strengths"]["pts"] == 1.0
    assert sga["status"] is None
    assert (nopos["positions"], nopos["team"], nopos["projection"]) == (None, None, None)
    assert body["freshness"]["asOf"] == "2026-09-26T08:00:00Z"


def test_a_punt_variant_reranks(client_for: Client, tmp_path: Path) -> None:
    body = client_for(seed(tmp_path)).get("/players", params={"variant": "punt_ast"}).json()
    assert [p["rank"] for p in body["players"]] == [1, 2, 3]
    assert body["players"][0]["name"] == "No Position"


def test_unknown_variant_and_missing_data_are_problems(client_for: Client, tmp_path: Path) -> None:
    r = client_for(tmp_path).get("/players")
    assert r.status_code == 404
    assert r.json()["type"] == f"{PROBLEM_BASE}/no-players"
    r = client_for(seed(tmp_path)).get("/players", params={"variant": "punt_everything"})
    assert r.status_code == 422
    assert r.json()["type"] == f"{PROBLEM_BASE}/invalid-request"


def test_works_without_a_week_table(client_for: Client, tmp_path: Path) -> None:
    body = client_for(seed(tmp_path, week=False)).get("/players").json()
    assert body["players"][0]["team"] is None
    assert body["players"][0]["status"] is None


def test_large_responses_are_compressed(client_for: Client, tmp_path: Path) -> None:
    r = client_for(seed(tmp_path)).get("/players", headers={"Accept-Encoding": "gzip"})
    assert r.headers["content-encoding"] == "gzip"


def test_healthy_rank_is_served_when_published(client_for: Client, tmp_path: Path) -> None:
    seed(tmp_path)
    vals = _values().with_columns(
        (4 - pl.col("overall_rank")).alias("healthy_rank"),
        (pl.col("dollars") + 5).alias("healthy_dollars"),
    )
    vals.write_parquet(tmp_path / "predictions" / "auction_values.parquet")
    jokic = client_for(tmp_path).get("/players").json()["players"][0]
    assert (jokic["healthyRank"], jokic["healthyDollars"]) == (3, 65.0)


def test_healthy_rank_is_null_for_older_values_files(client_for: Client, tmp_path: Path) -> None:
    jokic = client_for(seed(tmp_path)).get("/players").json()["players"][0]
    assert (jokic["healthyRank"], jokic["healthyDollars"]) == (None, None)


# --- WEB-018 badges ------------------------------------------------------------------------------

HISTORY = "player_history.parquet"
BREAKOUT = "breakout_probability.parquet"
SEASONS = ("2023-24", "2024-25", "2025-26")
TOP_TIER_BADGE = {
    "code": "top_tier",
    "label": "First-round value",
    "tone": "accent",
    "why": "#1 for this strategy: first-round value in a 1-team league",
}


def _season_rows(
    pid: int, games: tuple[int, int, int], mpg: float = 30.0
) -> list[dict[str, object]]:
    return [
        {
            "nba_player_id": pid,
            "season": s,
            "games_played": g,
            "season_team_games": 82,
            "minutes": g * mpg,
            "age": 28.0,  # the published history carries age (WEB-020)
            "draft_year": 2015,
            "overall_pick": 41,
        }
        for s, g in zip(SEASONS, games, strict=True)
    ]


def _rookie_row(pid: int) -> dict[str, object]:
    return {
        "nba_player_id": pid,
        "season": None,
        "games_played": None,
        "season_team_games": None,
        "minutes": None,
        "draft_year": 2026,
        "overall_pick": 3,
    }


def _write(root: Path, name: str, rows: list[dict[str, object]]) -> None:
    pl.DataFrame(rows).write_parquet(root / "predictions" / name)


def _seed_with_season(root: Path, *, week: bool = True) -> Path:
    seed(root, week=week)
    vals = _values().with_columns(pl.lit("2026-27").alias("season"))
    vals.write_parquet(root / "predictions" / "auction_values.parquet")
    return root


def _badges(client: TestClient, variant: str = "all") -> dict[str, list[dict[str, str]]]:
    body = client.get("/players", params={"variant": variant}).json()
    return {p["name"]: p["badges"] for p in body["players"]}


def _codes(client: TestClient, variant: str = "all") -> dict[str, list[str]]:
    return {n: [b["code"] for b in bs] for n, bs in _badges(client, variant).items()}


def test_badges_constants_are_pinned() -> None:
    assert badge_rules.ROTATION_MPG == 20.0
    assert badge_rules.AVAILABILITY_CUT == 0.6
    assert badge_rules.HISTORY_SEASONS == 3
    assert badge_rules.INJURY_PRONE_MIN_SEASONS == 2
    assert badge_rules.TOP_SHARE == 0.2
    assert badge_rules.PRIORITY == (
        "injured_today",
        "adjusted",
        "injury_prone",
        "missed_time",
        "breakout",
        "bounce_back",
        "rookie",
        "top_tier",
    )


def test_badges_injury_prone_needs_two_low_rotation_seasons(
    client_for: Client, tmp_path: Path
) -> None:
    _seed_with_season(tmp_path)
    _write(
        tmp_path,
        HISTORY,
        _season_rows(1, (38, 19, 39))  # three low seasons
        + _season_rows(2, (80, 30, 70)),  # one low season, not the last: no injury badge
    )
    badges = _badges(
        client_for(
            tmp_path,
        )
    )
    jokic = badges["Nikola Jokić"]
    assert jokic[1] == {
        "code": "injury_prone",
        "label": "Injury prone",
        "tone": "lose",
        "why": "Played 38, 19 and 39 of 82 games in the last three seasons",
    }
    assert "missed_time" not in [b["code"] for b in jokic]  # Injury prone already says it
    assert badges["Shai Gilgeous-Alexander"] == []


def test_badges_bench_seasons_do_not_count_as_injury(client_for: Client, tmp_path: Path) -> None:
    _seed_with_season(tmp_path)
    _write(tmp_path, HISTORY, _season_rows(2, (80, 33, 24), mpg=15.0))  # Gillespie-like
    assert _codes(client_for(tmp_path))["Shai Gilgeous-Alexander"] == []


def test_badges_missed_time_is_last_season_only(client_for: Client, tmp_path: Path) -> None:
    _seed_with_season(tmp_path)
    _write(tmp_path, HISTORY, _season_rows(2, (80, 78, 36)) + _season_rows(3, (80, 36, 78)))
    badges = _badges(client_for(tmp_path))
    assert badges["Shai Gilgeous-Alexander"] == [
        {
            "code": "missed_time",
            "label": "Missed time",
            "tone": "warn",
            "why": "Played 36 of 82 games last season",
        }
    ]
    assert badges["No Position"] == []  # the low season was two seasons ago


def test_badges_injury_why_names_seasons_when_some_are_missing(
    client_for: Client, tmp_path: Path
) -> None:
    _seed_with_season(tmp_path)
    rows = _season_rows(2, (30, 82, 40))
    del rows[1]
    rows[1]["season_team_games"] = 80
    _write(tmp_path, HISTORY, rows)
    sga = _badges(client_for(tmp_path))["Shai Gilgeous-Alexander"]
    assert [b["code"] for b in sga] == ["injury_prone"]
    assert sga[0]["why"] == "Played 30 of 82 and 40 of 80 games in 2023-24 and 2025-26"


def test_badges_only_the_last_three_seasons_before_the_target_count(
    client_for: Client, tmp_path: Path
) -> None:
    _seed_with_season(tmp_path)
    old = _season_rows(2, (10, 10, 10))
    for r, s in zip(old, ("2020-21", "2021-22", "2022-23"), strict=True):
        r["season"] = s
    _write(tmp_path, HISTORY, old + _season_rows(2, (80, 80, 80)))
    assert _codes(client_for(tmp_path))["Shai Gilgeous-Alexander"] == []


def test_badges_rookie_is_drafted_in_the_target_seasons_draft(
    client_for: Client, tmp_path: Path
) -> None:
    _seed_with_season(tmp_path)
    _write(tmp_path, HISTORY, [*_season_rows(2, (80, 80, 80)), _rookie_row(3)])
    badges = _badges(client_for(tmp_path))
    assert badges["No Position"] == [
        {"code": "rookie", "label": "Rookie", "tone": "neutral", "why": "2026 draft, pick 3"}
    ]
    assert badges["Shai Gilgeous-Alexander"] == []  # drafted in 2015


def test_badges_rookie_needs_the_values_season(client_for: Client, tmp_path: Path) -> None:
    seed(tmp_path)  # an older values file without a season column
    _write(tmp_path, HISTORY, [_rookie_row(3)])
    assert _codes(client_for(tmp_path))["No Position"] == []


def test_badges_breakout_and_bounce_back_are_the_top_fifth(
    client_for: Client, tmp_path: Path
) -> None:
    _seed_with_season(tmp_path, week=False)
    rows: list[dict[str, object]] = []
    # 10 growth probabilities: the top 20 % is the top 2 (players 1 and 2).
    for i, p in enumerate([0.34, 0.30, 0.2, 0.1, 0.1, 0.1, 0.05, 0.05, 0.05, 0.01]):
        rows.append(
            {"nba_player_id": i + 1, "kind": "growth", "p_breakout": p, "season": "2026-27"}
        )
    # 5 bounce-back probabilities: the top 20 % is the top 1 (player 2).
    for i, p in enumerate([0.41, 0.2, 0.1, 0.1, 0.05]):
        rows.append(
            {"nba_player_id": i + 2, "kind": "bounce_back", "p_breakout": p, "season": "2026-27"}
        )
    _write(tmp_path, BREAKOUT, rows)
    badges = _badges(client_for(tmp_path))
    assert badges["Nikola Jokić"] == [
        {
            "code": "breakout",
            "label": "Breakout chance",
            "tone": "accent",
            "why": "Breakout chance 34 % (top 20 %)",
        },
        TOP_TIER_BADGE,
    ]
    sga = badges["Shai Gilgeous-Alexander"]
    assert [b["code"] for b in sga] == ["breakout", "bounce_back"]
    assert sga[1] == {
        "code": "bounce_back",
        "label": "Bounce-back",
        "tone": "win",
        "why": "Bounce-back chance 41 % (top 20 %)",
    }
    assert badges["No Position"] == []  # 0.20 growth: outside the top fifth


def test_badges_breakout_uses_the_latest_season(client_for: Client, tmp_path: Path) -> None:
    _seed_with_season(tmp_path)
    _write(
        tmp_path,
        BREAKOUT,
        [
            {"nba_player_id": 3, "kind": "growth", "p_breakout": 0.9, "season": "2025-26"},
            {"nba_player_id": 2, "kind": "growth", "p_breakout": 0.3, "season": "2026-27"},
            {"nba_player_id": 3, "kind": "growth", "p_breakout": 0.1, "season": "2026-27"},
        ],
    )
    codes = _codes(client_for(tmp_path))
    assert codes["Shai Gilgeous-Alexander"] == ["breakout"]
    assert codes["No Position"] == []


def test_badges_top_tier_follows_the_strategy(client_for: Client, tmp_path: Path) -> None:
    seed(tmp_path, week=False)
    assert _codes(client_for(tmp_path)) == {
        "Nikola Jokić": ["top_tier"],
        "Shai Gilgeous-Alexander": [],
        "No Position": [],
    }
    punt = _badges(client_for(tmp_path), "punt_ast")
    assert punt["No Position"] == [TOP_TIER_BADGE]  # rank 1 under the punt: follows the strategy
    assert punt["Nikola Jokić"] == []


def test_badges_injured_today_comes_first(client_for: Client, tmp_path: Path) -> None:
    _seed_with_season(tmp_path)
    _write(tmp_path, HISTORY, _season_rows(1, (38, 19, 39)))
    badges = _badges(client_for(tmp_path))["Nikola Jokić"]
    assert [b["code"] for b in badges] == ["injured_today", "injury_prone", "top_tier"]
    assert badges[0] == {
        "code": "injured_today",
        "label": "Questionable",
        "tone": "warn",
        "why": "Questionable on today's report",
    }


def test_badges_missing_inputs_mean_no_badges_and_a_note(
    client_for: Client, tmp_path: Path
) -> None:
    body = client_for(seed(tmp_path, week=False)).get("/players").json()
    assert [p["badges"] for p in body["players"]] == [[TOP_TIER_BADGE], [], []]
    assert body["badgeNotes"] == [
        "Breakout model not published",
        "Injury history not published",
        "Steady / Volatile appears after the next daily run",
    ]


def test_badges_notes_are_empty_when_inputs_exist(client_for: Client, tmp_path: Path) -> None:
    _seed_with_season(tmp_path)
    _write(tmp_path, HISTORY, _season_rows(1, (80, 80, 80)))
    _write(
        tmp_path,
        BREAKOUT,
        [{"nba_player_id": 1, "kind": "growth", "p_breakout": 0.1, "season": "2026-27"}],
    )
    _write(
        tmp_path,
        "player_consistency.parquet",
        [
            {
                "nba_player_id": 1,
                "season": "2025-26",
                "weeks": 20,
                "weekly_sd": 1.0,
                "weekly_mean": 4.0,
                "rel_sd": 0.25,
                "pct": 0.5,
            }
        ],
    )
    assert client_for(tmp_path).get("/players").json()["badgeNotes"] == []


def test_notes_name_missing_sources(client_for: Client, tmp_path: Path) -> None:
    """WEB-022: no growth rows, no league size, no consistency → each says when it arrives."""
    seed(tmp_path, week=False)
    _values().drop("league_teams").write_parquet(
        tmp_path / "predictions" / "auction_values.parquet"
    )
    _write(
        tmp_path,
        BREAKOUT,
        [{"nba_player_id": 2, "kind": "bounce_back", "p_breakout": 0.4, "season": "2026-27"}],
    )
    notes = client_for(tmp_path).get("/players").json()["badgeNotes"]
    assert "Breakout chance appears after the pre-season backfill (draft week)" in notes
    assert "First-round value appears after the next daily run" in notes
    assert "Steady / Volatile appears after the next daily run" in notes


def test_badges_first_round_value(client_for: Client, tmp_path: Path) -> None:
    seed(tmp_path, week=False)
    _values().with_columns(pl.lit(2).alias("league_teams")).write_parquet(
        tmp_path / "predictions" / "auction_values.parquet"
    )
    codes = _codes(client_for(tmp_path))
    assert codes["Nikola Jokić"] == ["top_tier"]
    assert codes["Shai Gilgeous-Alexander"] == ["top_tier"]  # rank 2 in a 2-team league
    assert codes["No Position"] == []


# --- WEB-020 indicators ---------------------------------------------------------------------------


def test_indicators_are_served_with_a_row_signal(client_for: Client, tmp_path: Path) -> None:
    root = seed(tmp_path)
    proj = _projections().with_columns(pl.lit(1.0).alias("sd"))
    proj.write_parquet(root / "predictions" / "preseason_projection.parquet")
    pl.DataFrame(
        {
            "nba_player_id": [1, 2],
            "season": ["2025-26", "2025-26"],
            "games_played": [70, 70],
            "season_team_games": [82, 82],
            "minutes": [70 * 30.0, 70 * 34.0],
            "age": [30.0, 27.0],
            "draft_year": [2014, 2018],
            "overall_pick": [41, 11],
        }
    ).write_parquet(root / "predictions" / "player_history.parquet")
    body = client_for(root).get("/players").json()
    jokic = body["players"][0]
    codes = {i["code"] for i in jokic["indicators"]}
    assert {"range", "certainty", "role", "age"} <= codes
    assert jokic["signal"]["code"] == "role"  # 34 projected vs 30 last season
    assert jokic["signal"]["why"] == "Projected 34.0 min vs 30.0 last season"
    nopos = body["players"][2]
    assert nopos["indicators"] == []
    assert nopos["signal"] is None


def test_indicators_absent_without_inputs(client_for: Client, tmp_path: Path) -> None:
    jokic = client_for(seed(tmp_path)).get("/players").json()["players"][0]
    assert jokic["indicators"] == []  # the seeded projection has no sd column
    assert jokic["signal"] is None


def test_badges_adjusted_shows_the_cited_source(client_for: Client, tmp_path: Path) -> None:
    """DATA-036: an owner-reviewed raise is visible with its evidence."""
    seed(tmp_path, week=False)
    note = "Cleared: no minutes restriction (2026-10-10)"
    _values().with_columns(
        pl.when(pl.col("nba_player_id") == 2).then(pl.lit(note)).otherwise(None).alias("adjusted")
    ).write_parquet(tmp_path / "predictions" / "auction_values.parquet")
    sga = next(p for p in client_for(tmp_path).get("/players").json()["players"] if p["id"] == 2)
    assert {"code": "adjusted", "label": "Adjusted", "tone": "accent", "why": note} in sga["badges"]


def test_badges_adjusted_absent_without_the_column(client_for: Client, tmp_path: Path) -> None:
    codes = _codes(client_for(seed(tmp_path, week=False)))
    assert all("adjusted" not in c for c in codes.values())
