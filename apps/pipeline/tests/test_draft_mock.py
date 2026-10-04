from fantasy_pipeline.draft_mock import run_mock


def test_mock_fills_every_roster_quickly() -> None:
    players = [
        {
            "id": str(i),
            "usd": max(1.0, 28 - i * 0.12),
            "z": [0.1 * ((i + k) % 7 - 3) for k in range(9)],
        }
        for i in range(260)
    ]
    res = run_mock(players, [f"Team {i + 1}" for i in range(16)], 200, 14)
    assert res.picks == 224
    assert res.rosters_full
    assert res.max_ms < 2000
