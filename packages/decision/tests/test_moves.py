from fantasy_decision import moves as mv

BASE = {"pts": 15.0, "reb": 6.0, "ast": 4.0, "stl": 1.0, "blk": 0.8, "fg3m": 1.5, "tov": 2.0}


def _p(scale: float, games: float = 3.0, **kw: float) -> mv.PlayerWeek:
    per_game = {c: v * scale for c, v in BASE.items()} | {
        "fgm": 5.6 * scale,
        "fga": 12 * scale,
        "ftm": 3 * scale,
        "fta": 4 * scale,
    }
    return mv.PlayerWeek(per_game | kw, games)


def _league() -> tuple[dict[int, mv.PlayerWeek], list[int], list[int]]:
    players = {i: _p(1.0) for i in range(10)} | {i: _p(1.0) for i in range(10, 20)}
    players[9] = _p(0.2)  # my weakest player
    players[100] = _p(2.5)  # a strong free agent
    players[101] = _p(0.1)  # a useless free agent
    return players, list(range(10)), list(range(10, 20))


def test_a_clearly_helpful_add_is_recommended_for_the_weakest_player() -> None:
    players, mine, opp = _league()
    best = mv.best_moves(
        mine,
        opp,
        opp,
        [100, 101],
        players,
        players,
        value=dict.fromkeys(players, 1.0) | {9: -2.0},
        draws=800,
        seed=3,
    )
    assert best
    assert (best[0].add, best[0].drop) == (100, 9)
    assert best[0].gain > 0.3


def test_no_move_when_no_free_agent_helps() -> None:
    players, mine, opp = _league()
    players[9] = _p(1.0)
    best = mv.best_moves(
        mine,
        opp,
        opp,
        [101],
        players,
        players,
        value=dict.fromkeys(players, 1.0),
        draws=800,
        seed=3,
    )
    assert best == []


def test_common_random_numbers_make_it_deterministic() -> None:
    players, mine, opp = _league()
    kw = {"value": dict.fromkeys(players, 1.0) | {9: -2.0}, "draws": 500, "seed": 9}
    a = mv.best_moves(mine, opp, opp, [100, 101], players, players, **kw)  # type: ignore[arg-type]
    b = mv.best_moves(mine, opp, opp, [100, 101], players, players, **kw)  # type: ignore[arg-type]
    assert a == b


def test_next_week_counts_with_the_discount() -> None:
    players, mine, opp = _league()
    idle_now = dict(players) | {100: _p(2.5, games=0.0)}  # no games this week, 3 next week
    value = dict.fromkeys(players, 1.0) | {9: -2.0}
    with_next = mv.best_moves(
        mine, opp, opp, [100], idle_now, players, value=value, discount=0.5, draws=800, seed=1
    )
    this_only = mv.best_moves(
        mine, opp, opp, [100], idle_now, players, value=value, discount=0.0, draws=800, seed=1
    )
    assert with_next
    assert with_next[0].add == 100
    assert this_only == [] or this_only[0].gain < with_next[0].gain


def test_below_replacement_values_do_not_favour_idle_free_agents() -> None:
    # Free agents are below replacement (negative value): idle ones must not outrank playing ones.
    players, mine, opp = _league()
    players |= {200 + i: _p(0.5, games=0.0) for i in range(12)}  # idle free agents
    value = dict.fromkeys(players, 1.0) | {9: -2.0, 100: -3.0} | {200 + i: -1.0 for i in range(12)}
    best = mv.best_moves(
        mine, opp, opp, [*range(200, 212), 100], players, players, value=value, draws=800, seed=3
    )
    assert best
    assert best[0].add == 100


def test_pickups_from_the_week_tables_rank_the_two_week_moves() -> None:
    import polars as pl  # noqa: PLC0415 - only this test builds brief-style tables

    stats = {"pts": 15, "reb": 6, "ast": 4, "stl": 1, "blk": 0.8, "fg3m": 1.5, "tov": 2}
    stats |= {"fgm": 5.6, "fga": 12, "ftm": 3, "fta": 4}

    def row(pid: int, scale: float, games: float = 3.0) -> dict[str, object]:
        base: dict[str, object] = {
            "nba_player_id": pid,
            "player_name": f"P{pid}",
            "games_left": int(games),
            "exp_games": games,
        }
        return base | {s: v * scale * games for s, v in stats.items()}

    rows = [row(i, 1.0) for i in range(20)] + [row(9, 0.2), row(100, 2.5), row(101, 0.1)]
    table = pl.DataFrame(rows[:9] + rows[10:])  # player 9 is the weak one
    mine, opp = list(range(10)), list(range(10, 20))
    value = dict.fromkeys(range(20), 1.0) | {9: -2.0, 100: -3.0, 101: -4.0}
    picks = mv.pickups(
        table, table, mine, opp, opp, rostered=set(mine) | set(opp), value=value, draws=500
    )
    assert picks
    assert (picks[0].add_id, picks[0].drop_id) == (100, 9)
    assert picks[0].add_name == "P100"
    assert picks[0].gain > 0
    assert set(picks[0].helps) <= {
        "pts",
        "reb",
        "ast",
        "stl",
        "blk",
        "fg3m",
        "tov",
        "fg_pct",
        "ft_pct",
    }
