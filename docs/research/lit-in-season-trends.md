# In-season trends, late-season rest/tanking, trade-deadline role change, fantasy-playoff scheduling (RSCH-008)

Researched 2026-10-03 by the `researcher` subagent for RSCH-008 (second-half splits, late-season
rest/tanking, trade-deadline role change, fantasy-playoff schedule weighting). New IDs continue from the
highest existing (`R-105`, in `lit-minutes-injury.md`): **R-106…R-109**. Every entry below was checked
against a primary bibliographic source (Crossref API and/or publisher/RePEc/IDEAS landing page); where the
publisher page itself returned HTTP 403, the citation is confirmed via Crossref metadata plus independent
search-engine snippets quoting the abstract, consistent with the access-rule pattern already used in
`ml-literature-review.md` and `lit-breakouts.md`. No entry here was read as full text; **all are Abstract-level
or Crossref-metadata-level** and cannot be the sole basis for a gated decision per the access rule in
`ml-literature-review.md`.

## Q1 — Is a "second-half player" a repeatable trait, or regression to the mean / split-half noise?

| ID | Status | Citation | URL | Accessed | What it says | Applies to RSCH-008 |
|---|---|---|---|---|---|---|
| R-106 | Verified (Abstract/Crossref; cross-sport — baseball, not basketball) | Schall, T., & Smith, G. (2000). Do baseball players regress toward the mean? *The American Statistician*, 54(4), 231–235. https://doi.org/10.1080/00031305.2000.10474553 | https://doi.org/10.1080/00031305.2000.10474553 (publisher page returned HTTP 403; author's self-archived summary at https://economics-files.pomona.edu/garysmith/papers/BBregress/baseball.html returned HTTP 404 this pass; citation and abstract content confirmed via Crossref API and independent search snippets) | 2026-10-03 | Shows batting average and ERA are *imperfect* measures of ability: extreme first-half performers regress toward the mean in the second half because some of the extremity is measurement noise, not skill. Explicitly cites the folk claim that "90% of players who hit >20 HR in the first half hit fewer than 20 in the second half" as a textbook regression-to-the-mean illustration, not evidence of a real split-skill. Shows shrinkage using **prior-season correlation coefficients** improves second-half prediction over using raw first-half rates. | Directly supports the pre-registered **decision rule for Q1**: naive first-half-vs-second-half deltas are expected to look large even under pure noise; the correct test is season-to-season correlation of the *shrinkage-adjusted* delta (as RSCH-008 already proposes), not the raw split. Cross-sport (baseball) — same caveat pattern as R-16/R-71/R-88: the *mechanism* (regression to the mean under measurement error) transfers, the *magnitude* does not. |
| R-107 | Verified (Abstract/Crossref; cross-sport — baseball, not basketball) | Albert, J. (1994). Exploring baseball hitting data: what about those breakdown statistics? *Journal of the American Statistical Association*, 89(427), 1066–1074. https://doi.org/10.1080/01621459.1994.10476844 | https://doi.org/10.1080/01621459.1994.10476844 (publisher page returned HTTP 403; citation, scope and conclusion confirmed via Crossref API and independent search snippets) | 2026-10-03 | Uses Bayesian hierarchical (random-effects) models on 1992 MLB regulars to test **eight** situational splits for being "real" (i.e., explaining a significant share of between-player variance) rather than sampling noise — including **first half vs. second half of season** alongside home/away, platoon, count situations, etc. Finds most situational splits (including first/second half) show **little to no evidence of being a real, stable individual trait**; the hierarchical/shrinkage estimate pulls almost all of the apparent split back toward zero, with only one or two of the eight situations (e.g., platoon splits) showing a detectable real effect. | The closest methodological precedent for Q1's "repeatable trait vs. noise" test, and it is specifically about half-season splits (not just regression to the mean generally): a hierarchical/random-effects model applied to the *same* type of split RSCH-008 investigates, with the finding that half-season splits are among the weakest, least-persistent of the eight situational effects tested. Supports treating a null/near-zero result on Q1 as the *expected* finding, not a surprising one. Cross-sport (baseball) caveat applies equally. |

