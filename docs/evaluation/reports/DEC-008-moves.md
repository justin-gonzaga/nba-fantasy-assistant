# DEC-008: which add/drop rule gains more categories?

Generated 2026-09-28 01:53 UTC by `python -m fantasy_pipeline moves-replay`.
Pre-registered in the task file (commit 6f41bc4) before any result.

**Setup**: 16 rosters of 14 drafted by the leak-free 2025-26 values; 11 holdout weeks (from 19 Jan 2026) x 16 teams = 176 team-weeks. Each team-week, each
method proposes at most one Monday move from what was known then; the move is scored on
actual stats: categories won vs that week's opponent, minus without the move, plus 0.5 x
next week. Week-block bootstrap CIs [R-55]. A moves only if its own gain is > 0.

## Verdict

**B SHIPS**: method B becomes the brief's pickup rule (wired in DEC-010). B minus A: **+0.2202** categories per team-week (95 % CI +0.0554 to +0.3608; rule: CI entirely above 0).

## Realised gain per team-week vs making no move

| method | mean realised gain (categories) | 95 % CI | team-weeks with a move |
|---|---|---|---|
| A: live pickups rule (normal approx., this week) | +0.3452 | +0.2344 to +0.4418 | 98% |
| B: simulation, this week + 0.5 x next (decides) | +0.5653 | +0.3693 to +0.7727 | 100% |
| B at 0.3 (sensitivity) | +0.5724 | +0.4162 to +0.7202 | 100% |
| B at 0.7 (sensitivity) | +0.5795 | +0.3764 to +0.7770 | 100% |

A gain of +0.10 means one extra category every ten weeks for that team.

## Limitations (reviewer findings)

- Common random numbers are partial: numpy's negative-binomial and beta draws use a
  variable number of stream values, so swapping one player can shift the later draws. The
  estimate stays unbiased but noise cancels less than [R-61] promises.
- 1,000 draws per scored pair; Monte Carlo SE not measured here (U14; DEC-003 found
  SE 0.027 at 2,000). The ship margin (CI low +0.055) is measured on realised outcomes,
  so simulation noise can only make B's choices worse, not inflate its score.
- Players with no games yet this season get 0 expected games (e.g. a debuting rookie).
- Yahoo's weekly add limit and waiver order are not modelled; B moved every team-week.

## Disclosure: two bugs found before this run

1. The first run gave B exactly +0.0000 while moving in 15 % of team-weeks. Cause: B
   ranked free agents by draft value x games, but free agents' values are below
   replacement (negative), so players with **no games** ranked first and B only ever
   considered idle players. That was an implementation bug, not the pre-registered
   method ('the top free agents by projected weekly value'). Fix: the screen ranks free
   agents by the normal-approximation gain over the same horizon (regression test in
   `test_moves.py`).
2. Method A's gain differed between runs (+0.38, +0.34, +0.32) with no code change.
   Cause: several players share exactly the same value (e.g. rookies from the same draft
   slot) and the snake draft broke ties by row order, which the data load doesn't fix,
   so the league's rosters changed from run to run. Fix: ties go to the lowest player id
   (`test_draft_replay.py`). The spread shows that the gains depend on the league drawn;
   the CIs above cover week-to-week noise only, not other drafts.

Methods, data, scoring and the ship rule are otherwise as pre-registered. The bug-fix
run with the old tie-breaking gave B - A = +0.2557 (CI +0.1051 to +0.4034).
