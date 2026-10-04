import random

import pytest

from fantasy_models import draft_live as dl

TEAMS = [f"T{i}" for i in range(1, 17)]
CATS = 9
REB = 4


def players(n: int = 260, seed: int = 0) -> list[dict]:  # type: ignore[type-arg]
    rng = random.Random(seed)
    out = []
    for i in range(n):
        z = [round(rng.gauss(0.3 - i / 300, 0.8), 2) for _ in range(CATS)]
        out.append(
            {"id": str(i), "usd": max(1.0, round(28 - i * 0.12, 1)), "z": z}
        )  # top 224 ~ $3,200
    return out


def test_max_bid_rule() -> None:
    st = dl.team_state([{"pid": "0", "team": "T1", "price": 55}], TEAMS, 200, 14)
    assert st["T1"]["left"] == 145
    assert st["T1"]["open"] == 13
    assert st["T1"]["max_bid"] == 145 - 12
    assert st["T2"]["max_bid"] == 200 - 13


def test_inflation_rises_when_early_picks_are_cheap() -> None:
    ps = players()
    cheap = [{"pid": str(i), "team": TEAMS[i % 16], "price": 1} for i in range(5)]
    dear = [{"pid": str(i), "team": TEAMS[i % 16], "price": 90} for i in range(5)]
    a = dl.advise(ps, cheap, TEAMS, "T1", 200, 14)
    b = dl.advise(ps, dear, TEAMS, "T1", 200, 14)
    assert a["inflation"] > 1 > b["inflation"]


def test_recs_change_with_roster_build() -> None:
    """AC2: adding a strong-REB player lowers the REB weight (and raises weak categories)."""
    ps = players()
    ps[0]["z"] = [0.0] * CATS
    ps[0]["z"][REB] = 3.0
    before = dl.advise(ps, [], TEAMS, "T1", 200, 14)
    after = dl.advise(ps, [{"pid": "0", "team": "T1", "price": 40}], TEAMS, "T1", 200, 14)
    assert after["weights"][REB] < before["weights"][REB]
    reb_heavy = max((p for p in ps[1:]), key=lambda p: p["z"][REB])["id"]
    assert after["players"][reb_heavy]["fit"] <= before["players"][reb_heavy]["fit"]


def test_fit_is_capped_and_punts_zero_weight() -> None:
    w = dl.category_weights({"a": {"z": [5.0] * CATS}}, ["a"], {8})
    assert w[8] == 0.0
    assert all(dl.WEIGHT_BOUNDS[0] <= x <= dl.WEIGHT_BOUNDS[1] for x in w[:8])
    assert dl.fit_multiplier([1.0] * CATS, [1.5] * CATS, set()) == pytest.approx(1 + dl.FIT_CAP)


def test_ceiling_never_exceeds_max_bid() -> None:
    ps = players()
    picks = [{"pid": str(i), "team": "T1", "price": 14} for i in range(13)]
    adv = dl.advise(ps, picks, TEAMS, "T1", 200, 14)
    assert adv["my_max_bid"] == 200 - 13 * 14
    assert all(r["ceiling"] <= adv["my_max_bid"] for r in adv["players"].values())


def test_manual_entry_flow() -> None:
    """AC3: picks are plain entries (player, team, price); a correction is just a replaced entry."""
    ps = players()
    picks = [{"pid": "0", "team": "T3", "price": 61}]
    adv = dl.advise(ps, picks, TEAMS, "T1", 200, 14)
    assert "0" not in adv["players"]
    picks[0] = {"pid": "0", "team": "T4", "price": 58}
    adv2 = dl.advise(ps, picks, TEAMS, "T1", 200, 14)
    assert adv2["teams"]["T4"]["spent"] == 58
    assert adv2["teams"]["T3"]["spent"] == 0


def test_full_mock_draft_replay() -> None:
    """AC4 (unit level): a full 16 x 14 auction replays and ends with every slot full."""
    ps = players()
    rng = random.Random(1)
    picks: list[dict] = []  # type: ignore[type-arg]
    for _ in range(16 * 14):
        adv = dl.advise(ps, picks, TEAMS, "T1", 200, 14)
        pid = adv["targets"][0]
        bidders = [t for t in TEAMS if adv["teams"][t]["open"] > 0]
        team = rng.choice(bidders)
        price = max(1, min(int(adv["teams"][team]["max_bid"]), int(adv["players"][pid]["adj"])))
        picks.append({"pid": pid, "team": team, "price": price})
    final = dl.team_state(picks, TEAMS, 200, 14)
    assert all(s["open"] == 0 and s["left"] >= 0 for s in final.values())


def test_full_rosters_leftover_cash_does_not_inflate() -> None:
    """Review finding: a finished team's unspendable cash must not raise inflation."""
    ps = players()
    cheap_full = [
        {"pid": str(i), "team": "T2", "price": 1} for i in range(14)
    ]  # T2 full with $186 left
    other = [
        {"pid": str(14 + i), "team": "T3", "price": 14} for i in range(14)
    ]  # T3 full, spent it all
    a = dl.advise(ps, cheap_full, TEAMS, "T1", 200, 14)
    b = dl.advise(ps, other, TEAMS, "T1", 200, 14)
    # the same number of open slots and remaining players; T2's leftover cash is dead money
    assert a["teams"]["T2"]["open"] == 0
    assert a["teams"]["T2"]["left"] == 186
    assert a["inflation"] == pytest.approx(b["inflation"], rel=0.02)