**Gap:** no NBA-specific peer-reviewed study of first-half/second-half split persistence was found this
pass (searched directly; only practitioner fantasy-journalism pieces and team-level All-Star-break
win-percentage anecdotes turned up — e.g., "teams with several All-Stars see a 5–10% dip in win% after the
break," unsourced/not peer-reviewed, **not added as an R-id**). RSCH-008's own analysis on 2015-16…2025-26
warehouse data will be the first NBA-specific, project-level test; R-106/R-107 justify its design (test the
shrinkage-adjusted delta's persistence, expect a null result by default) rather than its NBA magnitude.

## Q2 — Late-season rest, tanking, and team context (playoff-locked / elimination) effects on playing time

| ID | Status | Citation | URL | Accessed | What it says | Applies to RSCH-008 |
|---|---|---|---|---|---|---|
| R-108 | Verified (Abstract/Crossref; peer-reviewed, NBA-specific) | Gong, H., Watanabe, N. M., Soebbing, B. P., Brown, M. T., & Nagel, M. S. (2022). Exploring tanking strategies in the NBA: an empirical analysis of resting healthy players. *Sport Management Review*, 25(3), 546–566. https://doi.org/10.1080/14413523.2021.1970972 | https://doi.org/10.1080/14413523.2021.1970972 (publisher page returned HTTP 403; citation and abstract confirmed via IDEAS/RePEc landing page https://ideas.repec.org/a/taf/rsmrxx/v25y2022i3p546-566.html and independent search snippets) | 2026-10-03 | NBA regular-season games, 2006-07 through 2017-18. Poisson count-regression model of the **number of healthy players rested per game**. Finds **eliminated teams rest significantly more players than teams still in contention**, and the number rested **increases further as more teams are tied in the draft-lottery standings** (tournament-theory incentive to tank). This is a team-decision-level (how many players rested), not an individual-minutes-level, result. | Directly supports the **team-context side of Q2's grouping variable**: "eliminated / bottom-6" should show a measurably higher rate of healthy scratches than "mid-race" or "playoff-locked top seed" teams, consistent with RSCH-008's (a) team-context grouping. It does not itself give an individual player's minutes/mpg change — RSCH-008's own per-player analysis is the first to quantify that for *your* game logs and *your* 1 Mar cutoff. Pair with R-101 (Herzog et al. 2026, already in `lit-minutes-injury.md`): rest did not reduce subsequent injury risk, so "resting because playoff seed is locked" should not be modelled as protective of future availability either. |

Existing, already-catalogued entries also apply directly to Q2 and are **not duplicated here**:
- **R-101** (Herzog, Brink, Gondalia, DiFiori & Mack, 2026, *Sports Medicine*): games missed for rest/load
  management did **not** reduce later injury hazard (all CIs cross 1; 1,233 player-seasons, 2014-15…2022-23).
  Relevant to interpreting any "rested players come back healthier/more available" hypothesis in Q2 — don't
  model it.
- **R-103** (Nakamura-Sakai, Forastiere & Macdonald, 2024, arXiv preprint, not peer-reviewed): rest effects on
  performance/availability vary by **age**; age is a relevant covariate alongside RSCH-008's "age ≤ 23 on
  bottom-6 teams" role grouping.

**Gap:** no peer-reviewed source was found that directly measures the **individual** minutes-per-game or
games-missed effect size, split by team playoff context, at the player level — RSCH-008's own Q2 analysis is
the first for this exact design. R-108's team-decision result is the closest supporting evidence that the
(a) team-context grouping variable is a real, previously-measured phenomenon, not a hypothesis invented for
this task.

## Trade-deadline effects on player role/minutes (context for the "player traded mid-season" edge case; not a pre-registered Q in RSCH-008)

| ID | Status | Citation | URL | Accessed | What it says | Applies to RSCH-008 |
|---|---|---|---|---|---|---|
| R-109 | Verified (Abstract/Crossref; peer-reviewed, NBA-specific, but does **not** measure individual minutes/role) | Nong, X., & Huang, W. (2026). Bargaining with a deadline: evidence from the NBA. *Journal of Sports Economics*, 27(3), 283–308. https://doi.org/10.1177/15270025251409666 | https://doi.org/10.1177/15270025251409666 (publisher page returned HTTP 403; citation and abstract confirmed via Crossref API) | 2026-10-03 | NBA trades, 2000-2024. Studies deadline-bargaining dynamics (newer GMs more likely to complete trades right before the deadline, as a reputation-building signal) and finds that although 58% of deadline trades involved "major assets," these trades showed **no significant effect on subsequent team win%**. It is a trade-negotiation-timing and team-performance study, **not** an individual player minutes/usage/role study. | Weak fit for "trade-deadline effects on player role/minutes" as posed: it answers a different question (negotiation timing; team-level win%, not individual role). **Flagged as a gap, not adopted as evidence for an individual-level effect.** |

Already-catalogued, more directly relevant entry (**not duplicated here**): **R-85** (Campbell, Saxton &
Banerjee, 2014, *Journal of Management*, "Resetting the Shot Clock: The Effect of Comobility on Human
Capital," `lit-breakouts.md`) is the project's existing peer-reviewed evidence that NBA trades carry a
measurable, directional **individual performance shock** for the traded player, moderated by whether they
move alone or as part of a package — this is the right citation for "player traded mid-season," not R-109.

**Gap:** no peer-reviewed source measuring an individual NBA player's **minutes-per-game** change
specifically around the trade deadline (as distinct from the general performance-shock finding of R-85) was
found this pass. Trade-press examples exist (e.g., a traded center's usage rate falling from 29.9% to 28.2%
after a mid-season trade) but are anecdotal, single-case, and not peer-reviewed — **not added as an R-id**.
RSCH-008's edge-case rule ("halves are by date, team context by the team on 1 Mar") should be treated as a
reasonable project-specific convention, not one backed by a dedicated trade-deadline minutes study.

## Q3 — Fantasy-sports playoff scheduling / schedule-strength effects

**No peer-reviewed or otherwise credible quantitative academic source was found** for fantasy-sports
playoff-week schedule weighting or schedule-strength effects, in basketball or any other fantasy sport.
Search covered Google Scholar-style queries, MIT Sloan Sports Analytics Conference proceedings listings, and
the existing Rosenof fantasy-valuation series (R-01, R-02, R-03 in `ml-literature-review.md` §1), none of
which treats playoff-week game-count weighting. What exists is exclusively **practitioner fantasy
journalism** (Yahoo Sports, RotoWire, Bleacher Nation, FantasyTeamAdvice, a hobbyist GitHub issue thread
discussing "playoff-weeks schedule weighting in trade values") — useful as a description of the practice,
not as a measured effect size, and **not added as R-ids** per the "no fabrication" rule.

- **Decision for RSCH-008**: Q3's own analysis (recomputing draft values with playoff weeks weighted by
  w ∈ {1, 2, 3} and measuring top-150 rank movement, as pre-registered) is **the only available evidence** on
  this question for this league's format; there is no external study to cite for either the existence or the
  magnitude of a schedule-weighting effect. Treat the pre-registered analysis's own result as the primary
  (and only) source, with the usual CIs/robustness checks RSCH-008 already requires elsewhere (bootstrap,
  R-54).
- Confirm with `researcher` again only if time passes and new SSAC/JQAS proceedings are published; this is a
  standing gap, not a one-time miss.

## Search log (2026-10-03)

| Query | Database / site | Outcome |
|---|---|---|
| split-half reliability regression to the mean sports statistics first half second half season repeatable | Google | led to R-106, R-107, Albert streakiness background |
| Schall Smith "Do Baseball Players Regress Toward the Mean" | Google + Crossref API | R-106 confirmed |
| Albert 1994 "Exploring baseball hitting data" breakdown statistics JASA | Google + Crossref API | R-107 confirmed |
| NBA load management playoff seeding locked rest minutes tanking elimination peer-reviewed study | Google | R-108, reconfirmed R-101/R-102/R-103 already catalogued |
| NBA tanking incentive playing time rookies JQAS / Journal of Sports Economics | Google | R-108 located and confirmed via IDEAS/RePEc |
| NBA trade deadline effect player minutes usage role change study | Google | R-109 located (weak fit); R-85 (already catalogued) identified as the better existing fit |
| "trade deadline" NBA player performance minutes empirical study economics | Google + Crossref API | R-109 confirmed; a Skidmore undergraduate thesis found but excluded (not peer-reviewed) |
| fantasy sports playoff schedule strength effect research MIT Sloan Sports Analytics Conference | Google | 0 academic hits; practitioner-only, logged as a gap |
| fantasy basketball playoff weeks weighted schedule strategy academic paper roster value | Google | 0 academic hits; practitioner-only (Yahoo, RotoWire, GitHub issue), logged as a gap |
| "games played" fantasy football playoff schedule strength study journal sports analytics | Google | 0 academic hits (cross-sport check); practitioner-only, confirms the gap is not basketball-specific |
| NBA players "All-Star break" performance improvement decline statistical study second half season | Google | 0 peer-reviewed hits; unsourced team-level win% anecdote found, not added as an R-id |
| NBA player minutes per game before after trade deadline change study "usage rate" empirical | Google | surfaced R-84 (already catalogued, production curves) and single-case trade press examples only |
| "resting starters" NBA win probability late season "locked" seed effect quantitative | Google | 0 additional peer-reviewed hits beyond R-108/R-101 |

## Summary for RSCH-008

| Question | Best available literature | Confidence | Implication |
|---|---|---|---|
| Q1: second-half split persistence | R-106, R-107 (both cross-sport, baseball) | Medium (mechanism), Low (NBA magnitude) | Expect the pre-registered null/noise result by default; the literature's prior is that half-season splits are among the *least* persistent situational effects tested. No NBA-specific split-half study exists; RSCH-008's own run is the first. |
| Q2: late-season rest/tanking by team context | R-108 (NBA-specific, team-decision level), R-101/R-103 (already catalogued) | Medium (team-level resting pattern is measured); Low (no individual mpg/games-missed-by-context study exists) | R-108 corroborates that the (a) team-context grouping (eliminated/bottom-6 vs. playoff-locked vs. mid-race) is a real, previously-measured managerial pattern — supports running Q2 as designed, but the actual effect sizes for your decision rule (≥2 games / ≥3 mpg) must come from RSCH-008's own data; no external effect size to borrow. |
| Q3: fantasy-playoff schedule weighting | None (practitioner only) | N/A — explicit literature gap | RSCH-008's own w ∈ {1,2,3} replay is the sole evidence; proceed exactly as pre-registered, with no external benchmark to sanity-check against. |
| (context) trade-deadline role/minutes | R-85 (already catalogued, individual performance shock) is the best fit; R-109 (new) is a weak fit (team win%, not minutes) | Medium (R-85), Low (no minutes-specific study) | Use R-85, not R-109, if the "player traded mid-season" edge case needs a literature citation; no study measures the minutes change itself. |
