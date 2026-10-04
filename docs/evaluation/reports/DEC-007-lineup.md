# DEC-007: lineup optimiser vs greedy (replay of 2025-26)

Generated 2026-09-27 23:15 UTC by `python -m fantasy_pipeline lineup-replay`.
Pre-registered in the task file (commits 0aad42e, amended before any result in 738a953).

**Setup**: every 2025-26 regular-season game day × 16 sample rosters (a snake draft of the
top 224 by this season's draft values), slots G×3, F×3, C×1, Util×3. A player
plays that day if he has a game-log row. Both methods maximise the number of active players, then
their total value.

## Verdict

**SHIPS**: the brief's lineup comes from the optimiser. Across **2,624 lineups**:
- the optimiser started **more players** than greedy in **36** lineups
  (+1.00 players on average when it did), and the same number with **more
  value** in **6**;
- it was worse in **0** and illegal in **0** (rule: both 0);
- the slowest solve took **10 ms** (rule: < 1 s).

## Sample-roster standings (a thought experiment)

**Superseded by the leak-free draft replay: [DRAFT-009](DRAFT-009-draft-replay.md).**

What each sample roster's optimised lineups actually produced over 2025-26, ranked like a
rotisserie table (16 points for the best in a category). These rosters are a snake draft by the
**2026-27** draft values replayed on last season's games, so they show how draft value turned into
production, not a real league.

| rank | roster (first 3 picks) | starts | PTS | REB | AST | STL | BLK | 3PM | TO | FG% | FT% | roto pts |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | #1: Victor Wembanyama, Dyson Daniels, Kon Knueppel | 913 | 12,370 | 5,030 | 2,975 | 863 | 646 | 1,264 | 1,521 | 0.493 | 0.776 | 89.0 |
| 2 | #6: Scottie Barnes, Trey Murphy III, Jay Huff | 998 | 12,184 | 4,951 | 3,384 | 1,067 | 620 | 1,392 | 1,524 | 0.485 | 0.780 | 89.0 |
| 3 | #13: Jalen Johnson, Jalen Duren, Mikal Bridges | 920 | 15,717 | 4,931 | 3,170 | 825 | 448 | 1,507 | 1,664 | 0.486 | 0.790 | 89.0 |
| 4 | #2: Nikola Jokić, Matas Buzelis, Devin Booker | 849 | 13,359 | 4,670 | 2,950 | 819 | 494 | 1,406 | 1,605 | 0.487 | 0.822 | 85.0 |
| 5 | #5: Tyrese Maxey, Bam Adebayo, Nickeil Alexander-Walker | 825 | 13,634 | 4,434 | 2,768 | 804 | 444 | 1,588 | 1,351 | 0.480 | 0.824 | 84.0 |
| 6 | #15: Anthony Edwards, LaMelo Ball, Jabari Smith Jr. | 984 | 13,627 | 4,704 | 3,559 | 1,078 | 534 | 1,486 | 1,696 | 0.465 | 0.763 | 84.0 |
| 7 | #16: Derrick White, Desmond Bane, Immanuel Quickley | 895 | 13,043 | 3,691 | 2,623 | 845 | 525 | 1,818 | 1,294 | 0.448 | 0.841 | 82.0 |
| 8 | #3: Shai Gilgeous-Alexander, Kel'el Ware, Payton Pritchard | 891 | 12,905 | 5,330 | 2,308 | 774 | 647 | 1,212 | 1,256 | 0.510 | 0.762 | 81.0 |
| 9 | #12: Donovan Clingan, Kawhi Leonard, Donte DiVincenzo | 882 | 12,573 | 4,607 | 2,423 | 848 | 450 | 1,559 | 1,251 | 0.471 | 0.811 | 80.0 |
| 10 | #7: Donovan Mitchell, Jalen Brunson, Ryan Rollins | 879 | 12,839 | 4,132 | 2,787 | 887 | 445 | 1,558 | 1,431 | 0.473 | 0.806 | 77.0 |
| 11 | #14: Kevin Durant, Amen Thompson, Myles Turner | 895 | 11,855 | 5,120 | 2,228 | 764 | 661 | 1,007 | 1,219 | 0.526 | 0.783 | 77.0 |
| 12 | #4: Luka Dončić, Alperen Sengun, Reed Sheppard | 816 | 13,060 | 4,441 | 3,099 | 813 | 522 | 1,422 | 1,588 | 0.483 | 0.770 | 71.0 |
| 13 | #8: Jamal Murray, Onyeka Okongwu, De'Aaron Fox | 820 | 12,266 | 4,016 | 2,952 | 751 | 438 | 1,501 | 1,397 | 0.473 | 0.814 | 62.0 |
| 14 | #9: Karl-Anthony Towns, Cooper Flagg, Deni Avdija | 846 | 12,003 | 4,511 | 2,776 | 857 | 477 | 1,141 | 1,507 | 0.480 | 0.787 | 61.0 |
| 15 | #11: Cade Cunningham, James Harden, Naz Reid | 787 | 12,569 | 3,718 | 3,444 | 835 | 329 | 1,276 | 1,554 | 0.477 | 0.805 | 61.0 |
| 16 | #10: Chet Holmgren, Evan Mobley, Josh Giddey | 837 | 11,535 | 4,654 | 2,734 | 692 | 547 | 1,213 | 1,434 | 0.483 | 0.753 | 52.0 |

**Caveat**: the 2026-27 draft values were built partly from these same 2025-26 seasons, so this
table is hindsight: it shows how the values map to last season's production, not evidence that a
draft strategy works. Three rosters tie on 89 points (#1, #6, #13); the table breaks ties by roster
order only.
