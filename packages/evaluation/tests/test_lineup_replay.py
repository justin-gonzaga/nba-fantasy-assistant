import polars as pl

from fantasy_evaluation import lineup_replay as lr


def test_replay_counts_days_and_never_finds_the_optimiser_worse() -> None:
    n = lr.TEAMS * lr.ROUNDS
    values = pl.DataFrame(
        {
            "nba_player_id": list(range(n)),
            "value": [float(n - i) for i in range(n)],
            "nba_position": ["F-C", "F", "G", "C", "G-F"] * (n // 5) + ["G"] * (n % 5),
        }
    )
    logs = pl.DataFrame(
        {
            "GAME_DATE": ["2025-11-01"] * (n // 2) + ["2025-11-02"] * (n // 2),
            "PLAYER_ID": list(range(0, n, 2)) + list(range(1, n, 2)),
        }
    )
    res = lr.run(logs, values)
    assert res.lineups == 2 * lr.TEAMS
    assert res.worse == 0
    assert res.illegal == 0
    assert res.ships
