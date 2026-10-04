import polars as pl
import pytest

from fantasy_decision import brief
from fantasy_decision import explain as ex

STATS = ["pts", "reb", "ast", "stl", "blk", "fg3m", "tov", "fgm", "fga", "ftm", "fta"]


def _player(pid: int, name: str, scale: float, **kw: object) -> dict[str, object]:
    row: dict[str, object] = {
        "nba_player_id": pid,
        "player_name": name,
        "team": "AAA",
        "games_left": 3,
        "exp_games": 3.0,
        "plays_today": True,
        "status_today": None,
    }
    per_game = {"pts": 20, "reb": 5, "ast": 5, "stl": 1, "blk": 0.5, "fg3m": 2, "tov": 2}
    per_game |= {"fgm": 7, "fga": 15, "ftm": 4, "fta": 5}
    row |= {s: per_game[s] * scale * float(row["exp_games"]) for s in STATS}  # type: ignore[arg-type]
    row |= kw
    return row


WEEK = pl.DataFrame(
    [
        _player(1, "Star Guard", 1.5),
        _player(2, "Solid Forward", 1.0),
        _player(3, "Idle Center", 1.0, plays_today=False),
        _player(4, "Hurt Wing", 1.0, status_today="Out"),
        _player(5, "Iffy Guard", 1.0, status_today="Questionable"),
        _player(6, "Bench Scrub", 0.3),
        _player(10, "Opp One", 1.0),
        _player(11, "Opp Two", 1.0),
        _player(20, "Free Big", 1.0, blk=9.0, reb=40.0),
        _player(21, "Free Nobody", 0.1),
        _player(22, "Free Idle", 1.0, games_left=0, exp_games=0.0),
    ]
)
POS = {
    1: ("G",),
    2: ("F",),
    3: ("C",),
    4: ("G", "F"),
    5: ("G",),
    6: ("F",),
    20: ("F", "C"),
    21: ("G",),
}
VALUE = {1: 5.0, 2: 3.0, 3: 2.5, 4: 2.0, 5: 1.5, 6: -1.0, 20: 1.0, 21: -2.0, 22: 0.5}
MINE = [1, 2, 3, 4, 5, 6]
SLOTS = {"G": 1, "F": 1, "C": 1, "Util": 1}


def test_lineup_benches_players_without_a_game_or_ruled_out_and_flags_questionable() -> None:
    lu = {x.player_id: x for x in brief.lineup(WEEK, MINE, POS, VALUE, SLOTS)}
    assert lu[3].slot == "BN"
    assert "no game" in lu[3].reason
    assert lu[4].slot == "BN"
    assert "Out" in lu[4].reason
    assert lu[1].slot in {"G", "Util"}  # the best guard is active (slot labels are ties)
    assert lu[5].slot != "BN"  # active, but flagged
    assert lu[6].slot == "BN"  # the lowest value misses out when slots are full
    assert "Questionable" in lu[5].reason
    active = [x for x in lu.values() if x.slot != "BN"]
    assert len(active) <= sum(SLOTS.values())


def test_category_win_probabilities_favour_the_stronger_side_and_invert_turnovers() -> None:
    mine = brief.team_totals(WEEK, [1, 2])
    theirs = brief.team_totals(WEEK, [10])
    p = brief.win_probs(mine, theirs)
    assert p["pts"] > 0.9
    assert p["tov"] < 0.1  # more turnovers is worse
    assert 0.0 <= p["fg_pct"] <= 1.0


def test_pickups_rank_by_category_wins_gained_against_the_opponent() -> None:
    picks = brief.pickups(WEEK, MINE, [10, 11], rostered=set(MINE) | {10, 11}, value=VALUE, n=3)
    assert picks[0].add_id == 20  # the rebound/block specialist
    assert picks[0].drop_id == 6  # my lowest-value player
    assert picks[0].gain > 0
    assert "blk" in picks[0].helps
    assert all(p.add_id != 22 for p in picks)  # no games left this week


def test_pickups_without_an_opponent_use_weekly_value() -> None:
    picks = brief.pickups(WEEK, MINE, None, rostered=set(MINE), value=VALUE, n=2)
    assert picks[0].add_id == 20
    assert picks[0].helps == []


def test_render_is_short_markdown_from_structured_evidence_only() -> None:
    b = brief.build(
        WEEK, MINE, [10, 11], rostered=set(MINE) | {10, 11}, positions=POS, value=VALUE, slots=SLOTS
    )
    md = brief.render(b, day="Tue 20 Oct", opponent="Team 7")
    assert md.startswith("*Tue 20 Oct")
    assert "Hurt Wing" in md
    assert "Free Big" in md
    assert len(md) < 3500  # fits one Telegram message (4,096 max)
    for word in ("probably", "likely", "I think"):
        assert word not in md


@pytest.mark.parametrize(("p", "label"), [(0.8, "▲"), (0.2, "▼"), (0.5, "●")])
def test_marks_use_icons_not_colour(p: float, label: str) -> None:
    assert brief.mark(p) == label


def test_counting_variances_are_negative_binomial_wider_than_poisson() -> None:
    tot = brief.team_totals(WEEK, [1, 2])
    mean, var = tot["pts"]
    assert var > mean  # Poisson would give var == mean


def test_every_number_in_the_brief_comes_from_evidence() -> None:
    b = brief.build(
        WEEK, MINE, [10, 11], rostered=set(MINE) | {10, 11}, positions=POS, value=VALUE, slots=SLOTS
    )
    lines = brief.explained(b, day="Tue 20 Oct", opponent="Team 7")
    assert "\n".join(e.text for e in lines) == brief.render(b, day="Tue 20 Oct", opponent="Team 7")
    assert b.pickups  # the test covers the pickup lines too
    # Golden text rendered by the pre-template implementation (DEC-009 changed no wording).
    assert brief.render(b, day="Tue 20 Oct", opponent="Team 7") == GOLDEN_BRIEF
    assert [(e.text, ex.ungrounded(e)) for e in lines if ex.ungrounded(e)] == []


GOLDEN_BRIEF = "\n".join(
    [
        "*Tue 20 Oct* · vs Team 7",
        "",
        "*Matchup*: 6.9 of 9 categories expected",
        "PTS ▲ REB ▲ AST ▲ STL ▲ BLK ▲ 3PM ▲ TO ▼ FG% ● FT% ●",
        "",
        "*Lineup today*",
        "Util: Star Guard (plays today)",
        "F: Solid Forward (plays today)",
        "BN: Idle Center (no game today)",
        "BN: Hurt Wing (Out on today's injury report)",
        "G: Iffy Guard (Questionable: check the last report before tip-off)",
        "BN: Bench Scrub (active slots full)",
        "",
        "*Injury report*",
        "Hurt Wing: Out",
        "Iffy Guard: Questionable",
        "",
        "*Pickups* (add / drop, gain this week)",
        "+Free Big / -Bench Scrub: +0.07 cat. wins, 3 games, helps BLK",
        "+Free Nobody / -Bench Scrub: -0.01 cat. wins, 3 games",
    ]
)
